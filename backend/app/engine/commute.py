"""통근 시간 계산.

ODSAY_API_KEY가 있으면 ODsay 대중교통 길찾기(searchPubTransPathT)의 실제 소요 시간을 쓰고,
없거나 호출이 실패하면 직선거리로 추정해요.
추정식: 10분(집·회사 앞 도보 + 대기) + 직선 1km당 3분
  (실제 경로는 직선의 약 1.3배, 문 앞에서 문 앞까지 평균 약 시속 26km → 직선 기준 시속 20km)
호출을 줄이려고 ① 추정치로 먼저 걸러내고 ② 남은 후보만 실제 API로 확인하고 ③ 결과를 캐시해요.
"""
from __future__ import annotations

import math
import os
from typing import Callable, Optional

import httpx

ODSAY_URL = "https://api.odsay.com/v1/api/searchPubTransPathT"
_cache: dict[str, int] = {}


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


BASE_MIN = 10.0
MIN_PER_KM = 3.0


def estimate_minutes(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    km = haversine_km(lat1, lng1, lat2, lng2)
    return int(5 * round((BASE_MIN + MIN_PER_KM * km) / 5))  # 5분 단위


def reach_km(minutes: int) -> float:
    """주어진 통근 시간으로 닿는 직선거리 (지도 원 반경과 같은 공식)."""
    return max(0.5, (minutes - BASE_MIN) / MIN_PER_KM)


def odsay_minutes(lat1: float, lng1: float, lat2: float, lng2: float) -> int | None:
    key = os.getenv("ODSAY_API_KEY")
    if not key:
        return None
    ck = f"{lat1:.3f},{lng1:.3f}>{lat2:.3f},{lng2:.3f}"
    if ck in _cache:
        return _cache[ck]
    try:
        r = httpx.get(ODSAY_URL, params={"SX": lng1, "SY": lat1, "EX": lng2, "EY": lat2, "apiKey": key}, timeout=8)
        r.raise_for_status()
        paths = r.json().get("result", {}).get("path", [])
        if not paths:
            return None
        m = min(p["info"]["totalTime"] for p in paths)
    except Exception:
        return None
    _cache[ck] = int(m)
    return int(m)


MinutesFn = Callable[[float, float, float, float], Optional[int]]


def candidate_regions(regions: list[dict], people: list[dict], limit: int = 6,
                      precise: Optional[MinutesFn] = odsay_minutes, precise_top: int = 25) -> list[dict]:
    """두 사람 모두 최대 통근 시간 안에 들어오는 동네만, 통근 합이 짧은 순으로."""
    rough = []
    for r in regions:
        est = {p["label"]: estimate_minutes(r["lat"], r["lng"], p["company"]["lat"], p["company"]["lng"]) for p in people}
        # 추정치는 오차가 있으니 15분 여유를 두고 1차로 거름
        if all(est[p["label"]] <= p["max_commute"] + 15 for p in people):
            rough.append((sum(est.values()), r, est))
    rough.sort(key=lambda x: x[0])

    out = []
    for i, (_, r, est) in enumerate(rough):
        times, provider = dict(est), "estimate"
        if precise and i < precise_top:
            real = {p["label"]: precise(r["lat"], r["lng"], p["company"]["lat"], p["company"]["lng"]) for p in people}
            if all(v is not None for v in real.values()):
                times, provider = real, "odsay"
        if all(times[p["label"]] <= p["max_commute"] for p in people):
            out.append({**r, "commute": times, "commute_provider": provider})
    out.sort(key=lambda r: sum(r["commute"].values()))
    return out[:limit]
