from __future__ import annotations

import os
from typing import Optional
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parents[1] / ".env")
except ImportError:
    pass

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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


@app.exception_handler(RequestValidationError)
async def on_validation_error(request: Request, exc: RequestValidationError):
    errs = [{"field": ".".join(str(x) for x in e["loc"][1:]), "msg": e["msg"], "input": e.get("input")} for e in exc.errors()]
    print("[422]", request.url.path, errs, flush=True)
    msg = ", ".join(f"{e['field']}: {e['msg']}" for e in errs)
    return JSONResponse(status_code=422, content={"message": msg, "errors": errs})


@app.get("/api/health")
def health(repo: Repo = Depends(get_repo)):
    meta = repo.regions_meta()
    return {"ok": True, "storage": "supabase" if repo.remote else "local", "prices": "sample" if meta.get("sample", True) else "real",
            "kakao": bool(os.getenv("KAKAO_REST_KEY")), "mapbox": bool(os.getenv("MAPBOX_TOKEN")), "odsay": bool(os.getenv("ODSAY_API_KEY")),
            "llm": bool(os.getenv("ANTHROPIC_API_KEY"))}


@app.get("/api/companies")
def companies(q: str = Query("", max_length=50), repo: Repo = Depends(get_repo)):
    """회사 검색: 카카오(KAKAO_REST_KEY) → 오픈스트리트맵(키 불필요) → 예시 업무지구 순으로 시도해요."""
    q = q.strip()
    if q and os.getenv("KAKAO_REST_KEY"):
        from collect import kakao
        try:
            return {"places": kakao.keyword(q), "source": "kakao"}
        except Exception:
            pass
    if len(q) >= 2 and os.getenv("MAPBOX_TOKEN"):
        from collect import mapbox
        try:
            found = mapbox.search(q)
            if found:
                return {"places": found, "source": "mapbox"}
        except Exception:
            pass
    if len(q) >= 2 and os.getenv("OSM_SEARCH", "1") == "1":
        from collect import osm
        try:
            found = osm.search(q)
            if found:
                return {"places": found, "source": "osm"}
        except Exception:
            pass
    places = repo.companies()
    if q:
        places = [p for p in places if q in p["name"] or q in p["address"]]
    return {"places": places[:10], "source": "sample"}


@app.get("/api/reverse")
def reverse(lat: float = Query(..., ge=33, le=39), lng: float = Query(..., ge=124, le=132)):
    """지도에서 찍은 좌표 → 건물명·주소. 카카오 → 오픈스트리트맵 → 좌표만 순으로 시도해요."""
    order = (("kakao",) if os.getenv("KAKAO_REST_KEY") else ()) + (("mapbox",) if os.getenv("MAPBOX_TOKEN") else ()) + ("osm",)
    for mod in order:
        try:
            m = __import__(f"collect.{mod}", fromlist=["reverse"])
            found = m.reverse(lat, lng)
            if found:
                if not found["name"]:
                    found["name"] = "지도에서 고른 위치"
                return {**found, "source": mod}
        except Exception:
            continue
    return {"name": "지도에서 고른 위치", "address": f"{lat:.5f}, {lng:.5f}", "lat": lat, "lng": lng, "source": "coords"}


@app.post("/api/plan", response_model=PlanResult)
def plan(inp: PlanInput, repo: Repo = Depends(get_repo)):
    products, eff = repo.loan_products()
    out = make_plan(inp.model_dump(), repo.regions(), products, eff)
    meta = repo.regions_meta()
    out["price_source"] = {k: meta.get(k) for k in ("source", "period", "collected", "sample", "note")}
    return out


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
    result: Optional[dict] = None


@app.post("/api/plans")
def save_plan(body: SaveIn, repo: Repo = Depends(get_repo)):
    return {"id": repo.save_plan(body.model_dump())}


@app.get("/api/plans/{pid}")
def get_plan(pid: str, repo: Repo = Depends(get_repo)):
    p = repo.get_plan(pid)
    if not p:
        raise HTTPException(404, "플랜을 찾을 수 없어요")
    return p
