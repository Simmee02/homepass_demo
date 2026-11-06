"""키가 제대로 들어갔는지 한 번에 확인해요:  python -m collect.check_keys"""
from pathlib import Path
import os

import httpx

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parents[1] / ".env")
except ImportError:
    pass


def check(name, fn):
    try:
        print(f"[OK]   {name}: {fn()}")
    except Exception as e:  # noqa: BLE001
        print(f"[FAIL] {name}: {e}")


def molit():
    from .prices import TRADE_URL, parse_items
    key = os.environ["MOLIT_SERVICE_KEY"]
    r = httpx.get(TRADE_URL, params={"serviceKey": key, "LAWD_CD": "41131", "DEAL_YMD": "202609", "pageNo": 1, "numOfRows": 5}, timeout=15)
    items, total = parse_items(r.text)
    return f"성남 수정구 2026.09 매매 {total}건"


def kakao_geo():
    from .kakao import geocode
    return geocode("경기 성남시 수정구 신흥동")


def odsay():
    from app.engine.commute import odsay_minutes
    m = odsay_minutes(37.45, 127.146, 37.402, 127.108)
    if m is None:
        raise RuntimeError("응답 없음 (키 또는 등록된 서버 IP/URI 확인)")
    return f"신흥동→판교 {m}분"


check("국토부 실거래가 (MOLIT_SERVICE_KEY)", molit)
check("카카오 로컬 (KAKAO_REST_KEY)", kakao_geo)
check("ODsay (ODSAY_API_KEY)", odsay)
