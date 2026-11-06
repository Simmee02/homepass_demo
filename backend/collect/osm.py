"""오픈스트리트맵 Nominatim (키 불필요). 카카오 키가 없을 때 회사 검색·동네 좌표에 써요.

이용 정책: 초당 1회 이하, 식별 가능한 User-Agent 필수 → https://operations.osmfoundation.org/policies/nominatim/
서비스 규모가 커지면 카카오 로컬 API로 바꾸세요.
"""
from __future__ import annotations

import os
import time

import httpx

URL = "https://nominatim.openstreetmap.org/search"
UA = os.getenv("OSM_USER_AGENT", "homepass-demo/0.1")
_last = 0.0


def _wait() -> None:
    global _last
    gap = time.time() - _last
    if gap < 1.05:
        time.sleep(1.05 - gap)
    _last = time.time()


def _get(params: dict, client: httpx.Client | None = None) -> list[dict]:
    _wait()
    c = client or httpx
    r = c.get(URL, params={"format": "jsonv2", "countrycodes": "kr", "accept-language": "ko", **params},
              headers={"User-Agent": UA}, timeout=10)
    r.raise_for_status()
    return r.json()


def _addr(d: dict) -> str:
    a = d.get("address") or {}
    parts = [a.get(k) for k in ("province", "city", "borough", "suburb", "quarter", "road", "house_number") if a.get(k)]
    return " ".join(parts) or d.get("display_name", "")


AREA_TYPES = {"boundary", "place"}  # 동·구 같은 지역 결과


def search(query: str, limit: int = 8, client: httpx.Client | None = None) -> list[dict]:
    """건물·회사 결과를 앞에, '성수' 같은 동네 결과는 뒤에 둬요."""
    docs = _get({"q": query, "limit": limit, "addressdetails": 1, "extratags": 1}, client)
    out = []
    for d in docs:
        area = d.get("category") in AREA_TYPES or d.get("addresstype") in {"suburb", "quarter", "neighbourhood", "city_district", "borough", "city"}
        a = d.get("address") or {}
        name = d.get("name") or a.get("building") or a.get("amenity") or a.get("office") or ""
        if not name:
            road = " ".join(x for x in (a.get("road"), a.get("house_number")) if x)
            name = road or d.get("display_name", "").split(",")[0]
        out.append({"name": name, "address": _addr(d), "lat": float(d["lat"]), "lng": float(d["lon"]),
                    "kind": "area" if area else "place"})
    out.sort(key=lambda x: x["kind"] == "area")
    return out


def geocode(query: str, client: httpx.Client | None = None) -> tuple[float, float] | None:
    docs = _get({"q": query, "limit": 1}, client)
    return (float(docs[0]["lat"]), float(docs[0]["lon"])) if docs else None
