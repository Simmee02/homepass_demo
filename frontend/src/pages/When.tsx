import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Cta, StepHeader } from '../components/ui';
import { useStore } from '../store';
import type { Marriage } from '../types';

const MARRIAGE: { id: Marriage; label: string; note: string }[] = [
  { id: 'soon', label: '3개월 안', note: '입주 전 혼인신고 → 신혼부부 대출 기준이 적용돼요' },
  { id: 'year', label: '1년 안', note: '입주 시점과 비교해 신혼부부 기준 적용 여부를 알려드려요' },
  { id: 'undecided', label: '미정', note: '혼인신고 전·후 두 경우를 나눠서 보여드려요' },
  { id: 'done', label: '했어요', note: '혼인 7년 이내면 신혼부부 기준이 적용돼요' },
];

export default function When() {
  const nav = useNavigate();
  const { marriage, moveIn, set } = useStore();
  const today = new Date();
  const nowY = today.getFullYear();
  const nowM = today.getMonth() + 1;
  const [view, setView] = useState(moveIn.year);
  const note = MARRIAGE.find((m) => m.id === marriage)!.note;

  return (
    <div className="app">
      <StepHeader step={1} name="언제" title={'두 분 일정을\n알려주세요.'} pose="detective" progress={33} bubble="입주 시점까지 남은 기간이 모을 수 있는 돈을 정해요!" />
      <main className="body">
        <section className="q">
          <h2>혼인신고는 언제쯤 하세요?</h2>
          <div className="chips" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
            {MARRIAGE.map((m) => (
              <button key={m.id} className={`chip ${marriage === m.id ? 'on' : ''}`} onClick={() => set({ marriage: m.id })}>{m.label}</button>
            ))}
          </div>
          <span className="hint">{note}</span>
        </section>
        <section className="q">
          <h2>언제부터 함께 살고 싶으세요?</h2>
          <div className="picker">
            <div className="head">
              <button className="icon-btn" style={{ width: 32, height: 32, opacity: view > nowY ? 1 : 0.25 }} aria-label="이전 해" disabled={view <= nowY} onClick={() => setView(view - 1)}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M14 7l-5 5 5 5" stroke="#1E2230" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </button>
              <strong>{view}년</strong>
              <button className="icon-btn" style={{ width: 32, height: 32 }} aria-label="다음 해" disabled={view >= nowY + 4} onClick={() => setView(view + 1)}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M10 7l5 5-5 5" stroke="#1E2230" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </button>
            </div>
            <div className="grid">
              {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => {
                const past = view < nowY || (view === nowY && m <= nowM);
                const on = moveIn.year === view && moveIn.month === m;
                return <button key={m} className={on ? 'on' : ''} disabled={past} onClick={() => set({ moveIn: { year: view, month: m } })}>{m}월</button>;
              })}
            </div>
          </div>
        </section>
      </main>
      <div className="spacer" />
      <Cta onClick={() => nav('/where')}>다음</Cta>
    </div>
  );
}
