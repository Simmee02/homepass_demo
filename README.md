# 홈패스 (HomePass)

예비부부가 **동네 → 집값 → 자금 마련(대출 + 모은 돈 + 더 모을 돈)** 순서로 주거 예산을 함께 세우는 서비스.

> 원칙: 숫자는 규칙표로 계산하고, AI는 설명만 해요. 상품 추천·시세 예측·투자 조언은 하지 않아요.

## 구조

```
homepass/
├─ backend/                FastAPI
│  ├─ app/engine/          계산 엔진 (순수 함수, 화면과 무관하게 테스트)
│  │  ├─ commute.py        통근 시간 → 두 사람 범위가 겹치는 동네
│  │  ├─ loans.py          대출 자격·한도 판정 (규칙표 기반)
│  │  └─ plan.py           점유형태별 자금 마련 계획·여유/가능/빠듯
│  ├─ app/data/            시드 데이터 (대출 규칙표, 예시 시세, 예시 회사)
│  ├─ app/repo.py          Supabase 있으면 Supabase, 없으면 로컬 JSON
│  ├─ app/explain.py       Claude로 결과 설명 (키 없으면 기본 문장)
│  ├─ app/main.py          API
│  └─ tests/               pytest
├─ frontend/               React + Vite + TypeScript + Zustand
│  └─ src/pages/           인트로 · 언제 · 어디 · 얼마 · 결과 · 대출 상세 · 분담
└─ supabase/               schema.sql, seed.py
```

## 실행 (로컬)

키가 하나도 없어도 바로 돌아가요.

```bash
# 1) 백엔드
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000           # http://localhost:8000/docs

# 2) 프론트 (새 터미널)
cd frontend
npm install
npm run dev                                          # http://localhost:5173
```

테스트: `cd backend && pytest`

## API

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/health` | 상태, 저장소 종류 |
| GET | `/api/companies?q=` | 회사 검색 (운영: 카카오 로컬 API) |
| POST | `/api/plan` | 언제·어디·얼마 입력 → 후보 동네별 전세/월세/매매 자금 계획 |
| GET | `/api/loan-products` | 현재 대출 규칙표 |
| POST | `/api/explain` | 선택한 시나리오를 문장으로 설명 |
| POST/GET | `/api/plans`, `/api/plans/{id}` | 두 사람 공유용 플랜 저장·조회 |

## 외부 연동 (선택)

`backend/.env.example` 참고. 없으면 대체 로직으로 동작해요.

| 키 | 용도 | 없을 때 |
|---|---|---|
| `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | 규칙표·시세·플랜 저장 | 로컬 JSON·메모리 |
| `ANTHROPIC_API_KEY` | 결과 설명 | 규칙 기반 문장 |
| `KAKAO_REST_KEY` | 회사 검색 | 예시 업무지구 9곳 |
| `ODSAY_API_KEY` | 대중교통 통근 시간 | 직선거리 추정 (도보·대기 10분 + 직선 1km당 3분) |

Supabase 연결: 대시보드 SQL Editor에서 `supabase/schema.sql` 실행 → `python supabase/seed.py`.

## 실데이터 수집

### 0. 키 없이 바로 쓰는 실데이터

| 항목 | 방법 |
|---|---|
| 지도 | 오픈스트리트맵 타일 (키 불필요, 브라우저에서 바로 로드) |
| 회사 검색 | 오픈스트리트맵 Nominatim 검색 (키 불필요, 초당 1회 제한) |
| 시세 | 국토부 실거래가 공개시스템 CSV를 내려받아 가져오기 ↓ |

**실거래가 CSV 가져오기 (키 불필요)**

