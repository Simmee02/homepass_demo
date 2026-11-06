"""로컬 JSON 시드를 Supabase에 올려요.

사용법:
  export SUPABASE_URL=https://xxxx.supabase.co
  export SUPABASE_SERVICE_KEY=...
  python supabase/seed.py                   # 대출 규칙표만 적재
  python supabase/seed.py --sample-regions  # 예시 시세 16곳도 적재 (실데이터 넣기 전 화면 확인용)
"""
import json
import os
import sys
from pathlib import Path

import httpx

ENV = Path(__file__).parents[1] / "backend" / ".env"
try:
    from dotenv import load_dotenv
    load_dotenv(ENV)
except ImportError:  # python-dotenv가 없는 파이썬으로 실행해도 .env를 읽어요
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_KEY"):
    sys.exit(f"{ENV} 에 SUPABASE_URL, SUPABASE_SERVICE_KEY 를 넣어 주세요")

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]
H = {"apikey": KEY, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"}
if not KEY.startswith("sb_"):  # 예전 service_role(JWT) 키
    H["Authorization"] = f"Bearer {KEY}"
DATA = Path(__file__).parents[1] / "backend" / "app" / "data"

lp = json.loads((DATA / "loan_products.json").read_text(encoding="utf-8"))
rows = [{"id": p["id"], "effective_date": lp["effective_date"], "active": True, "rule": p,
         "source_url": p["apply"]["url"], "verified": p.get("verified", False)} for p in lp["products"]]
httpx.post(f"{URL}/rest/v1/loan_products", headers=H, json=rows, timeout=20).raise_for_status()

print("loan_products:", len(rows), "개 적재")
if "--sample-regions" not in sys.argv:
    sys.exit(0)
rg = json.loads((DATA / "regions.json").read_text(encoding="utf-8"))
rows = [{"id": r["id"], "name": r["name"], "lat": r["lat"], "lng": r["lng"], "capital": r["capital"],
         "jeonse": r["jeonse"], "buy": r["buy"], "monthly_deposit": r["monthly"]["deposit"],
         "monthly_rent": r["monthly"]["rent"], "sample": True} for r in rg["regions"]]
httpx.post(f"{URL}/rest/v1/regions", headers=H, json=rows, timeout=20).raise_for_status()
print("regions(예시):", len(rows), "곳 적재")
