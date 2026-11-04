-- 홈패스 Supabase 스키마. Supabase 대시보드 > SQL Editor에 붙여 넣고 실행하세요.
-- 금액 단위: 만원

-- 대출 규칙표: 규정이 바뀌면 새 행을 넣고 이전 행은 active=false로 돌려요.
create table if not exists loan_products (
  id text not null,
  effective_date date not null,
  active boolean not null default true,
  rule jsonb not null,            -- backend/app/data/loan_products.json 의 product 객체 그대로
  source_url text,
  verified boolean not null default false,
  created_at timestamptz not null default now(),
  primary key (id, effective_date)
);

-- 동네별 시세 (국토부 실거래가 월간 배치로 갱신)
create table if not exists regions (
  id text primary key,
  name text not null,
  lat double precision not null,
  lng double precision not null,
  capital boolean not null default true,
  jeonse integer not null,          -- 아파트 전세 중앙값
  buy integer not null,             -- 아파트 매매 중앙값
  monthly_deposit integer not null, -- 월세 보증금 중앙값
  monthly_rent integer not null,    -- 월세 중앙값
  sample boolean not null default true,
  updated_at timestamptz not null default now()
);

-- 통근 시간 캐시 (ODsay 호출 줄이기)
create table if not exists commute_cache (
  region_id text references regions(id) on delete cascade,
  dest_key text not null,           -- 회사 좌표를 소수 3자리로 반올림한 키 "37.402,127.108"
  minutes integer not null,
  provider text not null default 'estimate',
  updated_at timestamptz not null default now(),
  primary key (region_id, dest_key)
);

-- 두 사람이 함께 보는 플랜 (공유 링크)
create table if not exists plans (
  id text primary key,
  input jsonb not null,
  result jsonb,
  created_at timestamptz not null default now()
);

-- 서버(service key)만 쓰도록 RLS를 켜고, 공개 정책은 만들지 않아요.
alter table loan_products enable row level security;
alter table regions enable row level security;
alter table commute_cache enable row level security;
alter table plans enable row level security;
