# 홈패스 (HomePass)

예비부부가 **동네 → 집값 → 자금 마련(대출 + 모은 돈 + 더 모을 돈)** 순서로 주거 예산을 함께 세우는 서비스.

> 원칙: 숫자는 규칙표로 계산하고, AI는 설명만 해요. 상품 추천·시세 예측·투자 조언은 하지 않아요.

## 구조

```
homepass_demo/
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
| `ODSAY_API_KEY` | 대중교통 통근 시간 | 직선거리 추정 (8분 + 2.3분/km) |

Supabase 연결: 대시보드 SQL Editor에서 `supabase/schema.sql` 실행 → `python supabase/seed.py`.

## 아직 할 일

- [ ] 대출 규칙표 수치를 주택도시기금·HF 공식 자료로 검증 (`verified: false`)
- [ ] 시세: 국토부 실거래가 API 월간 배치 → `regions` 테이블
- [ ] 회사 검색·통근: 카카오 로컬, ODsay 실제 호출 + `commute_cache`
- [ ] 지도: 카카오맵 SDK로 교체 (지금은 단순 투영 그림)
- [ ] 공유 코드로 배우자가 같은 플랜 열기 화면
