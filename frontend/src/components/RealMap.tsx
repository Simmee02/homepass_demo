import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MAPBOX_LOGO } from './mapbox-logo';

export interface MapPin { id: string; lat: number; lng: number; color: string; label?: string; selected?: boolean }
export interface MapCircle { id: string; lat: number; lng: number; color: string; radiusKm: number }

const pinIcon = (color: string, label?: string, selected?: boolean) => L.divIcon({
  className: '',
  iconSize: [24, 30],
  iconAnchor: [12, 30],
  html: `<div style="position:relative">
    <svg width="24" height="30" viewBox="0 0 24 30"><path d="M12 0C5 0 0 5 0 11c0 8 12 19 12 19s12-11 12-19C24 5 19 0 12 0Z" fill="${color}" stroke="#fff" stroke-width="${selected ? 2 : 0}"/><circle cx="12" cy="11" r="4" fill="#fff"/></svg>
    ${label ? `<span style="position:absolute;left:26px;top:2px;white-space:nowrap;background:${selected ? '#1E2230' : '#fff'};color:${selected ? '#fff' : '#1E2230'};border:1px solid #DCE0EA;border-radius:6px;padding:2px 6px;font:700 11px Pretendard,'Noto Sans KR',sans-serif">${label}</span>` : ''}
  </div>`,
});

/** 실제 지도. VITE_MAPBOX_TOKEN이 있으면 Mapbox, 없으면 오픈스트리트맵 타일을 써요. */
export default function RealMap({ pins, circles = [], height = 160, onPinClick, onMapClick }: {
  pins: MapPin[]; circles?: MapCircle[]; height?: number; onPinClick?: (id: string) => void;
  onMapClick?: (lat: number, lng: number) => void;
}) {
  const clickRef = useRef(onMapClick);
  clickRef.current = onMapClick;
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const layer = useRef<L.LayerGroup | null>(null);
  const fitKey = useRef('');

  useEffect(() => {
    if (!el.current || map.current) return;
    map.current = L.map(el.current, { zoomControl: true, attributionControl: true, scrollWheelZoom: true, touchZoom: true, doubleClickZoom: true }).setView([37.5, 127.03], 10);
    map.current.zoomControl.setPosition('topright');
    map.current.attributionControl.setPrefix(false); // 'Leaflet' 표시만 빼요. Mapbox·OSM 출처는 약관상 필수
    const token = import.meta.env.VITE_MAPBOX_TOKEN as string | undefined;
    if (token) {
      // Mapbox 지도 (한글 라벨). 스타일을 바꾸려면 VITE_MAPBOX_STYLE=계정명/스타일ID
      const style = (import.meta.env.VITE_MAPBOX_STYLE as string | undefined) ?? 'mapbox/streets-v12';
      L.tileLayer(`https://api.mapbox.com/styles/v1/${style}/tiles/{z}/{x}/{y}?access_token=${token}`, {
        tileSize: 512, zoomOffset: -1, maxZoom: 20,
        attribution: '&copy; <a href="https://www.mapbox.com/about/maps/" target="_blank">Mapbox</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> <a href="https://apps.mapbox.com/feedback/" target="_blank"><b>Improve this map</b></a>',
      }).addTo(map.current);
      // Mapbox 약관: 로고 필수 (왼쪽 아래)
      const Logo = L.Control.extend({
        onAdd: () => {
          const a = L.DomUtil.create('a', 'mapbox-logo');
          a.href = 'https://www.mapbox.com/';
          a.target = '_blank';
          a.setAttribute('aria-label', 'Mapbox');
          a.style.backgroundImage = `url("${MAPBOX_LOGO}")`;
          return a;
        },
      });
      new Logo({ position: 'bottomleft' }).addTo(map.current);
    } else {
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(map.current);
    }
    layer.current = L.layerGroup().addTo(map.current);
    map.current.on('click', (e: L.LeafletMouseEvent) => clickRef.current?.(e.latlng.lat, e.latlng.lng));
    return () => { map.current?.remove(); map.current = null; };
  }, []);

  useEffect(() => {
    const m = map.current, g = layer.current;
    if (!m || !g) return;
    g.clearLayers();
    const bounds: L.LatLngExpression[] = [];
    circles.forEach((c) => {
      const circle = L.circle([c.lat, c.lng], { radius: c.radiusKm * 1000, color: c.color, weight: 1.5, dashArray: '4 4', fillColor: c.color, fillOpacity: 0.1 });
      circle.addTo(g);
      const b = circle.getBounds();
      bounds.push(b.getNorthWest(), b.getSouthEast());
    });
    pins.forEach((p) => {
      const mk = L.marker([p.lat, p.lng], { icon: pinIcon(p.color, p.label, p.selected), zIndexOffset: p.selected ? 1000 : 0 });
      if (onPinClick) mk.on('click', () => onPinClick(p.id));
      mk.addTo(g);
      bounds.push([p.lat, p.lng]);
    });
    const key = pins.map((p) => `${p.id}${p.lat}`).join('|') + circles.map((c) => `${c.id}${c.radiusKm}`).join('|');
    if (bounds.length && key !== fitKey.current) {
      fitKey.current = key;
      m.fitBounds(L.latLngBounds(bounds), { padding: [16, 16], maxZoom: 13 });
    }
  }, [pins, circles, onPinClick]);

  return <div ref={el} style={{ height, borderRadius: 8, overflow: 'hidden', background: '#EEF1F5', cursor: onMapClick ? 'crosshair' : undefined }} aria-label="지도" />;
}
