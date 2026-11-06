"""Mapbox Search Box API (회사·건물 검색, 좌표 → 주소). 토큰: MAPBOX_TOKEN (pk.로 시작하는 공개 토큰도 돼요)

문서: https://docs.mapbox.com/api/search/search-box/
"""
from __future__ import annotations

import os

import httpx

BASE = "https://api.mapbox.com/search/searchbox/v1"


def _token() -> str:
    t = os.getenv("MAPBOX_TOKEN")
    if not t:
        raise RuntimeError("MAPBOX_TOKEN이 없어요")
    return t


def _place(f: dict) -> dict:
    p = f.get("properties", {})
    lng, lat = f["geometry"]["coordinates"]
    addr = p.get("full_address") or p.get("place_formatted") or p.get("address") or ""
    kind = "area" if p.get("feature_type") in {"region", "district", "place", "locality", "neighborhood", "postcode"} else "place"
    return {"name": p.get("name") or addr, "address": addr, "lat": float(lat), "lng": float(lng), "kind": kind}


def search(query: str, limit: int = 8) -> list[dict]:
    r = httpx.get(f"{BASE}/forward", params={"q": query, "country": "kr", "language": "ko", "limit": limit,
                                             "access_token": _token()}, timeout=10)
    r.raise_for_status()
    out = [_place(f) for f in r.json().get("features", [])]
    out.sort(key=lambda x: x["kind"] == "area")
    return out


def reverse(lat: float, lng: float) -> dict | None:
    r = httpx.get(f"{BASE}/reverse", params={"latitude": lat, "longitude": lng, "language": "ko", "limit": 1,
                                             "access_token": _token()}, timeout=10)
    r.raise_for_status()
    feats = r.json().get("features", [])
    if not feats:
        return None
    p = _place(feats[0])
    return {**p, "lat": lat, "lng": lng}


def geocode(query: str, client: httpx.Client | None = None) -> tuple[float, float] | None:
    """주소(시군구 + 법정동) → (lat, lng). Geocoding v6."""
    c = client or httpx
    r = c.get("https://api.mapbox.com/search/geocode/v6/forward",
              params={"q": query, "country": "kr", "language": "ko", "limit": 1, "access_token": _token()}, timeout=10)
    r.raise_for_status()
    feats = r.json().get("features", [])
    if not feats:
        return None
    lng, lat = feats[0]["geometry"]["coordinates"]
    return float(lat), float(lng)
