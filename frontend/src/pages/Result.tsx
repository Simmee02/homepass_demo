import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { BackIcon, Chevron, Mascot } from '../components/ui';
import { GRADE_CLASS, TENURE_LABEL, won } from '../format';
import { useStore } from '../store';
import type { Tenure } from '../types';

const ROW_COLOR = { loan: 'var(--main)', saved: 'var(--teal)', gap: 'var(--yellow)' } as const;

export default function Result() {
  const nav = useNavigate();
  const s = useStore();
  const { result, regionId, tenure, people, moveIn, set } = s;
  const [error, setError] = useState('');
  const [explain, setExplain] = useState<{ text: string; source: string } | null>(null);
  const [explaining, setExplaining] = useState(false);

  useEffect(() => {
    if (result) return;
    setError('');
    api.plan(s.planInput())
      .then((r) => set({ result: r, regionId: r.regions[0]?.id ?? null, split: null }))
      .catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result]);
  useEffect(() => { setExplain(null); }, [regionId, tenure]);

  if (error) return <div className="app"><div className="loading">결과를 불러오지 못했어요. 서버가 켜져 있는지 확인해 주세요.<p className="error">{error}</p></div></div>;
  if (!result) return <div className="app"><div className="loading"><Mascot pose="detective" size={120} /><p>두 분 조건으로 계산하고 있어요…</p></div></div>;

  const region = result.regions.find((r) => r.id === regionId) ?? result.regions[0];
  const summary = [
    `${moveIn.year}.${moveIn.month} 입주 · ${result.months}개월`,
    `합산 ${won(result.combined_income)}`,
    `모은 돈 ${won(s.saved)}`,
    `통근 A ${people[0].maxCommute}분 · B ${people[1].maxCommute}분`,
  ];

  const header = (
    <header className="top" style={{ paddingBottom: 22 }}>
      <div className="nav" style={{ justifyContent: 'space-between', marginRight: -10 }}>
        <button className="icon-btn" aria-label="이전" onClick={() => nav('/money')}><BackIcon /></button>
        <span style={{ fontSize: 12, opacity: 0.85 }}>{result.rules_effective_date.slice(0, 7).replace('-', '.')} 기준 · 예시 시세</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <Mascot pose="party" size={64} />
        <h1 style={{ fontSize: 21, margin: 0 }}>{region ? `두 분 통근 범위에서\n동네 ${result.regions.length}곳을 찾았어요` : '통근 범위가 겹치는\n동네를 못 찾았어요'}</h1>
      </div>
      <div className="summary">{summary.map((t) => <span key={t}>{t}</span>)}</div>
    </header>
  );

  if (!region) {
    return (
      <div className="app gray">{header}
        <div className="sec"><p className="desc" style={{ margin: 0 }}>두 분 중 한 분의 최대 통근 시간을 늘리면 겹치는 동네가 생길 수 있어요.</p>
          <button className="btn ghost" onClick={() => nav('/where')}>통근 시간 바꾸기</button></div>
      </div>
    );
  }

  const opt = region.options[tenure];
  const failed = opt.loans.filter((l) => l.status === 'no');
  const others = (['jeonse', 'monthly', 'buy'] as Tenure[]).filter((t) => t !== tenure);

  return (
    <div className="app gray">
      {header}

      <section className="sec">
        <h2>어느 동네부터 볼까요?</h2>
        <div className="regions">
          {result.regions.map((r) => (
            <button key={r.id} className={`region ${r.id === region.id ? 'on' : ''}`} onClick={() => set({ regionId: r.id })}>
              <b style={{ color: r.id === region.id ? 'var(--ink)' : 'var(--sub)' }}>{r.name}</b>
              <span>A {r.commute.A}분 · B {r.commute.B}분</span>
            </button>
          ))}
        </div>
      </section>

      <section className="sec" style={{ paddingTop: 24 }}>
        <h2>{region.name}에 살려면</h2>
        <div className="seg" style={{ background: '#E9ECF2' }}>
          {(['jeonse', 'monthly', 'buy'] as Tenure[]).map((t) => (
            <button key={t} className={tenure === t ? 'on' : ''} style={{ height: 34 }} onClick={() => set({ tenure: t })}>{TENURE_LABEL[t]}</button>
          ))}
        </div>
        <div className="fund">
          <div className="price-row">
            <div><small>{tenure === 'monthly' ? '아파트 월세 시세' : `아파트 ${TENURE_LABEL[tenure]} 시세`}</small><strong>{tenure === 'monthly' ? opt.price_label : `약 ${won(opt.price)}`}</strong></div>
            <span className={`pill ${GRADE_CLASS[opt.grade]}`}>{opt.grade}</span>
          </div>
          <div className="bar">
            {opt.rows.map((r) => <div key={r.kind} style={{ width: `${(r.amount / Math.max(opt.price, 1)) * 100}%`, background: ROW_COLOR[r.kind] }} />)}
          </div>
          <h3>이렇게 마련할 수 있어요</h3>
          {opt.rows.map((r) => {
            const inner = (<>
              <span className="dot" style={{ background: ROW_COLOR[r.kind] }} />
              <span className="info"><small>{r.label}</small><b>{r.name}</b><span>{r.sub}</span></span>
              <span className="val" style={r.kind === 'gap' ? { color: 'var(--mid)' } : undefined}>{won(r.amount)}</span>
            </>);
            return r.product_id
              ? <button key={r.kind} className="frow" onClick={() => nav(`/loan/${r.product_id}`)}>{inner}<Chevron /></button>
              : <div key={r.kind} className="frow">{inner}</div>;
          })}
          {failed.map((l) => <div key={l.product_id} className="note">{l.name}({l.rate_label})은 {l.reason.replace(' · ', ', ')}라 안 돼요</div>)}
          <div className={`tip ${opt.grade === '빠듯' ? 'warn' : 'good'}`}>{opt.tip}</div>
          {opt.need_total > 0 && (
            <button className="btn ghost" style={{ marginTop: 12 }} onClick={() => nav('/split')}>월 {opt.need_monthly.toLocaleString('ko-KR')}만, 둘이 어떻게 나눌지 보기</button>
          )}
        </div>
        {explain ? (
          <div className="explain">{explain.text}<small>{explain.source === 'llm' ? 'AI가 계산 결과를 설명했어요 · 숫자는 기준표로 계산해요' : '기본 설명이에요 · AI 키를 연결하면 더 자연스럽게 설명해요'}</small></div>
        ) : (
          <button className="btn ghost" disabled={explaining} onClick={() => { setExplaining(true); api.explain(region.name, opt).then(setExplain).finally(() => setExplaining(false)); }}>
            {explaining ? '설명을 만드는 중…' : '이 결과, 쉽게 설명 듣기'}
          </button>
        )}
      </section>

      <section className="sec" style={{ paddingTop: 24 }}>
        <h2 style={{ fontSize: 15 }}>같은 동네, 다른 방법</h2>
        <div className="list">
          {others.map((t) => {
            const o = region.options[t];
            const loan = o.rows.find((r) => r.kind === 'loan');
            const sub = t === 'monthly' ? o.tip : loan ? `${loan.name} ${won(loan.amount)}${o.need_total ? ` · ${won(o.need_total)} 부족` : ''}` : o.tip;
            return (
              <button key={t} className="item" onClick={() => set({ tenure: t })}>
                <span className="tag">{TENURE_LABEL[t]}</span>
                <span className="info"><b>{t === 'monthly' ? o.price_label : `아파트 약 ${won(o.price)}`}</b><span>{sub}</span></span>
                <span className={`pill ${GRADE_CLASS[o.grade]}`}>{o.grade}</span><Chevron />
              </button>
            );
          })}
        </div>
      </section>

      <section className="sec" style={{ gap: 16, paddingBottom: 8 }}>
        <div className="lock">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none" aria-hidden="true"><circle cx="20" cy="20" r="18" fill="#E6E8EE" /><rect x="13" y="19" width="14" height="10" rx="2.5" stroke="#5B6170" strokeWidth="2" /><path d="M16 19v-3a4 4 0 0 1 8 0v3" stroke="#5B6170" strokeWidth="2" /></svg>
          <div style={{ flex: 1 }}><b style={{ fontSize: 14, color: 'var(--no)' }}>신혼 특별공급 · 신생아 특례</b><div style={{ fontSize: 13, color: 'var(--sub)' }}>청약통장·출산 계획을 넣으면 열려요</div></div>
          <span className="tag" style={{ background: 'var(--bg)', color: 'var(--mute)' }}>준비 중</span>
        </div>
        <p className="disclaimer">{result.notes.join(' ')} 금액은 기준표로 계산하고, AI는 설명만 해요.</p>
      </section>
      <div className="cta"><button className="btn" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>다른 동네도 보기</button></div>
    </div>
  );
}
