import { Navigate, useNavigate, useParams } from 'react-router-dom';
import { BackIcon } from '../components/ui';
import { TENURE_LABEL } from '../format';
import { useStore } from '../store';

export default function LoanDetail() {
  const nav = useNavigate();
  const { productId } = useParams();
  const { result, regionId, tenure } = useStore();
  const region = result?.regions.find((r) => r.id === regionId);
  const loan = region?.options[tenure].loans.find((l) => l.product_id === productId);
  if (!region || !loan) return <Navigate to="/result" replace />;

  const ok = loan.status !== 'no';
  const warn = loan.checks.find((c) => c.status === 'warn');
  const markStyle = (st: string) => ({ background: st === 'ok' ? 'var(--ok-bg)' : st === 'warn' ? 'var(--mid-bg)' : 'var(--no-bg)', color: st === 'ok' ? 'var(--ok)' : st === 'warn' ? 'var(--mid)' : 'var(--no)' });

  return (
    <div className="app">
      <header className="top">
        <div className="nav"><button className="icon-btn" aria-label="이전" onClick={() => nav(-1)}><BackIcon /></button><span style={{ fontSize: 14, opacity: 0.85 }}>{region.name} · {TENURE_LABEL[tenure]}</span></div>
        <div style={{ display: 'flex', gap: 6 }}>
          {[TENURE_LABEL[loan.tenure], loan.org].map((t) => <span key={t} style={{ fontSize: 12, fontWeight: 700, background: 'rgba(255,255,255,.2)', borderRadius: 4, padding: '3px 8px' }}>{t}</span>)}
        </div>
        <h1 style={{ marginTop: 8 }}>{loan.name} 대출</h1>
        <span style={{ display: 'inline-flex', marginTop: 14, background: '#fff', color: ok ? 'var(--ok)' : 'var(--no)', borderRadius: 999, padding: '6px 12px', fontSize: 13, fontWeight: 700 }}>
          {loan.status === 'ok' ? '✓ 두 분은 받을 수 있어요' : loan.status === 'conditional' ? '! 조건을 채우면 받을 수 있어요' : '✕ 지금 조건으로는 어려워요'}
        </span>
        <div className="stats">
          <div><small>예상 대출액</small><b>{ok ? `${(loan.amount / 10000).toFixed(1)}억` : '-'}</b></div>
          <div><small>금리</small><b>{loan.rate_label}</b></div>
        </div>
      </header>
      <main className="body">
        <section className="q">
          <h2>두 분 조건 vs 대출 기준</h2>
          <span className="hint">입력하신 값으로 하나씩 확인했어요</span>
          <div className="table">
            {loan.checks.map((c) => (
              <div key={c.key} className="trow">
                <span className="mark" style={markStyle(c.status)}>{c.status === 'ok' ? '✓' : c.status === 'warn' ? '!' : '✕'}</span>
                <span className="l"><small>{c.label}</small><b>{c.mine}</b></span>
                <span className="r"><small>기준</small><span>{c.standard}</span></span>
              </div>
            ))}
          </div>
          {warn && <div className="note" style={{ background: 'var(--warn-bg)', fontSize: 13 }}><b style={{ color: 'var(--ink)' }}>신청 전에 혼인신고가 필요해요</b><br />혼인신고 전에는 일반 기준이 적용돼요. 입주 일정에 맞춰 신고하면 돼요.</div>}
        </section>
        {loan.preferential.length > 0 && (
          <section className="q">
            <h2>금리를 더 낮추려면</h2>
            <div className="table">
              {loan.preferential.map((p) => (
                <div key={p.label} className="trow">
                  <span className="l"><b style={{ fontWeight: 500 }}>{p.label}</b></span>
                  <b style={{ fontSize: 14, color: p.applied ? 'var(--teal-text)' : 'var(--ink)' }}>−{p.value}%p</b>
                  <span style={{ fontSize: 12, color: p.applied ? 'var(--sub)' : 'var(--main-text)', fontWeight: p.applied ? 400 : 700 }}>{p.applied === null ? '정보 넣기 ›' : p.applied ? '적용돼요' : '해당 없음'}</span>
                </div>
              ))}
            </div>
          </section>
        )}
        {loan.sources.length > 0 && <p className="disclaimer">기준 출처: {loan.sources.map((src, i) => <span key={src.url}>{i ? ' · ' : ''}<a href={src.url} target="_blank" rel="noreferrer">{src.title}</a> ({src.checked} 확인)</span>)}</p>}
        {!loan.verified && <p className="disclaimer" style={{ color: 'var(--mid)' }}>이 상품의 한도·금리는 아직 공식 원문으로 확인하지 못한 값이에요.</p>}
        <p className="disclaimer">공개 기준으로 계산한 예상치예요. 최종 한도·금리는 {loan.org}와 취급 은행 심사로 정해져요.</p>
      </main>
      <div className="spacer" />
      <div className="cta">
        <a className="btn" href={loan.apply.url} target="_blank" rel="noreferrer">{loan.apply.label} ↗</a>
        <p style={{ textAlign: 'center', fontSize: 11, color: 'var(--mute)', margin: '8px 0 0' }}>{loan.apply.site} 페이지로 이동해요 · 입력하신 값은 홈패스에 남아 있어요</p>
      </div>
    </div>
  );
}
