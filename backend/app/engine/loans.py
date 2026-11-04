"""대출 자격·한도 판정. 규칙은 data/loan_products.json(운영 시 Supabase loan_products)에서 읽어요.

원칙: 숫자는 여기서 규칙으로만 계산해요. LLM은 이 결과를 설명만 해요.
"""
from __future__ import annotations

from dataclasses import dataclass


def won(v: int | float) -> str:
    """만원 단위 숫자를 '3.2억', '7,800만' 형태로."""
    v = int(round(v))
    if v >= 10000:
        eok, man = divmod(v, 10000)
        if man == 0:
            return f"{eok}억"
        if man % 1000 == 0:
            return f"{eok}.{man // 1000}억"
        return f"{eok}억 {man:,}만"
    return f"{v:,}만"


@dataclass
class Ctx:
    combined_income: int
    net_asset: int
    marriage: str  # soon | year | undecided | done
    first_home: bool
    homeless: bool
    existing_loan_monthly: int
    price: int  # 매매가 또는 전세 보증금
    capital: bool


def _newlywed_status(marriage: str) -> str:
    # 혼인 7년 이내(이미 신고) 또는 입주 전 신고 예정이면 신혼 기준을 적용할 수 있어요.
    return "ok" if marriage == "done" else "warn"


def _annuity_pv(monthly_payment: float, annual_rate: float, years: int = 30) -> float:
    r = annual_rate / 100 / 12
    n = years * 12
    if r == 0:
        return monthly_payment * n
    return monthly_payment * (1 - (1 + r) ** -n) / r


def evaluate(product: dict, ctx: Ctx) -> dict:
    checks: list[dict] = []
    newlywed = product["marital"] == "newlywed"

    income_max = product.get("income_max")
    if product.get("income_max_newlywed"):
        income_max = product["income_max_newlywed"]  # 예비부부는 신혼 기준으로 안내
    if income_max:
        ok = ctx.combined_income <= income_max
        checks.append(dict(key="income", label="부부합산 소득", mine=won(ctx.combined_income),
                           standard=f"{won(income_max)} 이하", status="ok" if ok else "no"))

    if product.get("net_asset_max"):
        ok = ctx.net_asset <= product["net_asset_max"]
        checks.append(dict(key="net_asset", label="순자산", mine=won(ctx.net_asset),
                           standard=f"{won(product['net_asset_max'])} 이하", status="ok" if ok else "no"))

    if product["tenure"] == "buy" and product.get("price_max"):
        ok = ctx.price <= product["price_max"]
        checks.append(dict(key="price", label="주택 가격", mine=won(ctx.price),
                           standard=f"{won(product['price_max'])} 이하", status="ok" if ok else "no"))

    if product["tenure"] == "jeonse" and product.get("deposit_max"):
        cap = product["deposit_max"]["capital" if ctx.capital else "other"]
        ok = ctx.price <= cap
        checks.append(dict(key="deposit", label="전세 보증금", mine=won(ctx.price),
                           standard=f"{won(cap)} 이하", status="ok" if ok else "no"))

    checks.append(dict(key="homeless", label="무주택", mine="두 분 모두 무주택" if ctx.homeless else "주택 있음",
                       standard="세대원 전원 무주택", status="ok" if ctx.homeless else "no"))

    if newlywed or product.get("income_max_newlywed"):
        st = _newlywed_status(ctx.marriage)
        checks.append(dict(key="marriage", label="혼인 상태",
                           mine="혼인신고 완료" if ctx.marriage == "done" else "입주 전 신고 예정",
                           standard="신혼가구 (혼인 7년 이내)", status=st))

    # 한도
    if product["tenure"] == "buy":
        ltv = product["ltv"].get("first_home" if ctx.first_home else "default", product["ltv"]["default"])
        cap_limit = product["limit"].get("first_home" if ctx.first_home else "default", product["limit"]["default"])
        rate = (product["rate"]["min"] + product["rate"]["max"]) / 2
        monthly_capacity = max(0.0, ctx.combined_income * product["repay_ratio"] / 12 - ctx.existing_loan_monthly)
        by_income = _annuity_pv(monthly_capacity, rate)
        amount = min(cap_limit, ctx.price * ltv, by_income)
        limit_label = f"최대 {won(cap_limit)}"
    else:
        region_key = "capital" if ctx.capital else "other"
        cap_limit = product["limit"][region_key]
        rate = (product["rate"]["min"] + product["rate"]["max"]) / 2
        annual_capacity = max(0.0, ctx.combined_income * product["repay_ratio"] - ctx.existing_loan_monthly * 12)
        by_income = annual_capacity / (rate / 100)  # 전세대출은 이자만 낸다고 보고 계산
        amount = min(cap_limit, ctx.price * product["deposit_ratio"], by_income)
        limit_label = f"보증금 {int(product['deposit_ratio'] * 100)}% · 최대 {won(cap_limit)}"
    amount = int(amount // 100 * 100)  # 100만원 단위 내림

    statuses = [c["status"] for c in checks]
    status = "no" if "no" in statuses else ("conditional" if "warn" in statuses else "ok")
    if status == "no":
        amount = 0

    failed = [c for c in checks if c["status"] == "no"]
    if failed:
        c = failed[0]
        reason = f"{c['label']} {c['mine']} — 기준({c['standard']})을 넘어요"
        if c["key"] == "income" and income_max:
            reason = f"합산 {won(ctx.combined_income)} > {won(income_max)} · {won(ctx.combined_income - income_max)} 초과"
    elif status == "conditional":
        reason = "신청 전에 혼인신고가 필요해요"
    else:
        reason = "두 분 조건이 모두 기준 안에 있어요"

    rate_label = product.get("rate_label") or f"연 {product['rate']['min']}~{product['rate']['max']}%"
    pref = []
    for p in product.get("preferential", []):
        applied = (
            (p["auto"] == "newlywed")
            or (p["auto"] == "first_home" and ctx.first_home)
            or (p["auto"] == "newlywed_low_income" and ctx.combined_income <= 7000)
        )
        pref.append({**p, "applied": bool(applied) if p["auto"] else None})

    return dict(
        product_id=product["id"], name=product["name"], org=product["org"], tenure=product["tenure"],
        status=status, amount=amount, limit_label=limit_label, rate_label=rate_label,
        checks=checks, reason=reason, preferential=pref, apply=product["apply"],
    )


def best_loan(results: list[dict]) -> dict | None:
    usable = [r for r in results if r["status"] != "no" and r["amount"] > 0]
    if not usable:
        return None
    # 금액 우선, 같으면 판정이 확실한 것(ok) 우선
    usable.sort(key=lambda r: (r["amount"], r["status"] == "ok"), reverse=True)
    return usable[0]
