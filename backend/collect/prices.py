"""국토교통부 아파트 실거래가(매매·전월세) → 법정동별 시세 중앙값 → regions_real.json

준비물 (data.go.kr에서 활용신청, 보통 즉시~1시간 내 승인):
  - 국토교통부_아파트 매매 실거래가 자료   (RTMSDataSvcAptTrade)
  - 국토교통부_아파트 전월세 실거래가 자료 (RTMSDataSvcAptRent)
  → 마이페이지의 '일반 인증키(Decoding)'를 MOLIT_SERVICE_KEY에 넣어요.
  - 좌표: KAKAO_REST_KEY가 있으면 카카오, 없으면 오픈스트리트맵(키 불필요)
  - 키 없이 하려면 collect/prices_csv.py (공개시스템 CSV 다운로드) 를 쓰세요

실행:
  cd backend
  python -m collect.prices --months 6               # 기본: 전용 49~85㎡, 최근 6개월
  python -m collect.prices --months 3 --only 41131 11650   # 일부 시군구만
  python -m collect.prices --supabase               # Supabase regions 테이블에도 반영
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date
from pathlib import Path

import httpx

from .sigungu import SIGUNGU
from .store import Geocoder, make_region, publish

TRADE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
RENT_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"

# 신·구 응답 필드명을 모두 받아요 (2024년 개편 전 한글 태그 대응)
F = {
    "umd": ("umdNm", "법정동"),
    "area": ("excluUseAr", "전용면적"),
    "price": ("dealAmount", "거래금액"),
    "cancel": ("cdealType", "해제여부"),
    "deposit": ("deposit", "보증금액"),
    "rent": ("monthlyRent", "월세금액"),
}


def _get(item: ET.Element, key: str) -> str:
    for tag in F[key]:
        el = item.find(tag)
        if el is not None and el.text is not None:
            return el.text.strip()
    return ""


def _num(s: str) -> float:
    s = s.replace(",", "").strip()
    return float(s) if s else 0.0


def parse_items(xml_text: str) -> tuple[list[ET.Element], int]:
    root = ET.fromstring(xml_text)
    code = root.findtext(".//resultCode") or root.findtext(".//returnReasonCode") or ""
    if code and code not in ("00", "000"):
        msg = root.findtext(".//resultMsg") or root.findtext(".//returnAuthMsg") or ""
        raise RuntimeError(f"API 오류 {code}: {msg}")
    total = int(root.findtext(".//totalCount") or 0)
    return root.findall(".//item"), total


def fetch_month(client: httpx.Client, url: str, key: str, lawd: str, ym: str) -> list[ET.Element]:
    items, page = [], 1
    while True:
        r = client.get(url, params={"serviceKey": key, "LAWD_CD": lawd, "DEAL_YMD": ym, "pageNo": page, "numOfRows": 1000})
        r.raise_for_status()
        got, total = parse_items(r.text)
        items += got
        if len(items) >= total or not got:
            return items
        page += 1


def recent_months(n: int, today: date | None = None) -> list[str]:
    d = today or date.today()
    y, m = d.year, d.month - 1  # 이번 달은 신고가 덜 들어와서 지난달부터
    out = []
    for _ in range(n):
        if m == 0:
            y, m = y - 1, 12
        out.append(f"{y}{m:02d}")
        m -= 1
    return out


def to_records(trades: list[ET.Element], rents: list[ET.Element]) -> tuple[list[dict], list[dict]]:
    tr = [{"umd": _get(it, "umd"), "area": _num(_get(it, "area")), "price": _num(_get(it, "price")),
           "cancel": _get(it, "cancel") == "O"} for it in trades]
    rr = [{"umd": _get(it, "umd"), "area": _num(_get(it, "area")), "deposit": _num(_get(it, "deposit")),
           "rent": _num(_get(it, "rent"))} for it in rents]
    return tr, rr


def aggregate_records(trades: list[dict], rents: list[dict], area=(49, 85), min_n: int = 3) -> dict[str, dict]:
    """법정동별 중앙값. 표본이 min_n 미만인 항목은 None. (API·CSV 공통)"""
    buy, jeonse, wd, wr = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    for t in trades:
        if area[0] <= t["area"] <= area[1] and not t["cancel"] and t["price"] > 0:
            buy[t["umd"]].append(t["price"])
    for r in rents:
        if not (area[0] <= r["area"] <= area[1]):
            continue
        if r["rent"] == 0:
            jeonse[r["umd"]].append(r["deposit"])
        else:
            wd[r["umd"]].append(r["deposit"])
            wr[r["umd"]].append(r["rent"])

    def med(v):
        return int(round(statistics.median(v))) if len(v) >= min_n else None

    out = {}
    for umd in set(buy) | set(jeonse) | set(wd):
        if not umd:
            continue
        out[umd] = {
            "buy": med(buy[umd]), "jeonse": med(jeonse[umd]),
            "monthly_deposit": med(wd[umd]), "monthly_rent": med(wr[umd]),
            "n": {"buy": len(buy[umd]), "jeonse": len(jeonse[umd]), "monthly": len(wr[umd])},
        }
    return out


def aggregate(trades: list[ET.Element], rents: list[ET.Element], area=(49, 85), min_n: int = 3) -> dict[str, dict]:
    return aggregate_records(*to_records(trades, rents), area=area, min_n=min_n)


def fill_missing(dongs: dict[str, dict]) -> dict[str, dict]:
    """동 단위 표본이 부족한 값은 같은 시군구 중앙값으로 채우고 표시해요."""
    keys = ("buy", "jeonse", "monthly_deposit", "monthly_rent")
    sgg = {k: [d[k] for d in dongs.values() if d[k]] for k in keys}
    sgg_med = {k: int(statistics.median(v)) if v else None for k, v in sgg.items()}
    for d in dongs.values():
        d["filled"] = [k for k in keys if d[k] is None]
        for k in d["filled"]:
            d[k] = sgg_med[k]
    return {u: d for u, d in dongs.items() if all(d[k] for k in keys)}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=6)
    ap.add_argument("--only", nargs="*", help="LAWD_CD 일부만")
    ap.add_argument("--min-area", type=float, default=49)
    ap.add_argument("--max-area", type=float, default=85)
    ap.add_argument("--supabase", action="store_true")
    args = ap.parse_args(argv)
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parents[1] / ".env")
    except ImportError:
        pass

    key = os.getenv("MOLIT_SERVICE_KEY")
    if not key:
        sys.exit("MOLIT_SERVICE_KEY(data.go.kr 일반 인증키 Decoding)를 설정하세요")

    targets = [s for s in SIGUNGU if not args.only or s[0] in args.only]
    months = recent_months(args.months)
    geo = Geocoder()
    regions = []
    with httpx.Client(timeout=30) as c:
        for lawd, sido, sgg in targets:
            trades, rents = [], []
            for ym in months:
                trades += fetch_month(c, TRADE_URL, key, lawd, ym)
                rents += fetch_month(c, RENT_URL, key, lawd, ym)
                time.sleep(0.1)
            dongs = fill_missing(aggregate(trades, rents, (args.min_area, args.max_area)))
            for umd, d in dongs.items():
                r = make_region(lawd, sido, sgg, umd, d, geo)
                if r:
                    regions.append(r)
            print(f"{sido} {sgg}: 거래 {len(trades)}건 · 전월세 {len(rents)}건 → 동 {len(dongs)}곳", flush=True)

    geo.save()
    publish(regions, {
        "source": "국토교통부 아파트 매매·전월세 실거래가 API (data.go.kr)",
        "period": f"{months[-1]}~{months[0]}", "area_m2": [args.min_area, args.max_area],
    }, supabase=args.supabase)

if __name__ == "__main__":
    main()
