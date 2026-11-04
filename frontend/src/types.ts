export type Marriage = 'soon' | 'year' | 'undecided' | 'done';
export type Tenure = 'jeonse' | 'monthly' | 'buy';
export type Grade = '여유' | '가능' | '빠듯';

export interface Place { name: string; address: string; lat: number; lng: number }

export interface Check { key: string; label: string; mine: string; standard: string; status: 'ok' | 'warn' | 'no' }

export interface LoanResult {
  product_id: string; name: string; org: string; tenure: Tenure;
  status: 'ok' | 'conditional' | 'no'; amount: number;
  limit_label: string; rate_label: string; checks: Check[]; reason: string;
  preferential: { label: string; value: number | string; applied: boolean | null }[];
  apply: { label: string; url: string; site: string };
}

export interface FundingRow { kind: 'loan' | 'saved' | 'gap'; label: string; name: string; sub: string; amount: number; product_id?: string | null }

export interface Option {
  tenure: Tenure; price_label: string; price: number; grade: Grade; rows: FundingRow[];
  need_total: number; need_monthly: number; surplus: number; tip: string; loans: LoanResult[]; rent?: number | null;
}

export interface RegionResult { id: string; name: string; lat: number; lng: number; commute: Record<string, number>; options: Record<Tenure, Option> }

export interface PlanResult {
  months: number; combined_income: number; monthly_saving: number; monthly_saving_estimated: boolean;
  regions: RegionResult[]; rules_effective_date: string; notes: string[];
}
