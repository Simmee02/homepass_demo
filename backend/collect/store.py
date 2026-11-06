"""수집 결과 공통 처리: 좌표 붙이기 → JSON·CSV 저장 → (선택) Supabase 적재."""
from __future__ import annotations

import csv
import json
import os
from datetime import date
from pathlib import Path

import httpx

from .sigungu import CAPITAL_SIDO, short_name

DATA = Path(__file__).parents[1] / "app" / "data"
OUT_JSON = DATA / "regions_real.json"
OUT_CSV = Path(__file__).parents[2] / "supabase" / "regions.csv"
GEO_CACHE = DATA / "geocode_cache.json"
CSV_COLUMNS = ["id", "name", "lat", "lng", "capital", "jeonse", "buy", "monthly_deposit", "monthly_rent", "sample"]


class Geocoder:
    """카카오 키가 있으면 카카오, 없으면 오픈스트리트맵(Nominatim). 결과는 파일로 캐시해요."""

    def __init__(self) -> None:
        self.cache: dict = json.loads(GEO_CACHE.read_text(encoding="utf-8")) if GEO_CACHE.exists() else {}
        self.provider = "kakao" if os.getenv("KAKAO_REST_KEY") else ("mapbox" if os.getenv("MAPBOX_TOKEN") else "osm")

    def __call__(self, query: str) -> tuple[float, float] | None:
        if query in self.cache:
            v = self.cache[query]
            return tuple(v) if v else None
        try:
            if self.provider == "kakao":
                from .kakao import geocode
            elif self.provider == "mapbox":
                from .mapbox import geocode
            else:
                from .osm import geocode
            v = geocode(query)
        except Exception as e:  # noqa: BLE001
            print(f"  좌표 실패: {query} ({e})")
            v = None
        self.cache[query] = list(v) if v else None
        return v

    def save(self) -> None:
        GEO_CACHE.write_text(json.dumps(self.cache, ensure_ascii=False, indent=1), encoding="utf-8")


def make_region(code: str, sido: str, sgg: str, umd: str, d: dict, geo: Geocoder, sido_full: str | None = None) -> dict | None:
    pt = geo(f"{sido_full or sido} {sgg} {umd}")
    if not pt:
        return None
    return {
        "id": f"{code}_{umd}", "name": f"{short_name(sido, sgg)} {umd}", "lat": pt[0], "lng": pt[1],
        "capital": sido in CAPITAL_SIDO, "jeonse": d["jeonse"], "buy": d["buy"],
        "monthly": {"deposit": d["monthly_deposit"], "rent": d["monthly_rent"]},
        "n": d["n"], "filled_from_sigungu": d["filled"],
    }


def publish(regions: list[dict], meta: dict, supabase: bool = False) -> None:
    doc = {**meta, "method": "법정동별 중앙값, 표본 3건 미만은 시군구 중앙값으로 대체",
           "collected": date.today().isoformat(), "sample": False, "regions": regions}
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")

    rows = [{"id": r["id"], "name": r["name"], "lat": r["lat"], "lng": r["lng"], "capital": r["capital"],
             "jeonse": r["jeonse"], "buy": r["buy"], "monthly_deposit": r["monthly"]["deposit"],
             "monthly_rent": r["monthly"]["rent"], "sample": False} for r in regions]
    OUT_CSV.parent.mkdir(exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"저장: {OUT_JSON} · {OUT_CSV} ({len(regions)}곳)")

    if supabase:
        url, key = os.environ["SUPABASE_URL"].rstrip("/"), os.environ["SUPABASE_SERVICE_KEY"]
        h = {"apikey": key, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"}
        if not key.startswith("sb_"):
            h["Authorization"] = f"Bearer {key}"
        for i in range(0, len(rows), 500):
            httpx.post(f"{url}/rest/v1/regions", headers=h, json=rows[i:i + 500], timeout=30).raise_for_status()
        print(f"Supabase regions 테이블에 {len(rows)}곳 적재 완료")
