"""AI 설명. 계산이 끝난 숫자를 문장으로만 풀어요. 숫자를 새로 만들거나 상품을 추천하지 않아요.

ANTHROPIC_API_KEY가 없으면 규칙 기반 문장으로 대신해요.
"""
from __future__ import annotations

import json
import os

import httpx

from .engine.loans import won

SYSTEM = (
    "너는 예비부부 주거 예산 서비스 '홈패스'의 설명 담당이야. "
    "입력 JSON에 있는 숫자와 판정만 사용해서 3문장 이내 한국어 존댓말로 설명해. "
    "규칙: 새 숫자를 만들거나 계산하지 마. 특정 상품 가입을 권유하거나 집값·금리를 예측하지 마. "
    "투자 조언을 하지 마. 마지막에 '최종 심사는 취급 기관에서 해요'를 붙여."
)


def template(region: str, option: dict) -> str:
    rows = option["rows"]
    loan = next((r for r in rows if r["kind"] == "loan"), None)
    parts = [f"{region}의 {option['price_label']}을 기준으로 계산했어요."]
    if loan:
        parts.append(f"{loan['name']}으로 {won(loan['amount'])}원을 빌리고, 모아둔 돈을 더하는 방식이에요.")
    parts.append(option["tip"] + ".")
    parts.append("최종 심사는 취급 기관에서 해요.")
    return " ".join(parts)


def explain(region: str, option: dict) -> dict:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return {"text": template(region, option), "source": "template"}
    slim = {k: option[k] for k in ("tenure", "price_label", "grade", "rows", "need_monthly", "surplus", "tip")}
    slim["loans"] = [{k: l[k] for k in ("name", "status", "reason")} for l in option.get("loans", [])]
    try:
        r = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={
                "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
                "max_tokens": 300,
                "system": SYSTEM,
                "messages": [{"role": "user", "content": json.dumps({"region": region, **slim}, ensure_ascii=False)}],
            },
            timeout=20,
        )
        r.raise_for_status()
        text = "".join(b.get("text", "") for b in r.json().get("content", []))
        return {"text": text.strip(), "source": "llm"}
    except Exception:
        return {"text": template(region, option), "source": "template"}