1. [rt.molit.go.kr](https://rt.molit.go.kr) → 조건별 자료제공 → 아파트(매매), 아파트(전월세) / 최근 6개월 / 지역 선택 → CSV 다운로드
2. 받은 파일을 `backend/raw/`에 넣고:

```bash
cd backend
python -m collect.prices_csv raw/*.csv              # → app/data/regions_real.json + supabase/regions.csv
python -m collect.prices_csv raw/*.csv --supabase   # Supabase regions 테이블에 바로 적재
```

Supabase에 키 없이 올리려면 대시보드 Table Editor → `regions` → Import data from CSV → `supabase/regions.csv`.
동네 좌표는 카카오 키가 없으면 오픈스트리트맵으로 붙이고 `geocode_cache.json`에 저장해요 (동 300곳이면 약 5분).

### 1. 키 발급 (자동 수집용, 모두 무료)

| 데이터 | 어디서 | 넣을 곳 |
|---|---|---|
| 아파트 매매·전월세 실거래가 | [data.go.kr](https://www.data.go.kr)에서 "국토교통부_아파트 매매 실거래가 자료", "국토교통부_아파트 전월세 실거래가 자료" 활용신청 → 마이페이지 **일반 인증키(Decoding)** | `MOLIT_SERVICE_KEY` |
| 좌표 변환·회사 검색 | [developers.kakao.com](https://developers.kakao.com) → 애플리케이션 추가 → **REST API 키** (카카오맵 사용 설정 ON) | `KAKAO_REST_KEY` |
| 대중교통 통근 시간 | [lab.odsay.com](https://lab.odsay.com) → 애플리케이션 등록(서버 IP 등록) → API 키 | `ODSAY_API_KEY` |

`backend/.env.example`을 `backend/.env`로 복사하고 키를 채운 뒤 확인:

```bash
cd backend
python -m collect.check_keys
```

### 2. 시세 수집

```bash
python -m collect.prices --months 6                # 수도권 48개 시군구, 전용 49~85㎡, 최근 6개월
python -m collect.prices --only 41131 41135 11650  # 일부만 빠르게
python -m collect.prices --supabase                # Supabase regions 테이블에도 반영
```

- 결과: `backend/app/data/regions_real.json` (법정동별 매매·전세·월세 중앙값, 거래 건수, 수집 기간)
- 표본 3건 미만인 값은 같은 시군구 중앙값으로 채우고 `filled_from_sigungu`에 표시해요.
- 파일이 생기면 API가 자동으로 실데이터를 쓰고, 결과 화면 상단 표시가 '예시 시세' → '실거래가 기간'으로 바뀌어요.
- 매달 한 번 다시 돌리면 돼요 (GitHub Actions cron 추천).

### 3. 대출 규칙표 출처

`backend/app/data/loan_products.json`의 각 상품에 `sources`(출처·확인일)와 `unverified_fields`가 있어요.

| 상품 | 확인한 곳 (2026-11-03) | 남은 확인 |
|---|---|---|
| 디딤돌 신혼 | [서울주거포털](https://housing.seoul.go.kr/site/main/content/sh01_070500) | 주택가격 상한, 우대금리 |
| 버팀목 신혼 | [경기주거복지포털](https://housing.gg.go.kr/html/24205.do) (소득·보증금 구간별 금리표 포함) | 상환능력 비율 |
| 보금자리론 | [경기주거복지포털](https://housing.gg.go.kr/html/24217.do), [한경비즈니스 2026.10.19 개선](https://magazine.hankyung.com/business/article/202609289898b) | LTV·DTI |
| HF 전세자금보증 | 공식 원문 미확인 | 한도·비율·금리 전부 |

## 아직 할 일

- [ ] HF 전세자금보증 한도·비율을 HF 공식 상품설명서로 확인
- [ ] 시세 수집 월간 자동화 (GitHub Actions)
- [ ] 통근 캐시를 Supabase `commute_cache`에 영구 저장
- [ ] 지도: 카카오맵 SDK로 교체 (지금은 단순 투영 그림)
- [ ] 공유 코드로 배우자가 같은 플랜 열기 화면
