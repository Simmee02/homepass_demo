"""입력 → 후보 동네 → 점유형태별 자금 마련 계획."""
from __future__ import annotations

import math
from datetime import date

from .commute import candidate_regions
from .loans import Ctx, best_loan, evaluate, won

NET_RATIO = 0.82       # 세전 → 세후 근사
SAVING_RATIO = 0.45    # 월 저축 추정: 두 분 세후 월소득의 45% (맞벌이 예비부부 공동 저축 가정)


def months_until(move_in: str, today: str | None = None) -> int:
    y, m = map(int, move_in.split("-"))
    if today:
        ty, tm = map(int, today.split("-"))
    else:
        d = date.today()
        ty, tm = d.year, d.month
    return max(1, (y - ty) * 12 + (m - tm))


def estimate_monthly_saving(combined_income: int) -> int:
    net_monthly = combined_income * NET_RATIO / 12
    return int(round(net_monthly * SAVING_RATIO / 10) * 10)


def _grade_from_need(need_monthly: int, saving: int) -> str:
    if need_monthly <= 0:
        return "여유"
    return "가능" if need_monthly <= saving else "빠듯"


def build_option(tenure: str, region: dict, products: list[dict], base: dict) -> dict:
    months, saving, saved = base["months"], base["saving"], base["saved"]
    if tenure == "monthly":
        dep, rent = region["monthly"]["deposit"], region["monthly"]["rent"]
        net_monthly = base["income"] * NET_RATIO / 12
        ratio = rent / net_monthly if net_monthly else 1
        gap = max(0, dep - saved)
        need_monthly = math.ceil(gap / months) if gap else 0
        grade = "여유" if ratio <= 0.25 and gap == 0 else ("가능" if ratio <= 0.35 and need_monthly <= saving else "빠듯")
        rows = [dict(kind="saved", label="보증금", name="지금 있는 돈", sub="두 분이 모아둔 돈", amount=min(dep, saved))]
        if gap:
            rows.append(dict(kind="gap", label="더 모을 돈", name=f"입주까지 {months}개월", sub=f"월 {need_monthly:,}만씩", amount=gap))
        return dict(
            tenure="monthly", price_label=f"보증금 {dep:,} · 월 {rent}", price=dep, rent=rent, grade=grade,
            rows=rows, need_total=gap, need_monthly=need_monthly, surplus=max(0, saved - dep),
            tip=f"월세가 세후 월소득의 약 {round(ratio * 100)}%예요", loans=[],
        )

    price = region[tenure]
    ctx = Ctx(
        combined_income=base["income"], net_asset=saved, marriage=base["marriage"],
        first_home=base["first_home"], homeless=base["homeless"],
        existing_loan_monthly=base["existing"], price=price, capital=region["capital"],
    )
    loans = [evaluate(p, ctx) for p in products if p["tenure"] == tenure]
    loans.sort(key=lambda l: (l["status"] == "no", -l["amount"]))
    best = best_loan(loans)
    loan_amt = best["amount"] if best else 0
    gap = max(0, price - loan_amt - saved)
    need_monthly = math.ceil(gap / months) if gap else 0
    surplus = max(0, saved - (price - loan_amt))
    grade = _grade_from_need(need_monthly, saving)

    rows = []
    if best:
        rows.append(dict(kind="loan", label="대출", name=best["name"], sub=f"{best['limit_label']} · {best['rate_label']}",
                         amount=loan_amt, product_id=best["product_id"]))
    rows.append(dict(kind="saved", label="지금 있는 돈", name="주거 자금", sub="두 분이 모아둔 돈", amount=min(saved, price - loan_amt)))
    if gap:
        rows.append(dict(kind="gap", label="더 모을 돈", name=f"입주까지 {months}개월", sub=f"월 {need_monthly:,}만씩 모으면 채워요", amount=gap))

    if grade == "여유":
        tip = f"입주 때 {won(surplus)}원이 남아요" if surplus else "입주 시점에 딱 맞아요"
    elif grade == "가능":
        tip = f"월 {need_monthly:,}만씩 모으면 입주 때 맞출 수 있어요"
    else:
        extra = math.ceil(gap / saving) - months if saving else 999
        if extra <= 24:
            tip = f"월 {need_monthly:,}만이 필요해요. 지금 저축 속도면 입주를 {extra}개월 늦추면 가능해요"
        else:
            tip = f"예산보다 {won(gap)} 더 필요해요. 다른 동네나 점유 형태를 먼저 보세요"

    label = "아파트 전세" if tenure == "jeonse" else "아파트 매매"
    return dict(tenure=tenure, price_label=f"{label} 약 {won(price)}", price=price, grade=grade, rows=rows,
                need_total=gap, need_monthly=need_monthly, surplus=surplus, tip=tip, loans=loans)


def make_plan(inp: dict, regions: list[dict], products: list[dict], effective_date: str) -> dict:
    people = inp["people"]
    income = sum(p["income"] for p in people)
    months = months_until(inp["move_in"], inp.get("today"))
    estimated = inp.get("monthly_saving") is None
    saving = estimate_monthly_saving(income) if estimated else inp["monthly_saving"]
    base = dict(months=months, saving=saving, saved=inp["saved"], income=income, marriage=inp["marriage"],
                first_home=inp.get("first_home", True), homeless=inp.get("homeless", True),
                existing=inp.get("existing_loan_monthly", 0))

    out = []
    for r in candidate_regions(regions, people):
        opts = {t: build_option(t, r, products, base) for t in ("jeonse", "monthly", "buy")}
        out.append(dict(id=r["id"], name=r["name"], lat=r["lat"], lng=r["lng"], commute=r["commute"], options=opts))
    rank = {"여유": 0, "가능": 1, "빠듯": 2}
    out.sort(key=lambda r: (min(rank[o["grade"]] for k, o in r["options"].items() if k != "monthly"),
                            sum(r["commute"].values())))

    notes = ["대출 한도·금리는 공개 기준으로 계산한 예상치예요. 최종 심사는 취급 기관에서 해요."]
    if estimated:
        notes.append(f"월 저축액은 소득으로 추정했어요(월 {saving:,}만). 분담 화면에서 바꿀 수 있어요.")
    return dict(months=months, combined_income=income, monthly_saving=saving, monthly_saving_estimated=estimated,
                regions=out, rules_effective_date=effective_date, notes=notes)
