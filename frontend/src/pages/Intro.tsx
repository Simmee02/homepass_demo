import { useNavigate } from 'react-router-dom';
import { Mascot } from '../components/ui';

export default function Intro() {
  const nav = useNavigate();
  return (
    <div className="app" style={{ background: 'var(--main)', color: '#fff' }}>
      <div style={{ padding: '72px 28px 0', flex: 1, display: 'flex', flexDirection: 'column' }}>
        <h1 style={{ margin: 0, fontSize: 28, lineHeight: 1.35, fontWeight: 800, letterSpacing: -0.8 }}>우리 집,<br />어디까지 갈 수 있을까?</h1>
        <span style={{ alignSelf: 'flex-start', marginTop: 14, background: 'rgba(255,255,255,.18)', borderRadius: 999, padding: '6px 12px', fontSize: 13 }}>약 2분 · 3단계 질문</span>
        <div style={{ display: 'flex', justifyContent: 'center', margin: '48px 0 32px' }}><Mascot pose="hello" size={200} /></div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ background: 'rgba(255,255,255,.16)', borderRadius: 8, padding: '12px 14px', fontSize: 14 }}>안녕하세요, 홈패스예요!</div>
          <div style={{ background: 'rgba(255,255,255,.16)', borderRadius: 8, padding: '12px 14px', fontSize: 14, lineHeight: 1.5 }}>두 분이 모은 돈으로 갈 수 있는 집을 같이 찾아볼게요.</div>
        </div>
      </div>
      <div className="cta"><button className="btn" style={{ background: '#fff', color: 'var(--main-text)' }} onClick={() => nav('/when')}>시작하기</button></div>
    </div>
  );
}
