/** 만원 단위 숫자 → '3.2억', '7,800만' */
export function won(v: number): string {
  v = Math.round(v);
  if (v >= 10000) {
    const eok = Math.floor(v / 10000);
    const man = v % 10000;
    if (man === 0) return `${eok}억`;
    if (man % 1000 === 0) return `${eok}.${man / 1000}억`;
    return `${eok}억 ${man.toLocaleString('ko-KR')}만`;
  }
  return `${v.toLocaleString('ko-KR')}만`;
}

export const TENURE_LABEL = { jeonse: '전세', monthly: '월세', buy: '매매' } as const;
export const GRADE_CLASS = { 여유: 'ok', 가능: 'mid', 빠듯: 'no' } as const;

export function addMonths(year: number, month: number, add: number) {
  const idx = year * 12 + (month - 1) + add;
  return { year: Math.floor(idx / 12), month: (idx % 12) + 1 };
}
