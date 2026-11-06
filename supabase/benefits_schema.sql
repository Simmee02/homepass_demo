-- 신혼부부 주거 혜택(정책대출 + 지자체 이자지원) 표. SQL Editor에서 실행한 뒤
-- Table Editor → housing_benefits → Import data from CSV → housing_benefits.csv
create table if not exists housing_benefits (
  id text primary key,
  name text not null,
  provider text not null,            -- 주택도시기금 / 한국주택금융공사 / 서울특별시 ...
  kind text not null,                -- policy_loan(정책대출) / guarantee(보증) / interest_support(이자지원)
  tenure text not null,              -- buy / jeonse
  region_scope text not null,        -- 전국 / 서울
  marital_condition text,            -- 신혼 인정 조건
  income_max integer,                -- 소득 상한 (만원)
  income_basis text,                 -- 부부합산 / 1인 기준 등
  net_asset_max integer,             -- 순자산 상한 (만원)
  price_or_deposit_max text,         -- 주택가격·보증금 상한
  limit_max text,                    -- 대출 한도
  rate_or_support text,              -- 금리 또는 이자 지원율
  extra_benefits text,               -- 우대금리·추가지원
  apply_url text,
  source_url text not null,
  checked_date date not null,
  verified boolean not null default false,
  note text
);
alter table housing_benefits enable row level security;
