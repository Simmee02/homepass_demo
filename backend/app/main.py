from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .engine.plan import make_plan
from .explain import explain
from .models import PlanInput, PlanResult
from .repo import Repo, get_repo

app = FastAPI(title="홈패스 API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health(repo: Repo = Depends(get_repo)):
    return {"ok": True, "storage": "supabase" if repo.remote else "local"}


@app.get("/api/companies")
def companies(q: str = Query("", max_length=50), repo: Repo = Depends(get_repo)):
    """회사 검색. 운영에서는 카카오 로컬 API(KAKAO_REST_KEY)로 바꿔요."""
    places = repo.companies()
    q = q.strip()
    if q:
        places = [p for p in places if q in p["name"] or q in p["address"]]
    return {"places": places[:10]}


@app.post("/api/plan", response_model=PlanResult)
def plan(inp: PlanInput, repo: Repo = Depends(get_repo)):
    products, eff = repo.loan_products()
    return make_plan(inp.model_dump(), repo.regions(), products, eff)


@app.get("/api/loan-products")
def loan_products(repo: Repo = Depends(get_repo)):
    products, eff = repo.loan_products()
    return {"effective_date": eff, "products": products}


class ExplainIn(BaseModel):
    region: str
    option: dict


@app.post("/api/explain")
def explain_option(body: ExplainIn):
    return explain(body.region, body.option)


class SaveIn(BaseModel):
    input: dict
    result: dict | None = None


@app.post("/api/plans")
def save_plan(body: SaveIn, repo: Repo = Depends(get_repo)):
    return {"id": repo.save_plan(body.model_dump())}


@app.get("/api/plans/{pid}")
def get_plan(pid: str, repo: Repo = Depends(get_repo)):
    p = repo.get_plan(pid)
    if not p:
        raise HTTPException(404, "플랜을 찾을 수 없어요")
    return p
