import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';

type Pose = 'hello' | 'detective' | 'coin' | 'pin' | 'party' | 'heart';

/** 홈패스 캐릭터 (Figma 'Mascot' 컴포넌트를 단순화한 버전) */
export function Mascot({ pose = 'hello', size = 96 }: { pose?: Pose; size?: number }) {
  const eyes = pose === 'detective'
    ? <><ellipse cx="44" cy="67" rx="4" ry="6" fill="#14161F" /><ellipse cx="61" cy="67" rx="4" ry="6" fill="#14161F" /></>
    : pose === 'party'
      ? <path d="M46 63l7 5-7 5M74 63l-7 5 7 5" stroke="#14161F" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" fill="none" />
      : pose === 'heart' || pose === 'coin'
        ? <path d="M45 69c2-4 8-4 10 0M65 69c2-4 8-4 10 0" stroke="#14161F" strokeWidth="3" strokeLinecap="round" fill="none" />
        : <><ellipse cx="51" cy="68" rx="4" ry="6" fill="#14161F" /><ellipse cx="69" cy="68" rx="4" ry="6" fill="#14161F" /></>;
  return (
    <svg width={size} height={size} viewBox="0 0 120 120" fill="none" aria-hidden="true">
      <ellipse cx="60" cy="110" rx="28" ry="4" fill="#3A45B8" fillOpacity=".35" />
      <path d="M25 62c0-7 3-13 9-17l19-15c4-3 10-3 14 0l19 15c6 4 9 10 9 17v26c0 9-7 16-16 16H41c-9 0-16-7-16-16V62Z" fill="#fff" />
      <path d="M95 62v26c0 9-7 16-16 16H68c11-3 18-12 18-24V54c0-4-1-7-3-9l3 0c6 4 9 10 9 17Z" fill="#E3E6FF" />
      {eyes}
      {pose === 'detective'
        ? <path d="M52 79c-3-5-10-6-14-1-2 3-6 3-8 0 1 6 9 9 15 5 3-2 5-3 7-5 2 2 4 3 7 5 6 4 14 1 15-5-2 3-6 3-8 0-4-5-11-4-14 1Z" fill="#9AA0AE" />
        : pose === 'party' ? <path d="M52 79c0 8 16 8 16 0Z" fill="#E2557A" />
          : <path d="M54 81c3 3 9 3 12 0" stroke="#E2557A" strokeWidth="3" strokeLinecap="round" />}
      {pose !== 'detective' && <><ellipse cx="40" cy="78" rx="5" ry="3" fill="#FF9DB5" fillOpacity=".6" /><ellipse cx="80" cy="78" rx="5" ry="3" fill="#FF9DB5" fillOpacity=".6" /></>}
      {pose === 'detective' && <><circle cx="16" cy="54" r="11" fill="#CFEFFF" fillOpacity=".8" stroke="#2B2F3A" strokeWidth="3" /><path d="M22 63l5 9" stroke="#2B2F3A" strokeWidth="4" strokeLinecap="round" /></>}
      {pose === 'pin' && <><path d="M102 14c-8 0-13 6-13 12 0 9 13 20 13 20s13-11 13-20c0-6-5-12-13-12Z" fill="#FF6B8A" /><circle cx="102" cy="26" r="5" fill="#fff" /></>}
      {pose === 'coin' && <><circle cx="104" cy="36" r="10" fill="#FFC83D" stroke="#E8A92A" strokeWidth="1.5" /><path d="M104 31v10" stroke="#E8A92A" strokeWidth="2.4" strokeLinecap="round" /></>}
      {pose === 'heart' && <path d="M60 106s-15-8-15-18a7.5 7.5 0 0 1 15-3 7.5 7.5 0 0 1 15 3c0 10-15 18-15 18Z" fill="#FF6B8A" />}
      {(pose === 'hello' || pose === 'detective' || pose === 'pin') && <path d="M104 22l2.2 5.8 5.8 2.2-5.8 2.2-2.2 5.8-2.2-5.8-5.8-2.2 5.8-2.2Z" fill="#FFD66B" />}
    </svg>
  );
}

export function BackIcon() {
  return <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true"><path d="M18 11H4m6-6-6 6 6 6" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>;
}

export function Chevron() {
  return <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="m6 3 5 5-5 5" stroke="#A9AFBD" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>;
}

export function StepHeader({ step, name, title, pose, progress, bubble }: {
  step: number; name: string; title: string; pose: Pose; progress: number; bubble: string;
}) {
  const nav = useNavigate();
  return (
    <header className="top">
      <div className="nav"><button className="icon-btn" aria-label="이전" onClick={() => nav(-1)}><BackIcon /></button></div>
      <div className="row">
        <div>
          <div className="step">{step} / 3 · {name}</div>
          <h1>{title}</h1>
        </div>
        <Mascot pose={pose} size={92} />
      </div>
      <div className="progress" aria-label={`진행률 ${progress}%`}>
        <div className="track">
          <div className="fill" style={{ width: `${progress}%` }} />
          <div className="knob" style={{ left: `calc(${progress}% - 11px)` }} />
        </div>
        <span>{progress}%</span>
      </div>
      <div className="bubble">{bubble}</div>
    </header>
  );
}

export function Cta({ children, onClick, disabled }: { children: ReactNode; onClick: () => void; disabled?: boolean }) {
  return <div className="cta"><button className="btn" onClick={onClick} disabled={disabled}>{children}</button></div>;
}
