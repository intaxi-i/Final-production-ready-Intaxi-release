'use client';

import { useEffect, useMemo, useState } from 'react';
import { resolveCurrentLocation, searchPlaces, type PlaceSuggestion } from '@/lib/geo';

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
  countryCode?: string;
  placeholder?: string;
};

function texts(lang: string) {
  if (lang === 'uz') return { current: 'Joylashuvim', advanced: 'Kengaytirilgan', hideAdvanced: 'Yashirish', loading: 'Aniqlanmoqda...', detected: 'Joylashuv topildi', suggestions: 'Variantlar' };
  if (lang === 'kz') return { current: 'Орным', advanced: 'Кеңейтілген', hideAdvanced: 'Жасыру', loading: 'Анықталуда...', detected: 'Орналасу табылды', suggestions: 'Ұсыныстар' };
  if (lang === 'en') return { current: 'Use my location', advanced: 'Advanced', hideAdvanced: 'Hide', loading: 'Resolving...', detected: 'Location detected', suggestions: 'Suggestions' };
  return { current: 'Моя локация', advanced: 'Расширенные настройки', hideAdvanced: 'Скрыть настройки', loading: 'Определяем...', detected: 'Локация определена', suggestions: 'Подходящие адреса' };
}

export function AddressField({ lang, label, address, setAddress, lat, setLat, lng, setLng, onResolved, allowCurrentLocation = true, manualHint, countryCode, placeholder }: Props) {
  const ui = useMemo(() => texts(lang), [lang]);
  const [busy, setBusy] = useState(false);
  const [hint, setHint] = useState('');
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [suggestions, setSuggestions] = useState<PlaceSuggestion[]>([]);
  const [suggestBusy, setSuggestBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const query = address.trim();
    if (query.length < 3) {
      setSuggestions([]);
      return;
    }
    const timer = window.setTimeout(async () => {
      try {
        setSuggestBusy(true);
        const items = await searchPlaces(query, countryCode);
        if (!cancelled) setSuggestions(items);
      } finally {
        if (!cancelled) setSuggestBusy(false);
      }
    }, 450);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [address, countryCode]);

  function applyPlace(place: PlaceSuggestion) {
    setAddress(place.address);
    setLat(String(place.lat));
    setLng(String(place.lng));
    setSuggestions([]);
    onResolved?.({ address: place.address, lat: String(place.lat), lng: String(place.lng), countryCode: place.countryCode, city: place.city, region: place.region });
  }

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
    <div className="address-block">
      <label className="label">
        {label}
        <input className="input" value={address} onChange={(event) => setAddress(event.target.value)} placeholder={placeholder || manualHint || label} />
      </label>

      {suggestBusy ? <p className="subtitle">Ищем адрес...</p> : null}
      {suggestions.length > 0 ? (
        <div className="suggestion-list">
          <p className="metric-label">{ui.suggestions}</p>
          {suggestions.map((place) => (
            <button key={place.id} type="button" className="suggestion-item" onClick={() => applyPlace(place)}>
              <span>{place.address}</span>
              {place.city || place.region ? <small>{[place.city, place.region].filter(Boolean).join(', ')}</small> : null}
            </button>
          ))}
        </div>
      ) : null}

      <div className="address-actions">
        {allowCurrentLocation ? <button type="button" className="button primary" onClick={useCurrentLocation} disabled={busy}>{busy ? ui.loading : ui.current}</button> : null}
        <button type="button" className="button secondary" onClick={() => setAdvancedOpen((prev) => !prev)}>{advancedOpen ? ui.hideAdvanced : ui.advanced}</button>
      </div>

      {advancedOpen ? (
        <div className="advanced-box">
          <p className="subtitle">Координаты нужны только если адрес не удаётся найти обычным способом.</p>
          <div className="grid grid-2">
            <label className="label">Lat<input className="input" value={lat} onChange={(event) => setLat(event.target.value)} placeholder="41.2995" /></label>
            <label className="label">Lng<input className="input" value={lng} onChange={(event) => setLng(event.target.value)} placeholder="69.2401" /></label>
          </div>
        </div>
      ) : null}
      {hint ? <p className="subtitle">{hint}</p> : null}
      {!allowCurrentLocation && manualHint ? <p className="subtitle">{manualHint}</p> : null}
    </div>
  );
}
