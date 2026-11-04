"""요청·응답 스키마. 금액 단위는 모두 만원."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Marriage = Literal["soon", "year", "undecided", "done"]
Tenure = Literal["jeonse", "monthly", "buy"]
Grade = Literal["여유", "가능", "빠듯"]


class Place(BaseModel):
    name: str
    address: str = ""
    lat: float
    lng: float


class Person(BaseModel):
    label: str = Field(examples=["A"])
    company: Place
    max_commute: int = Field(ge=10, le=180, description="편도 최대 통근 시간(분)")
    income: int = Field(ge=0, description="세전 연소득(만원)")


class PlanInput(BaseModel):
    marriage: Marriage
    move_in: str = Field(pattern=r"^\d{4}-\d{2}$", examples=["2027-09"])
    people: list[Person] = Field(min_length=2, max_length=2)
    saved: int = Field(ge=0, description="주거 자금으로 모아둔 돈(만원)")
    existing_loan_monthly: int = Field(0, ge=0, description="기존 대출 월 상환액 합계(만원)")
    monthly_saving: Optional[int] = Field(None, ge=0, description="월 저축액. 없으면 소득으로 추정")
    first_home: bool = True
    homeless: bool = True
    today: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$", description="테스트용 기준 월")


class Check(BaseModel):
    key: str
    label: str
    mine: str
    standard: str
    status: Literal["ok", "warn", "no"]


class LoanResult(BaseModel):
    product_id: str
    name: str
    org: str
    tenure: Tenure
    status: Literal["ok", "conditional", "no"]
    amount: int = 0
    limit_label: str
    rate_label: str
    checks: list[Check]
    reason: str
    preferential: list[dict] = []
    apply: dict


class FundingRow(BaseModel):
    kind: Literal["loan", "saved", "gap"]
    label: str
    name: str
    sub: str
    amount: int
    product_id: Optional[str] = None


class Option(BaseModel):
    tenure: Tenure
    price_label: str
    price: int
    grade: Grade
    rows: list[FundingRow]
    need_total: int
    need_monthly: int
    surplus: int
    tip: str
    loans: list[LoanResult]
    rent: Optional[int] = None


class RegionResult(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    commute: dict[str, int]
    options: dict[str, Option]


class PlanResult(BaseModel):
    months: int
    combined_income: int
    monthly_saving: int
    monthly_saving_estimated: bool
    regions: list[RegionResult]
    rules_effective_date: str
    notes: list[str]
