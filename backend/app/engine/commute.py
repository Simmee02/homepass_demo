"""통근 시간 계산.

외부 키(ODSAY_API_KEY)가 없으면 직선거리로 대중교통 시간을 추정해요.
추정식: 8분(도보·대기) + 2.3분/km. 수도권 지하철 평균 표정속도를 감안한 근사치예요.
"""
from __future__ import annotations

import math


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def estimate_minutes(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    km = haversine_km(lat1, lng1, lat2, lng2)
    minutes = 8 + 2.3 * km
    return int(5 * round(minutes / 5))  # 5분 단위


def candidate_regions(regions: list[dict], people: list[dict], limit: int = 6) -> list[dict]:
    """두 사람 모두 최대 통근 시간 안에 들어오는 동네만, 통근 합이 짧은 순으로."""
    out = []
    for r in regions:
        times = {
            p["label"]: estimate_minutes(r["lat"], r["lng"], p["company"]["lat"], p["company"]["lng"])
            for p in people
        }
        if all(times[p["label"]] <= p["max_commute"] for p in people):
            out.append({**r, "commute": times})
    out.sort(key=lambda r: sum(r["commute"].values()))
    return out[:limit]
