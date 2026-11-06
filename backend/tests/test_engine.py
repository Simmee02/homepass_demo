import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.engine.commute import estimate_minutes
from app.engine.loans import Ctx, evaluate, won
from app.engine.plan import make_plan, months_until
from app.main import app

DATA = Path(__file__).parents[1] / "app" / "data"
PRODUCTS = json.loads((DATA / "loan_products.json").read_text())["products"]
REGIONS = json.loads((DATA / "regions.json").read_text())["regions"]
P = {p["id"]: p for p in PRODUCTS}

PANGYO = {"name": "판교", "lat": 37.4020, "lng": 127.1080}
GANGNAM = {"name": "강남역", "lat": 37.4979, "lng": 127.0276}

SAMPLE = {
    "marriage": "soon", "move_in": "2027-09", "today": "2026-11",
    "people": [
        {"label": "A", "company": PANGYO, "max_commute": 45, "income": 4200},
        {"label": "B", "company": GANGNAM, "max_commute": 60, "income": 3600},
    ],
    "saved": 4000, "existing_loan_monthly": 0,
}


def ctx(**kw):
    base = dict(combined_income=7800, net_asset=4000, marriage="soon", first_home=True, homeless=True,
                existing_loan_monthly=0, price=30000, capital=True)
    base.update(kw)
    return Ctx(**base)


def test_won_format():
    assert won(32000) == "3.2억"
    assert won(7800) == "7,800만"
    assert won(25500) == "2억 5,500만"


def test_months():
    assert months_until("2027-09", "2026-11") == 10


def test_commute_estimate():
    assert 20 <= estimate_minutes(37.45, 127.146, PANGYO["lat"], PANGYO["lng"]) <= 35  # 신흥동→판교 실제 약 30분


def test_beotimmok_income_over():
    r = evaluate(P["beotimmok_newlywed"], ctx())
    assert r["status"] == "no"
    assert "300만 초과" in r["reason"]


def test_didimdol_conditional_when_marriage_later():
    r = evaluate(P["didimdol_newlywed"], ctx(price=42000, marriage="year"))
    assert r["status"] == "conditional"
    assert r["amount"] == 29400  # 수도권 LTV 70% (4.2억 × 0.7)


def test_didimdol_ok_when_marrying_within_3_months():
    assert evaluate(P["didimdol_newlywed"], ctx(price=42000))["status"] == "ok"


def test_bogeumjari_single_income_rule():
    # 합산 9,000만 > 8,500만이지만 한 분이 7,000만 이하 → 2026.10.19 개선안으로 가능
    r = evaluate(P["bogeumjari"], ctx(combined_income=9000, incomes=(6500, 2500), price=50000))
    assert r["status"] == "ok"
    assert r["checks"][0]["label"] == "소득 (1인 기준)"


def test_beotimmok_rate_table():
    r = evaluate(P["beotimmok_newlywed"], ctx(combined_income=5000, price=12000))
    assert r["rate_label"] == "연 2.8%"


def test_didimdol_ok_after_marriage():
    r = evaluate(P["didimdol_newlywed"], ctx(price=42000, marriage="done"))
    assert r["status"] == "ok"


def test_existing_loan_reduces_limit():
    a = evaluate(P["hf_jeonse_guarantee"], ctx(price=60000, combined_income=4000))
    b = evaluate(P["hf_jeonse_guarantee"], ctx(price=60000, combined_income=4000, existing_loan_monthly=60))
    assert b["amount"] < a["amount"]


def test_plan_end_to_end():
    out = make_plan(SAMPLE, REGIONS, PRODUCTS, "2026-10-01")
    assert out["months"] == 10
    names = [r["name"] for r in out["regions"]]
    assert "성남 수정구" in names
    sj = next(r for r in out["regions"] if r["name"] == "성남 수정구")
    j = sj["options"]["jeonse"]
    assert j["rows"][0]["kind"] == "loan" and j["rows"][0]["amount"] == 24000
    assert j["need_total"] == 2000 and j["need_monthly"] == 200


def test_api():
    c = TestClient(app)
    assert c.get("/api/health").json()["ok"]
    r = c.post("/api/plan", json=SAMPLE)
    assert r.status_code == 200
    assert r.json()["regions"]
    assert c.get("/api/companies", params={"q": "판교"}).json()["places"]
    sid = c.post("/api/plans", json={"input": SAMPLE}).json()["id"]
    assert c.get(f"/api/plans/{sid}").status_code == 200


def test_reach_matches_estimate():
    from app.engine.commute import reach_km
    assert 11 < reach_km(45) < 13      # 45분 ≈ 직선 12km
    assert 6 < reach_km(30) < 7.5
