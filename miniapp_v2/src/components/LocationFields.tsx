'use client';

import { useMemo, useState } from 'react';
import { COUNTRY_OPTIONS_EXTENDED } from '@/lib/country-config';
import { resolveCurrentLocation } from '@/lib/geo';
import { getLocalityOptionsForCountry, getRegionOptionsForCountry, guessRegionFromCity } from '@/lib/locations';
import { t } from '@/lib/i18n';

type Props = {
  lang: string;
  country: string;
  setCountry?: (value: string) => void;
  regionKey: string;
  setRegionKey: (value: string) => void;
  city: string;
  setCity: (value: string) => void;
  showCountry?: boolean;
  collapsible?: boolean;
};

function labels(lang: string) {
  if (lang === 'uz') return { current: 'Joylashuvni bir bosishda olish', manual: 'Joylashuvni qo‘lda ko‘rsatish', hideManual: 'Qo‘lda ko‘rsatishni yashirish', detected: 'Aniqlangan joy', loading: 'Aniqlanmoqda...' };
  if (lang === 'kz') return { current: 'Орнымды бір басуда алу', manual: 'Орналасуды қолмен көрсету', hideManual: 'Қолмен таңдауды жасыру', detected: 'Анықталған орын', loading: 'Анықталуда...' };
  if (lang === 'en') return { current: 'Use current location', manual: 'Set location manually', hideManual: 'Hide manual location', detected: 'Detected place', loading: 'Resolving...' };
  return { current: 'Определить по текущей локации', manual: 'Указать локацию вручную', hideManual: 'Скрыть ручной выбор', detected: 'Определённое место', loading: 'Определяем...' };
}

export function LocationFields({ lang, country, setCountry, regionKey, setRegionKey, city, setCity, showCountry = true, collapsible = false }: Props) {
  const ui = useMemo(() => labels(lang), [lang]);
  const regionOptions = getRegionOptionsForCountry(country, lang);
  const cityOptions = getLocalityOptionsForCountry(country, regionKey);
  const [busy, setBusy] = useState(false);
  const [manualOpen, setManualOpen] = useState(!collapsible);
  const [detectedAddress, setDetectedAddress] = useState('');

  async function useCurrentLocation() {
    try {
      setBusy(true);
      const data = await resolveCurrentLocation();
      setDetectedAddress(data.address);
      const nextCountry = ['uz', 'tr', 'sa', 'kz'].includes(data.countryCode || '') ? data.countryCode || country : country;
      setCountry?.(nextCountry);
      const guessedCity = data.city || city;
      if (nextCountry === 'uz' || nextCountry === 'kz') {
        const guessedRegion = guessRegionFromCity(nextCountry, guessedCity || data.region || '');
        if (guessedRegion) setRegionKey(guessedRegion);
      } else {
        setRegionKey('');
      }
      if (guessedCity) setCity(guessedCity);
      if (collapsible) setManualOpen(false);
    } catch {
      setDetectedAddress('');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <button type="button" className="button secondary" onClick={useCurrentLocation} disabled={busy}>{busy ? ui.loading : ui.current}</button>
      {detectedAddress || city ? (
        <div className="card-soft">
          <strong>{ui.detected}</strong>
          <p className="subtitle">{city || detectedAddress || '—'}</p>
        </div>
      ) : null}
      {collapsible ? <button type="button" className="button secondary" onClick={() => setManualOpen((prev) => !prev)}>{manualOpen ? ui.hideManual : ui.manual}</button> : null}
      {manualOpen ? (
        <>
          {showCountry ? (
            <label className="label">
              {t(lang, 'country')}
              <select className="select" value={country} onChange={(event) => { setCountry?.(event.target.value); setRegionKey(''); setCity(''); }}>
                {COUNTRY_OPTIONS_EXTENDED.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}
              </select>
            </label>
          ) : null}
          {country === 'uz' || country === 'kz' ? (
            <label className="label">
              {t(lang, 'region')}
              <select className="select" value={regionKey} onChange={(event) => { setRegionKey(event.target.value); setCity(''); }}>
                <option value="">{t(lang, 'chooseRegion')}</option>
                {regionOptions.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}
              </select>
            </label>
          ) : null}
          <label className="label">
            {t(lang, 'cityField')}
            <select className="select" value={city} onChange={(event) => setCity(event.target.value)}>
              <option value="">{t(lang, 'chooseCity')}</option>
              {cityOptions.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
        </>
      ) : null}
    </div>
  );
}
