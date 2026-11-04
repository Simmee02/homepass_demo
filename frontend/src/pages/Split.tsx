import { useEffect, useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { addMonths, TENURE_LABEL, won } from '../format';
import { useStore } from '../store';

export default function Split() {
  const nav = useNavigate();
  const s = useStore();
  const { result, regionId, tenure, people, moveIn, split, set } = s;
  const region = result?.regions.find((r) => r.id === regionId);
  const opt = region?.options[tenure];
  const [shareId, setShareId] = useState('');

  useEffect(() => {
    if (!opt || split) return;
    const total = opt.need_monthly;
    const shareA = people[0].income / Math.max(1, people[0].income + people[1].income);
    const A = Math.round((total * shareA) / 10) * 10;
    set({ split: { A, B: Math.max(0, total - A) } });
  }, [opt, split, people, set]);

  if (!region || !opt) return <Navigate to="/result" replace />;
  const cur = split ?? { A: 0, B: 0 };
  const total = cur.A + cur.B;
  const need = opt.need_total;
  const monthsNeeded = total > 0 ? Math.ceil(need / total) : Infinity;
  const today = new Date();
  const done = Number.isFinite(monthsNeeded) ? addMonths(today.getFullYear(), today.getMonth() + 1, monthsNeeded) : null;
  const target = moveIn.year * 12 + moveIn.month;
  const onTime = done ? done.year * 12 + done.month <= target : false;
  const pctA = total ? Math.round((cur.A / total) * 100) : 50;
  const step = (k: 'A' | 'B', d: number) => set({ split: { ...cur, [k]: Math.max(0, cur[k] + d) } });

  return (
    <div className="app">
      <header style={{ padding: '12px 24px 0' }}>
        <div style={{ height: 44, display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginLeft: -10 }}>
          <button className="icon-btn" aria-label="이전" onClick={() => nav(-1)}><svg width="22" height="22" viewBox="0 0 22 22" fill="none"><path d="M18 11H4m6-6-6 6 6 6" stroke="#1E2230" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg></button>
          <span style={{ fontSize: 12, color: 'var(--sub)' }}>{region.name} · {TENURE_LABEL[tenure]} 기준</span>
        </div>
        <h1 style={{ margin: '8px 0 4px', fontSize: 24, fontWeight: 800, letterSpacing: -0.6 }}>입주까지, 둘이 이렇게 모아요</h1>
        <p style={{ margin: 0, fontSize: 14, color: 'var(--sub)' }}>{need ? `부족한 ${won(need)}원, 두 분이 나눠서 채워요` : '지금 모은 돈으로 충분해요'}</p>
      </header>
      <main className="body">
        <div className="card" style={{ border: 0, background: 'var(--bg)', gap: 10 }}>
          <span style={{ fontSize: 13, color: 'var(--sub)' }}>다 모으는 달</span>
          <b style={{ fontSize: 30, letterSpacing: -0.8 }}>{done ? `${done.year}년 ${done.month}월` : '-'}</b>
          <span style={{ fontSize: 13, color: 'var(--sub)' }}>함께 월 {total.toLocaleString('ko-KR')}만원씩{Number.isFinite(monthsNeeded) ? `, ${monthsNeeded}개월` : ''}</span>
          <div className="ratio"><div style={{ width: `${pctA}%`, background: people[0].color }} /><div style={{ flex: 1, background: people[1].color }} /></div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--sub)' }}><span>{people[0].label} {pctA}%</span><span>{people[1].label} {100 - pctA}%</span></div>
        </div>
        {(['A', 'B'] as const).map((k, i) => (
          <div key={k} className="card">
            <div className="stepper">
              <div><div style={{ fontSize: 12, fontWeight: 700, color: people[i].color }}>{people[i].label}</div><b style={{ fontSize: 20 }}>월 {cur[k].toLocaleString('ko-KR')}만원</b></div>
              <div className="btns"><button aria-label={`${people[i].label} 10만원 줄이기`} onClick={() => step(k, -10)}>−</button><button aria-label={`${people[i].label} 10만원 늘리기`} onClick={() => step(k, 10)}>+</button></div>
            </div>
          </div>
        ))}
        <div className={`tip ${onTime ? 'good' : 'warn'}`} style={{ marginTop: 0 }}>
          {onTime ? `목표 입주(${moveIn.year}년 ${moveIn.month}월)에 맞춰 모을 수 있어요` : `목표 입주(${moveIn.year}년 ${moveIn.month}월)보다 늦어져요. 월 저축을 늘리거나 다른 동네를 보세요`}
        </div>
        <p className="disclaimer">수익률은 가정하지 않은 단순 저축 계산이에요. 시세가 바뀌면 다시 계산해 알려드려요.</p>
        {shareId && <p className="disclaimer">공유 코드: <b>{shareId}</b> (배우자에게 전달해 같이 볼 수 있어요)</p>}
      </main>
      <div className="spacer" />
      <div className="cta"><button className="btn" onClick={() => api.save(s.planInput(), { regionId, tenure, split: cur }).then((r) => setShareId(r.id))}>결과 공유하기</button></div>
    </div>
  );
}
