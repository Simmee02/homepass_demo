"""국토부 실거래가 공개시스템에서 내려받은 CSV로 시세 만들기 (API 키 불필요)

1) https://rt.molit.go.kr → 조건별 자료제공
   - 실거래 구분: 아파트(매매) / 아파트(전월세), 기간: 최근 6개월, 지역: 서울·경기 (시군구 단위 여러 번 받아도 돼요)
   - 파일 형식: CSV
2) 받은 파일을 backend/raw/ 에 넣고:
     cd backend
     python -m collect.prices_csv raw/*.csv            # 매매·전월세 파일을 섞어 넣어도 알아서 구분해요
     python -m collect.prices_csv raw/*.csv --supabase # Supabase regions 테이블에도 적재
3) 결과: app/data/regions_real.json + supabase/regions.csv
   (Supabase 대시보드 Table Editor → regions → Import data from CSV 로 올려도 돼요)
"""
from __future__ import annotations

import argparse
import csv
import io
import re
from collections import defaultdict
from pathlib import Path

from .prices import aggregate_records, fill_missing
from .store import Geocoder, make_region, publish

SIDO_SHORT = {
    "서울특별시": "서울", "경기도": "경기", "인천광역시": "인천", "부산광역시": "부산", "대구광역시": "대구",
    "광주광역시": "광주", "대전광역시": "대전", "울산광역시": "울산", "세종특별자치시": "세종",
    "강원특별자치도": "강원", "강원도": "강원", "충청북도": "충북", "충청남도": "충남", "전북특별자치도": "전북",
    "전라북도": "전북", "전라남도": "전남", "경상북도": "경북", "경상남도": "경남", "제주특별자치도": "제주",
}


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"인코딩을 알 수 없어요: {path}")


def _num(s: str) -> float:
    s = (s or "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def _col(header: list[str], *keys: str) -> int | None:
    """헤더가 key로 시작하는 열을 먼저, 없으면 key를 포함하는 열을 찾아요. ('전월세구분'이 '월세'로 잡히지 않게)"""
    for i, h in enumerate(header):
        if h.startswith(keys[0]) and all(k in h for k in keys):
            return i
    for i, h in enumerate(header):
        if all(k in h for k in keys) and "종전" not in h:
            return i
    return None


def parse_file(path: Path) -> tuple[str, list[dict]]:
    """→ ('trade'|'rent', 레코드 목록). 파일 앞쪽 안내문 줄은 건너뛰어요."""
    rows = list(csv.reader(io.StringIO(_read_text(path))))
    hi = next((i for i, r in enumerate(rows) if any("시군구" in c for c in r) and any(("거래금액" in c) or ("보증금" in c) for c in r)), None)
    if hi is None:
        raise ValueError(f"실거래가 CSV 형식이 아니에요: {path.name}")
    header = [h.strip() for h in rows[hi]]
    c_sgg, c_area = _col(header, "시군구"), _col(header, "전용면적")
    kind = "trade" if _col(header, "거래금액") is not None else "rent"
    c_price, c_cancel = _col(header, "거래금액"), _col(header, "해제")
    c_dep = _col(header, "보증금")
    c_rent = _col(header, "월세금")
    if c_rent is None:
        c_rent = next((i for i, h in enumerate(header) if h.startswith("월세")), None)
    out = []
    for r in rows[hi + 1:]:
        if len(r) <= max(c for c in (c_sgg, c_area) if c is not None):
            continue
        loc = r[c_sgg].split()
        if len(loc) < 3:
            continue
        rec = {"sido_full": loc[0], "sido": SIDO_SHORT.get(loc[0], loc[0]), "sgg": " ".join(loc[1:-1]), "umd": loc[-1],
               "area": _num(r[c_area])}
        if kind == "trade":
            cancel = r[c_cancel].strip() if c_cancel is not None and c_cancel < len(r) else ""
            rec.update(price=_num(r[c_price]), cancel=cancel not in ("", "-"))
        else:
            rec.update(deposit=_num(r[c_dep]), rent=_num(r[c_rent]) if c_rent is not None else 0.0)
        out.append(rec)
    return kind, out


def build(files: list[Path], area=(49, 85)) -> tuple[list[dict], dict]:
    by_sgg: dict[tuple, dict] = defaultdict(lambda: {"trade": [], "rent": []})
    periods = []
    for f in files:
        kind, recs = parse_file(f)
        for r in recs:
            by_sgg[(r["sido_full"], r["sido"], r["sgg"])][kind].append(r)
        m = re.findall(r"(20\d{2})(\d{2})", f.name)
        periods += ["".join(x) for x in m]
        print(f"{f.name}: {'매매' if kind == 'trade' else '전월세'} {len(recs)}건")
    geo = Geocoder()
    regions = []
    for (sido_full, sido, sgg), d in sorted(by_sgg.items()):
        dongs = fill_missing(aggregate_records(d["trade"], d["rent"], area))
        code = re.sub(r"\s+", "", f"{sido}{sgg}")
        for umd, v in dongs.items():
            r = make_region(code, sido, sgg, umd, v, geo, sido_full=sido_full)
            if r:
                regions.append(r)
        print(f"  {sido} {sgg}: 동 {len(dongs)}곳")
    geo.save()
    meta = {"source": "국토교통부 실거래가 공개시스템 CSV (rt.molit.go.kr)", "area_m2": list(area),
            "period": f"{min(periods)}~{max(periods)}" if periods else "다운로드 기간"}
    return regions, meta


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--min-area", type=float, default=49)
    ap.add_argument("--max-area", type=float, default=85)
    ap.add_argument("--supabase", action="store_true")
    args = ap.parse_args(argv)
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parents[1] / ".env")
    except ImportError:
        pass
    regions, meta = build(args.files, (args.min_area, args.max_area))
    publish(regions, meta, supabase=args.supabase)


if __name__ == "__main__":
    main()
