import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { Cta, StepHeader } from '../components/ui';
import { useStore, type PersonState } from '../store';
import type { Place } from '../types';

const MINUTES = [30, 45, 60, 90];
const label = (m: number) => (m === 90 ? '1.5시간' : m === 60 ? '1시간' : `${m}분`);

function CompanySearch({ onPick }: { onPick: (p: Place) => void }) {
  const [q, setQ] = useState('');
  const [list, setList] = useState<Place[]>([]);
  useEffect(() => {
    const t = setTimeout(() => { api.companies(q).then((r) => setList(r.places)).catch(() => setList([])); }, 200);
    return () => clearTimeout(t);
  }, [q]);
  return (
    <div className="search">
      <input autoFocus placeholder="회사 이름이나 주소로 검색" value={q} onChange={(e) => setQ(e.target.value)} />
      {list.slice(0, 4).map((p) => (
        <button key={p.name} className="result" onClick={() => onPick(p)}><b>{p.name}</b><span>{p.address}</span></button>
      ))}
    </div>
  );
}

function PersonCard({ p, i }: { p: PersonState; i: 0 | 1 }) {
  const setPerson = useStore((s) => s.setPerson);
  const [editing, setEditing] = useState(!p.company);
  return (
    <div className="card">
      {editing || !p.company ? (
        <>
          <div className="person-top"><span className="who" style={{ color: p.color }}>{p.label}</span><span className="name">회사를 검색해 주세요</span></div>
          <CompanySearch onPick={(c) => { setPerson(i, { company: c }); setEditing(false); }} />
        </>
      ) : (
        <div className="person-top">
          <div className="avatar" style={{ background: p.tint }}>
            <svg width="16" height="20" viewBox="0 0 24 30" fill="none"><path d="M12 0C5 0 0 5 0 11c0 8 12 19 12 19s12-11 12-19C24 5 19 0 12 0Z" fill={p.color} /><circle cx="12" cy="11" r="4" fill="#fff" /></svg>
          </div>
          <div className="info">
            <div><span className="who" style={{ color: p.color }}>{p.label}</span><span className="name">{p.company.name}</span></div>
            <div className="addr">{p.company.address}</div>
          </div>
          <button className="link-btn" onClick={() => setEditing(true)}>변경</button>
        </div>
      )}
      <div className="divider" />
      <div className="q" style={{ gap: 8 }}>
        <div className="q-head"><span style={{ fontSize: 13, color: 'var(--sub)', fontWeight: 500 }}>통근은 최대</span><span style={{ fontSize: 11, color: 'var(--mute)' }}>편도 기준</span></div>
        <div className="seg" role="radiogroup">
          {MINUTES.map((m) => (
            <button key={m} role="radio" aria-checked={p.maxCommute === m} className={p.maxCommute === m ? 'on' : ''}
              style={p.maxCommute === m ? { borderColor: p.color, color: p.text } : undefined}
              onClick={() => setPerson(i, { maxCommute: m })}>{label(m)}</button>
          ))}
        </div>
      </div>
    </div>
  );
}

/** 두 회사 좌표와 통근 범위를 단순 투영해서 그려요. 실제 서비스는 카카오맵 SDK로 바꿔요. */
function MapPreview({ people }: { people: PersonState[] }) {
  const pts = people.filter((p) => p.company);
  if (!pts.length) return null;
  const W = 342, H = 140, KM = 6.5; // 1km ≈ 6.5px
  const cLat = pts.reduce((a, p) => a + p.company!.lat, 0) / pts.length;
  const cLng = pts.reduce((a, p) => a + p.company!.lng, 0) / pts.length;
  const proj = (lat: number, lng: number) => ({ x: W / 2 + (lng - cLng) * 88.2 * KM, y: H / 2 - (lat - cLat) * 111 * KM });
  return (
    <div style={{ position: 'relative', height: H, borderRadius: 8, overflow: 'hidden', background: '#EEF1F5' }}>
      <svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid slice" aria-label="통근 범위 지도">
        <path d="M0 95c60-18 110-8 170 8s120 16 172-6" stroke="#CFE3F4" strokeWidth="12" fill="none" />
        <path d="M40 0 62 150M150 0l-14 150M250 0l24 150M0 45h342M0 128h342" stroke="#fff" strokeWidth="5" fill="none" />
        {pts.map((p) => {
          const { x, y } = proj(p.company!.lat, p.company!.lng);
          const r = Math.max(8, ((p.maxCommute - 8) / 2.3) * KM);
          return <circle key={p.label} cx={x} cy={y} r={r} fill={p.color} fillOpacity=".1" stroke={p.color} strokeWidth="1.5" strokeDasharray="4 4" />;
        })}
        {pts.map((p) => {
          const { x, y } = proj(p.company!.lat, p.company!.lng);
          return <g key={p.label + 'pin'} transform={`translate(${x - 12} ${y - 26})`}><path d="M12 0C5 0 0 5 0 11c0 8 12 19 12 19s12-11 12-19C24 5 19 0 12 0Z" fill={p.color} /><circle cx="12" cy="11" r="4" fill="#fff" /></g>;
        })}
      </svg>
      <span style={{ position: 'absolute', left: 10, bottom: 10, background: '#1E2230', color: '#fff', borderRadius: 8, padding: '6px 10px', fontSize: 12, fontWeight: 700 }}>두 원이 겹치는 곳이 후보 동네예요</span>
    </div>
  );
}

export default function Where() {
  const nav = useNavigate();
  const people = useStore((s) => s.people);
  const ready = people.every((p) => p.company);
  return (
    <div className="app">
      <StepHeader step={2} name="어디" title={'출퇴근 거리를\n알려주세요.'} pose="pin" progress={67} bubble="두 분 통근 범위가 겹치는 동네만 후보로 보여드려요!" />
      <main className="body" style={{ gap: 8 }}>
        <section className="q">
          <h2>회사와 통근 시간을 각자 알려주세요</h2>
        </section>
        <PersonCard p={people[0]} i={0} />
        <PersonCard p={people[1]} i={1} />
        <MapPreview people={people} />
      </main>
      <div className="spacer" />
      <Cta onClick={() => nav('/money')} disabled={!ready}>다음</Cta>
    </div>
  );
}
