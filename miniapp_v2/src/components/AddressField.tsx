'use client';

import { useMemo, useState } from 'react';
import { resolveCurrentLocation } from '@/lib/geo';

type Props = {
  lang: string;
  label: string;
  address: string;
  setAddress: (value: string) => void;
  lat: string;
  setLat: (value: string) => void;
  lng: string;
  setLng: (value: string) => void;
  onResolved?: (payload: { address: string; lat: string; lng: string; countryCode?: string; city?: string; region?: string }) => void;
  allowCurrentLocation?: boolean;
  manualHint?: string;
};

function texts(lang: string) {
  if (lang === 'uz') return { current: 'Joylashuvim bo‘yicha', manual: 'Aniq nuqtani qo‘lda kiritish', hideManual: 'Aniq nuqtani yashirish', loading: 'Aniqlanmoqda...', detected: 'Joylashuv topildi' };
  if (lang === 'kz') return { current: 'Менің орным бойынша', manual: 'Нақты нүктені қолмен енгізу', hideManual: 'Нақты нүктені жасыру', loading: 'Анықталуда...', detected: 'Орналасу табылды' };
  if (lang === 'en') return { current: 'Use my location', manual: 'Enter precise point manually', hideManual: 'Hide precise point', loading: 'Resolving...', detected: 'Location detected' };
  return { current: 'По моей локации', manual: 'Указать точку вручную', hideManual: 'Скрыть точную точку', loading: 'Определяем...', detected: 'Локация определена' };
}

export function AddressField({ lang, label, address, setAddress, lat, setLat, lng, setLng, onResolved, allowCurrentLocation = true, manualHint }: Props) {
  const ui = useMemo(() => texts(lang), [lang]);
  const [busy, setBusy] = useState(false);
  const [hint, setHint] = useState('');
  const [manualOpen, setManualOpen] = useState(false);

  async function useCurrentLocation() {
    try {
      setBusy(true);
      setHint('');
      const data = await resolveCurrentLocation();
      const latValue = String(data.lat);
      const lngValue = String(data.lng);
      setAddress(data.address);
      setLat(latValue);
      setLng(lngValue);
      setHint(ui.detected);
      onResolved?.({ address: data.address, lat: latValue, lng: lngValue, countryCode: data.countryCode, city: data.city, region: data.region });
    } catch (error) {
      setHint(error instanceof Error ? error.message : 'Location error');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <label className="label">
        {label}
        <input className="input" value={address} onChange={(event) => setAddress(event.target.value)} placeholder={manualHint || label} />
      </label>
      {allowCurrentLocation ? <button type="button" className="button secondary" onClick={useCurrentLocation} disabled={busy}>{busy ? ui.loading : ui.current}</button> : null}
      <button type="button" className="button secondary" onClick={() => setManualOpen((prev) => !prev)}>{manualOpen ? ui.hideManual : ui.manual}</button>
      {manualOpen ? (
        <div className="grid grid-2">
          <label className="label">Lat<input className="input" value={lat} onChange={(event) => setLat(event.target.value)} placeholder="41.2995" /></label>
          <label className="label">Lng<input className="input" value={lng} onChange={(event) => setLng(event.target.value)} placeholder="69.2401" /></label>
        </div>
      ) : null}
      {hint ? <p className="subtitle">{hint}</p> : null}
      {!allowCurrentLocation && manualHint ? <p className="subtitle">{manualHint}</p> : null}
    </div>
  );
}
