import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Cta, StepHeader } from '../components/ui';
import { won } from '../format';
import { useStore } from '../store';

type Key = 'A' | 'B' | 'saved' | 'loan';

function MoneyField({ label, value, on, onFocus, onChange }: { label: string; value: number; on: boolean; onFocus: () => void; onChange: (v: number) => void }) {
  return (
    <div className={`field ${on ? 'on' : ''}`} onClick={onFocus}>
      <label>{label}</label>
      <input inputMode="numeric" aria-label={`${label} (만원)`} value={value ? value.toLocaleString('ko-KR') : ''} placeholder="0"
        onFocus={onFocus} onChange={(e) => onChange(Number(e.target.value.replace(/[^0-9]/g, '')) || 0)} />
      <span className="unit">만원</span>
    </div>
  );
}

export default function Money() {
  const nav = useNavigate();
  const { people, saved, hasLoan, loanMonthly, set, setPerson } = useStore();
  const [focus, setFocus] = useState<Key>('A');
  const sum = people[0].income + people[1].income;
  const get = (k: Key) => (k === 'A' ? people[0].income : k === 'B' ? people[1].income : k === 'saved' ? saved : loanMonthly);
  const put = (k: Key, v: number) => {
    if (k === 'A') setPerson(0, { income: v });
    else if (k === 'B') setPerson(1, { income: v });
    else if (k === 'saved') set({ saved: v, result: null });
    else set({ loanMonthly: v, result: null });
  };
  const ready = people.every((p) => p.income > 0) && (!hasLoan || loanMonthly > 0);

  return (
    <div className="app">
      <StepHeader step={3} name="얼마" title={'예산을 함께\n가늠해볼게요.'} pose="coin" progress={100} bubble="입력한 금액은 대출 계산에만 쓰여요!" />
      <main className="body">
        <section className="q">
          <div className="q-head"><h2>두 분의 연소득은요? <span className="hint" style={{ fontWeight: 400 }}>세전</span></h2>
            {sum > 0 && <span className="hint">합산 <b style={{ color: 'var(--teal-text)' }}>{won(sum)}</b></span>}</div>
          <span className="reason">받을 수 있는 대출과 한도를 계산할 때 필요해요</span>
          <MoneyField label={people[0].label} value={people[0].income} on={focus === 'A'} onFocus={() => setFocus('A')} onChange={(v) => put('A', v)} />
          <MoneyField label={people[1].label} value={people[1].income} on={focus === 'B'} onFocus={() => setFocus('B')} onChange={(v) => put('B', v)} />
        </section>
        <section className="q">
          <h2>주거 자금으로 모아둔 돈은요?</h2>
          <MoneyField label="주거 자금" value={saved} on={focus === 'saved'} onFocus={() => setFocus('saved')} onChange={(v) => put('saved', v)} />
          <div className="quick">
            {[100, 500, 1000].map((v) => <button key={v} onClick={() => put(focus, get(focus) + v)}>+{v.toLocaleString('ko-KR')}</button>)}
            <button onClick={() => put(focus, 0)}>지우기</button>
          </div>
        </section>
        <section className="q">
          <h2>갚고 있는 대출이 있나요?</h2>
          <div className="chips" style={{ gridTemplateColumns: '1fr 1fr' }}>
            <button className={`chip ${!hasLoan ? 'on' : ''}`} style={{ height: 40 }} onClick={() => set({ hasLoan: false, result: null })}>없어요</button>
            <button className={`chip ${hasLoan ? 'on' : ''}`} style={{ height: 40 }} onClick={() => { set({ hasLoan: true, result: null }); setFocus('loan'); }}>있어요</button>
          </div>
          {hasLoan && <>
            <MoneyField label="두 분 월 상환액" value={loanMonthly} on={focus === 'loan'} onFocus={() => setFocus('loan')} onChange={(v) => put('loan', v)} />
            <span className="reason">대략 합쳐서 적어도 돼요. 한도 계산(DSR)에서 빼고 계산해요.</span>
          </>}
        </section>
      </main>
      <div className="spacer" />
      <Cta onClick={() => { set({ result: null }); nav('/result'); }} disabled={!ready}>결과 보기</Cta>
    </div>
  );
}
