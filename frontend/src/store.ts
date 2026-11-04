import { create } from 'zustand';
import type { Marriage, Place, PlanResult, Tenure } from './types';

export interface PersonState { label: string; color: string; tint: string; text: string; company: Place | null; maxCommute: number; income: number }

interface State {
  marriage: Marriage;
  moveIn: { year: number; month: number };
  people: [PersonState, PersonState];
  saved: number;
  hasLoan: boolean;
  loanMonthly: number;
  result: PlanResult | null;
  regionId: string | null;
  tenure: Tenure;
  split: { A: number; B: number } | null;
  set: (p: Partial<State>) => void;
  setPerson: (i: 0 | 1, p: Partial<PersonState>) => void;
  planInput: () => unknown;
}

const now = new Date();

export const useStore = create<State>((set, get) => ({
  marriage: 'soon',
  moveIn: { year: now.getFullYear() + 1, month: 9 },
  people: [
    { label: '유저 A', color: '#2A8C97', tint: '#DDF2F4', text: '#1F6F78', company: null, maxCommute: 45, income: 0 },
    { label: '유저 B', color: '#6874FD', tint: '#ECEEFF', text: '#3B46C4', company: null, maxCommute: 60, income: 0 },
  ],
  saved: 0,
  hasLoan: false,
  loanMonthly: 0,
  result: null,
  regionId: null,
  tenure: 'jeonse',
  split: null,
  set: (p) => set(p),
  setPerson: (i, p) => set((s) => {
    const people = [...s.people] as [PersonState, PersonState];
    people[i] = { ...people[i], ...p };
    return { people, result: null };
  }),
  planInput: () => {
    const s = get();
    return {
      marriage: s.marriage,
      move_in: `${s.moveIn.year}-${String(s.moveIn.month).padStart(2, '0')}`,
      people: s.people.map((p, i) => ({ label: i === 0 ? 'A' : 'B', company: p.company, max_commute: p.maxCommute, income: p.income })),
      saved: s.saved,
      existing_loan_monthly: s.hasLoan ? s.loanMonthly : 0,
    };
  },
}));
