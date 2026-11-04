"""데이터 저장소. SUPABASE_URL·SUPABASE_SERVICE_KEY가 있으면 Supabase(PostgREST)를, 없으면 로컬 JSON·메모리를 써요."""
from __future__ import annotations

import json
import os
import uuid
from functools import lru_cache
from pathlib import Path

import httpx

DATA = Path(__file__).parent / "data"


def _load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class Repo:
    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.key = os.getenv("SUPABASE_SERVICE_KEY", "")
        self._plans: dict[str, dict] = {}

    @property
    def remote(self) -> bool:
        return bool(self.url and self.key)

    def _headers(self) -> dict:
        return {"apikey": self.key, "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}

    # ---- 규칙·시세 ----
    def loan_products(self) -> tuple[list[dict], str]:
        if self.remote:
            r = httpx.get(f"{self.url}/rest/v1/loan_products?select=rule,effective_date&active=eq.true",
                          headers=self._headers(), timeout=10)
            r.raise_for_status()
            rows = r.json()
            if rows:
                return [row["rule"] for row in rows], max(row["effective_date"] for row in rows)
        d = _load("loan_products.json")
        return d["products"], d["effective_date"]

    def regions(self) -> list[dict]:
        if self.remote:
            r = httpx.get(f"{self.url}/rest/v1/regions?select=*", headers=self._headers(), timeout=10)
            r.raise_for_status()
            rows = r.json()
            if rows:
                return [{**row, "monthly": {"deposit": row["monthly_deposit"], "rent": row["monthly_rent"]}} for row in rows]
        return _load("regions.json")["regions"]

    def companies(self) -> list[dict]:
        return _load("companies.json")["places"]

    # ---- 플랜 공유 ----
    def save_plan(self, payload: dict) -> str:
        pid = uuid.uuid4().hex[:10]
        if self.remote:
            r = httpx.post(f"{self.url}/rest/v1/plans", headers={**self._headers(), "Prefer": "return=minimal"},
                           json={"id": pid, "input": payload["input"], "result": payload.get("result")}, timeout=10)
            r.raise_for_status()
        else:
            self._plans[pid] = payload
        return pid

    def get_plan(self, pid: str) -> dict | None:
        if self.remote:
            r = httpx.get(f"{self.url}/rest/v1/plans?id=eq.{pid}&select=input,result", headers=self._headers(), timeout=10)
            r.raise_for_status()
            rows = r.json()
            return rows[0] if rows else None
        return self._plans.get(pid)


@lru_cache
def get_repo() -> Repo:
    return Repo()
