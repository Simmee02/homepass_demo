import type { Place, PlanResult, Option } from './types';

const BASE = import.meta.env.VITE_API_BASE ?? '';

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, { headers: { 'Content-Type': 'application/json' }, ...init });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(`요청 실패 (${res.status})${body?.message ? ` · ${body.message}` : ''}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  companies: (q: string) => req<{ places: Place[] }>(`/api/companies?q=${encodeURIComponent(q)}`),
  reverse: (lat: number, lng: number) => req<Place>(`/api/reverse?lat=${lat}&lng=${lng}`),
  plan: (body: unknown) => req<PlanResult>('/api/plan', { method: 'POST', body: JSON.stringify(body) }),
  explain: (region: string, option: Option) =>
    req<{ text: string; source: 'llm' | 'template' }>('/api/explain', { method: 'POST', body: JSON.stringify({ region, option }) }),
  save: (input: unknown, result: unknown) =>
    req<{ id: string }>('/api/plans', { method: 'POST', body: JSON.stringify({ input, result }) }),
};
