"""로컬 JSON 시드를 Supabase에 올려요.

사용법:
  export SUPABASE_URL=https://xxxx.supabase.co
  export SUPABASE_SERVICE_KEY=...
  python supabase/seed.py
"""
import json
import os
from pathlib import Path

import httpx

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
     "Prefer": "resolution=merge-duplicates"}
DATA = Path(__file__).parents[1] / "backend" / "app" / "data"

lp = json.loads((DATA / "loan_products.json").read_text(encoding="utf-8"))
rows = [{"id": p["id"], "effective_date": lp["effective_date"], "active": True, "rule": p,
         "source_url": p["apply"]["url"], "verified": p.get("verified", False)} for p in lp["products"]]
httpx.post(f"{URL}/rest/v1/loan_products", headers=H, json=rows, timeout=20).raise_for_status()

rg = json.loads((DATA / "regions.json").read_text(encoding="utf-8"))
rows = [{"id": r["id"], "name": r["name"], "lat": r["lat"], "lng": r["lng"], "capital": r["capital"],
         "jeonse": r["jeonse"], "buy": r["buy"], "monthly_deposit": r["monthly"]["deposit"],
         "monthly_rent": r["monthly"]["rent"], "sample": True} for r in rg["regions"]]
httpx.post(f"{URL}/rest/v1/regions", headers=H, json=rows, timeout=20).raise_for_status()
print("seed done:", len(lp["products"]), "products,", len(rows), "regions")
