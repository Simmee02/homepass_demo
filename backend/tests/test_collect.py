from datetime import date

from app.engine.commute import candidate_regions
from collect.prices import aggregate, fill_missing, parse_items, recent_months
from collect.sigungu import short_name

TRADE_NEW = """<?xml version="1.0" encoding="UTF-8"?><response><header><resultCode>000</resultCode><resultMsg>OK</resultMsg></header>
<body><items>
<item><umdNm>신흥동</umdNm><excluUseAr>59.9</excluUseAr><dealAmount>55,000</dealAmount><cdealType> </cdealType></item>
<item><umdNm>신흥동</umdNm><excluUseAr>84.9</excluUseAr><dealAmount>61,000</dealAmount><cdealType></cdealType></item>
<item><umdNm>신흥동</umdNm><excluUseAr>84.9</excluUseAr><dealAmount>58,000</dealAmount><cdealType></cdealType></item>
<item><umdNm>신흥동</umdNm><excluUseAr>84.9</excluUseAr><dealAmount>99,000</dealAmount><cdealType>O</cdealType></item>
<item><umdNm>신흥동</umdNm><excluUseAr>120</excluUseAr><dealAmount>120,000</dealAmount><cdealType></cdealType></item>
<item><umdNm>태평동</umdNm><excluUseAr>59</excluUseAr><dealAmount>45,000</dealAmount><cdealType></cdealType></item>
</items><numOfRows>1000</numOfRows><pageNo>1</pageNo><totalCount>6</totalCount></body></response>"""

RENT_OLD = """<response><header><resultCode>00</resultCode></header><body><items>
<item><법정동>신흥동</법정동><전용면적>59</전용면적><보증금액>30,000</보증금액><월세금액>0</월세금액></item>
<item><법정동>신흥동</법정동><전용면적>59</전용면적><보증금액>28,000</보증금액><월세금액>0</월세금액></item>
<item><법정동>신흥동</법정동><전용면적>84</전용면적><보증금액>32,000</보증금액><월세금액>0</월세금액></item>
<item><법정동>신흥동</법정동><전용면적>59</전용면적><보증금액>5,000</보증금액><월세금액>110</월세금액></item>
<item><법정동>신흥동</법정동><전용면적>59</전용면적><보증금액>3,000</보증금액><월세금액>120</월세금액></item>
<item><법정동>신흥동</법정동><전용면적>59</전용면적><보증금액>4,000</보증금액><월세금액>130</월세금액></item>
</items><totalCount>6</totalCount></body></response>"""


def test_parse_both_formats_and_aggregate():
    t, nt = parse_items(TRADE_NEW)
    r, nr = parse_items(RENT_OLD)
    assert nt == 6 and nr == 6
    agg = aggregate(t, r)
    s = agg["신흥동"]
    assert s["buy"] == 58000          # 해제 거래·120㎡ 제외 후 중앙값
    assert s["jeonse"] == 30000
    assert s["monthly_deposit"] == 4000 and s["monthly_rent"] == 120
    assert agg["태평동"]["buy"] is None  # 표본 3건 미만


def test_fill_missing_uses_sigungu_median():
    t, _ = parse_items(TRADE_NEW)
    r, _ = parse_items(RENT_OLD)
    filled = fill_missing(aggregate(t, r, min_n=1))
    assert filled["태평동"]["jeonse"] == 30000 and "jeonse" in filled["태평동"]["filled"]


def test_api_error_raises():
    bad = "<OpenAPI_ServiceResponse><cmmMsgHeader><returnAuthMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</returnAuthMsg><returnReasonCode>30</returnReasonCode></cmmMsgHeader></OpenAPI_ServiceResponse>"
    try:
        parse_items(bad)
        assert False
    except RuntimeError as e:
        assert "30" in str(e)


def test_recent_months_skips_current():
    assert recent_months(3, date(2026, 1, 15)) == ["202512", "202511", "202510"]


def test_short_name():
    assert short_name("경기", "성남시 수정구") == "성남 수정구"
    assert short_name("경기", "하남시") == "하남"
    assert short_name("서울", "강남구") == "강남구"


