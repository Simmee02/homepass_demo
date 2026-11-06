import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { Cta, StepHeader } from '../components/ui';
import RealMap, { type MapCircle, type MapPin } from '../components/RealMap';
import { useStore, type PersonState } from '../store';
import type { Place } from '../types';

const MINUTES = [30, 45, 60, 90];
/** 서버(backend/app/engine/commute.py)와 같은 추정식: 도보·대기 10분 + 직선 1km당 3분 */
const reachKm = (min: number) => Math.max(0.5, (min - 10) / 3);
const label = (m: number) => (m === 90 ? '1.5시간' : m === 60 ? '1시간' : `${m}분`);

const RECENT_KEY = 'homepass-recent-places';
const readRecent = (): Place[] => {
  try { return JSON.parse(localStorage.getItem(RECENT_KEY) ?? '[]'); } catch { return []; }
};
const writeRecent = (list: Place[]) => {
  try { localStorage.setItem(RECENT_KEY, JSON.stringify(list.slice(0, 5))); } catch { /* 저장소를 못 쓰는 환경 */ }
};

function CompanySearch({ onPick }: { onPick: (p: Place) => void }) {
  const [q, setQ] = useState('');
  const [list, setList] = useState<Place[]>([]);
  const [loading, setLoading] = useState(false);
  const [recent, setRecent] = useState<Place[]>(readRecent);

  useEffect(() => {
    const query = q.trim();
    if (query.length < 2) { setList([]); setLoading(false); return; }
    setLoading(true);
    const t = setTimeout(() => {
      api.companies(query).then((r) => setList(r.places)).catch(() => setList([])).finally(() => setLoading(false));
    }, 350);
    return () => clearTimeout(t);
  }, [q]);

  const pick = (p: Place) => {
    const next = [p, ...recent.filter((r) => !(r.name === p.name && r.address === p.address))];
    writeRecent(next);
    setRecent(next.slice(0, 5));
    onPick(p);
  };
  const remove = (p: Place) => {
    const next = recent.filter((r) => r !== p);
    writeRecent(next);
    setRecent(next);
  };

  const [onMap, setOnMap] = useState(false);
  const [picked, setPicked] = useState<Place | null>(null);
  const [resolving, setResolving] = useState(false);
  const mapPins = useMemo<MapPin[]>(() => (picked ? [{ id: 'pick', lat: picked.lat, lng: picked.lng, color: '#1E2230', label: picked.name }] : []), [picked]);

  const query = q.trim();
  if (onMap) {
    return (
      <div className="search">
        <span className="hint">지도를 확대해서 회사 건물을 눌러 주세요</span>
        <RealMap height={240} pins={mapPins} onMapClick={(lat, lng) => {
          setResolving(true);
          setPicked({ name: '주소 찾는 중…', address: '', lat, lng });
          api.reverse(lat, lng).then(setPicked).catch(() => setPicked({ name: '지도에서 고른 위치', address: `${lat.toFixed(5)}, ${lng.toFixed(5)}`, lat, lng })).finally(() => setResolving(false));
        }} />
        {picked && <div className="result" style={{ cursor: 'default' }}><b>{picked.name}</b><span>{picked.address}</span></div>}
        <div style={{ display: 'flex', gap: 6 }}>
          <button className="btn ghost" style={{ flex: 1, background: 'var(--bg)', color: 'var(--sub)' }} onClick={() => { setOnMap(false); setPicked(null); }}>검색으로 돌아가기</button>
          <button className="btn ghost" style={{ flex: 1 }} disabled={!picked || resolving} onClick={() => picked && pick(picked)}>이 위치로 정하기</button>
        </div>
      </div>
    );
  }
  return (
    <div className="search">
      <input autoFocus placeholder="회사 이름이나 주소로 검색" value={q} onFocus={() => setRecent(readRecent())} onChange={(e) => setQ(e.target.value)} />
      {query.length >= 2 ? (
        <>
          {list.slice(0, 5).map((p) => (
            <button key={`${p.name}-${p.lat}`} className="result" onClick={() => pick(p)}><b>{p.name}{p.kind === 'area' && <em className="area-tag">동네</em>}</b><span>{p.address}</span></button>
          ))}
          {!loading && list.length === 0 && <span className="hint" style={{ padding: '4px 2px' }}>검색 결과가 없어요. 도로명 주소로 다시 검색하거나 지도에서 직접 골라 주세요.</span>}
          {loading && <span className="hint" style={{ padding: '4px 2px' }}>찾는 중…</span>}
        </>
      ) : null}
      <button className="link-btn" style={{ alignSelf: 'flex-start' }} onClick={() => setOnMap(true)}>찾는 회사가 없나요? 지도에서 직접 고르기 ›</button>
      {query.length < 2 && recent.length > 0 && (
        <div className="recent">
          <div className="recent-head"><span>최근 검색</span><button onClick={() => { writeRecent([]); setRecent([]); }}>전체 삭제</button></div>
          {recent.map((p) => (
            <div key={`${p.name}-${p.lat}`} className="recent-item">
              <button className="recent-pick" onClick={() => pick(p)}>
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true"><circle cx="8" cy="8" r="6.5" stroke="#A9AFBD" strokeWidth="1.5" /><path d="M8 4.5V8l2.5 1.5" stroke="#A9AFBD" strokeWidth="1.5" strokeLinecap="round" /></svg>
                <span><b>{p.name}</b><small>{p.address}</small></span>
              </button>
              <button className="recent-del" aria-label={`${p.name} 기록 삭제`} onClick={() => remove(p)}>×</button>
            </div>
          ))}
        </div>
      )}
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

/** 실제 지도 위에 회사 위치와 통근 가능 범위(직선거리 기준 추정)를 그려요. */
function MapPreview({ people }: { people: PersonState[] }) {
  const pts = people.filter((p) => p.company);
  const pins = useMemo<MapPin[]>(() => pts.map((p) => ({ id: p.label, lat: p.company!.lat, lng: p.company!.lng, color: p.color, label: p.company!.name })), [pts.map((p) => `${p.company?.name}${p.label}`).join()]);
  const circles = useMemo<MapCircle[]>(() => pts.map((p) => ({ id: p.label, lat: p.company!.lat, lng: p.company!.lng, color: p.color, radiusKm: reachKm(p.maxCommute) })), [pts.map((p) => `${p.company?.name}${p.maxCommute}`).join()]);
  if (!pts.length) return null;
  return (
    <div style={{ position: 'relative' }}>
      <RealMap pins={pins} circles={circles} height={220} />
      <span style={{ position: 'absolute', left: 10, bottom: 10, zIndex: 500, background: '#1E2230', color: '#fff', borderRadius: 8, padding: '6px 10px', fontSize: 12, fontWeight: 700 }}>두 원이 겹치는 곳이 후보 동네예요 · 대중교통 추정</span>
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
