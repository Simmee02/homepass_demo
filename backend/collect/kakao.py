"""카카오 로컬 API. 키: developers.kakao.com > 내 애플리케이션 > REST API 키 → KAKAO_REST_KEY"""
from __future__ import annotations

import os

import httpx

BASE = "https://dapi.kakao.com/v2/local/search"


def _headers() -> dict:
    key = os.getenv("KAKAO_REST_KEY")
    if not key:
        raise RuntimeError("KAKAO_REST_KEY가 없어요")
    return {"Authorization": f"KakaoAK {key}"}


def geocode(query: str, client: httpx.Client | None = None) -> tuple[float, float] | None:
    """주소 → (lat, lng). 법정동 이름은 address 검색이 가장 정확해요."""
    c = client or httpx.Client(timeout=10)
    r = c.get(f"{BASE}/address.json", params={"query": query, "size": 1}, headers=_headers())
    r.raise_for_status()
    docs = r.json().get("documents", [])
    if not docs:
        return None
    return float(docs[0]["y"]), float(docs[0]["x"])


def keyword(query: str, size: int = 10) -> list[dict]:
    """회사·건물 이름 검색."""
    r = httpx.get(f"{BASE}/keyword.json", params={"query": query, "size": size}, headers=_headers(), timeout=10)
    r.raise_for_status()
    return [
        {"name": d["place_name"], "address": d.get("road_address_name") or d.get("address_name", ""),
         "lat": float(d["y"]), "lng": float(d["x"])}
        for d in r.json().get("documents", [])
    ]