def test_precise_commute_overrides_estimate():
    regions = [{"id": "x", "name": "x", "lat": 37.45, "lng": 127.146}]
    people = [{"label": "A", "company": {"lat": 37.402, "lng": 127.108}, "max_commute": 30},
              {"label": "B", "company": {"lat": 37.4979, "lng": 127.0276}, "max_commute": 40}]
    out = candidate_regions(regions, people, precise=lambda *a: 25)
    assert out and out[0]["commute"] == {"A": 25, "B": 25} and out[0]["commute_provider"] == "odsay"
    assert candidate_regions(regions, people, precise=lambda *a: 90) == []


CSV_TRADE = '''□ 본 서비스에서 제공하는 정보는 참고용이에요
□ 검색조건: 2026.04~2026.09
"NO","시군구","번지","본번","부번","단지명","전용면적(㎡)","계약년월","계약일","거래금액(만원)","동","층","매수자","매도자","건축년도","도로명","해제사유발생일","거래유형"
"1","경기도 성남시 수정구 신흥동","1","0001","0000","A아파트","59.9","202609","3","55,000","","5","개인","개인","2005","산성대로","-","중개거래"
"2","경기도 성남시 수정구 신흥동","1","0001","0000","A아파트","84.9","202608","3","61,000","","7","개인","개인","2005","산성대로","-","중개거래"
"3","경기도 성남시 수정구 신흥동","1","0001","0000","A아파트","84.9","202607","3","58,000","","7","개인","개인","2005","산성대로","-","중개거래"
"4","경기도 성남시 수정구 신흥동","1","0001","0000","A아파트","84.9","202607","9","99,000","","7","개인","개인","2005","산성대로","20260801","중개거래"
'''

CSV_RENT = '''"시군구","번지","본번","부번","단지명","전월세구분","전용면적(㎡)","계약년월","계약일","보증금(만원)","월세금(만원)","층"
"경기도 성남시 수정구 신흥동","1","0001","0000","A","전세","59","202609","1","30,000","0","3"
"경기도 성남시 수정구 신흥동","1","0001","0000","A","전세","59","202609","2","28,000","0","3"
"경기도 성남시 수정구 신흥동","1","0001","0000","A","전세","84","202609","3","32,000","0","3"
"경기도 성남시 수정구 신흥동","1","0001","0000","A","월세","59","202609","4","5,000","110","3"
"경기도 성남시 수정구 신흥동","1","0001","0000","A","월세","59","202609","5","3,000","120","3"
"경기도 성남시 수정구 신흥동","1","0001","0000","A","월세","59","202609","6","4,000","130","3"
'''


def test_prices_csv_build(tmp_path, monkeypatch):
    from collect import prices_csv, store
    (tmp_path / "아파트(매매)_실거래가_202604_202609.csv").write_bytes(CSV_TRADE.encode("cp949"))
    (tmp_path / "아파트(전월세)_실거래가.csv").write_text(CSV_RENT, encoding="utf-8-sig")
    monkeypatch.setattr(store, "GEO_CACHE", tmp_path / "geo.json")
    monkeypatch.setattr(store.Geocoder, "__call__", lambda self, q: (37.45, 127.146))
    regions, meta = prices_csv.build(sorted(tmp_path.glob("*.csv")))
    assert len(regions) == 1
    r = regions[0]
    assert r["name"] == "성남 수정구 신흥동"
    assert r["buy"] == 58000 and r["jeonse"] == 30000
    assert r["monthly"] == {"deposit": 4000, "rent": 120}
    assert meta["period"] == "202604~202609"


def test_companies_falls_back_to_osm_then_sample(monkeypatch):
    from fastapi.testclient import TestClient
    from collect import osm
    from app.main import app
    c = TestClient(app)
    monkeypatch.setattr(osm, "search", lambda q: [{"name": "네이버 1784", "address": "경기 성남시 분당구 정자일로 95", "lat": 37.359, "lng": 127.105}])
    r = c.get("/api/companies", params={"q": "네이버"}).json()
    assert r["source"] == "osm" and r["places"][0]["name"] == "네이버 1784"
    def boom(q):
        raise RuntimeError("offline")
    monkeypatch.setattr(osm, "search", boom)
    assert c.get("/api/companies", params={"q": "판교"}).json()["source"] == "sample"
