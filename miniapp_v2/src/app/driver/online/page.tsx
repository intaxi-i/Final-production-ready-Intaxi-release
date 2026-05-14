'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { CarFront, MapPin, Power, Radio, ShieldAlert } from 'lucide-react';
import { BottomNav } from '@/components/BottomNav';
import { getDriverOnline, getMe, setDriverOnline, updateRole } from '@/lib/api';
import { getDriverProfile } from '@/lib/api-extra';
import { APP_ROUTES } from '@/lib/constants';
import { getCurrentPosition, reverseGeocode } from '@/lib/geo';
import { t } from '@/lib/i18n';
import type { DriverOnlineState, DriverProfile, UserMe } from '@/lib/types';

type Point = { lat: number; lng: number };

function isConfirmedDriver(profile: DriverProfile | null) {
  if (!profile?.status) return false;
  return ['approved', 'verified', 'active'].includes(profile.status.toLowerCase());
}

function statusLabel(lang: string | undefined | null, state: DriverOnlineState | null) {
  if (!state) return '—';
  if (state.is_busy) return t(lang, 'inTrip');
  return state.is_online ? t(lang, 'online') : t(lang, 'offline');
}

export default function DriverOnlinePage() {
  const [state, setState] = useState<DriverOnlineState | null>(null);
  const [profile, setProfile] = useState<DriverProfile | null>(null);
  const [me, setMe] = useState<UserMe | null>(null);
  const [countryCode, setCountryCode] = useState('uz');
  const [locationLabel, setLocationLabel] = useState('');
  const [autoLocation, setAutoLocation] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [locating, setLocating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const watchIdRef = useRef<number | null>(null);
  const lastPointRef = useRef<Point | null>(null);
  const lang = me?.language;

  async function pushLocation(point: Point, country?: string | null) {
    lastPointRef.current = point;
    const nextCountry = country || countryCode;
    setState(await setDriverOnline({ is_online: true, country_code: nextCountry, city_id: state?.city_id ?? null, lat: point.lat, lng: point.lng }));
  }

  async function resolveAndPush(point: Point) {
    const geo = await reverseGeocode(point.lat, point.lng).catch(() => null);
    if (geo?.countryCode) setCountryCode(geo.countryCode);
    setLocationLabel(geo?.address || `${point.lat.toFixed(5)}, ${point.lng.toFixed(5)}`);
    await pushLocation(point, geo?.countryCode || countryCode);
  }

  function stopAutoLocation() {
    if (watchIdRef.current != null && typeof navigator !== 'undefined' && navigator.geolocation) {
      navigator.geolocation.clearWatch(watchIdRef.current);
    }
    watchIdRef.current = null;
    setAutoLocation(false);
  }

  function startAutoLocation() {
    if (typeof navigator === 'undefined' || !navigator.geolocation || watchIdRef.current != null) return;
    setAutoLocation(true);
    watchIdRef.current = navigator.geolocation.watchPosition(
      (position) => {
        const point = { lat: position.coords.latitude, lng: position.coords.longitude };
        const last = lastPointRef.current;
        const movedEnough = !last || Math.abs(last.lat - point.lat) > 0.00015 || Math.abs(last.lng - point.lng) > 0.00015;
        if (movedEnough) void resolveAndPush(point).catch(() => setError(t(lang, 'locationError')));
      },
      () => setError(t(lang, 'locationError')),
      { enableHighAccuracy: true, maximumAge: 15000, timeout: 15000 },
    );
  }

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const [user, onlineState, profileData] = await Promise.all([
        getMe().catch(() => null),
        getDriverOnline().catch(() => null),
        getDriverProfile().catch(() => null),
      ]);
      setMe(user);
      setState(onlineState);
      setProfile(profileData);
      if (onlineState?.country_code) setCountryCode(onlineState.country_code);
      else if (profileData?.country_code) setCountryCode(profileData.country_code);
      if (onlineState?.lat != null && onlineState?.lng != null) {
        lastPointRef.current = { lat: onlineState.lat, lng: onlineState.lng };
        setLocationLabel(`${onlineState.lat.toFixed(5)}, ${onlineState.lng.toFixed(5)}`);
      }
      if (onlineState?.is_online) startAutoLocation();
    } catch (err) {
      setError(err instanceof Error ? err.message : t(lang, 'loadDriverStatusFailed'));
    } finally {
      setLoading(false);
    }
  }

  async function useMyLocation() {
    setLocating(true);
    setError(null);
    try {
      const point = await getCurrentPosition();
      const geo = await reverseGeocode(point.lat, point.lng).catch(() => null);
      if (geo?.countryCode) setCountryCode(geo.countryCode);
      setLocationLabel(geo?.address || `${point.lat.toFixed(5)}, ${point.lng.toFixed(5)}`);
      lastPointRef.current = point;
      if (state?.is_online) await pushLocation(point, geo?.countryCode || countryCode);
    } catch (err) {
      setError(err instanceof Error ? err.message : t(lang, 'locationError'));
    } finally {
      setLocating(false);
    }
  }

  async function toggle(next: boolean) {
    setSaving(true);
    setError(null);
    try {
      await updateRole('driver');
      if (next) {
        const point = await getCurrentPosition();
        const geo = await reverseGeocode(point.lat, point.lng).catch(() => null);
        if (geo?.countryCode) setCountryCode(geo.countryCode);
        setLocationLabel(geo?.address || `${point.lat.toFixed(5)}, ${point.lng.toFixed(5)}`);
        lastPointRef.current = point;
        setState(await setDriverOnline({ is_online: true, country_code: geo?.countryCode || countryCode, lat: point.lat, lng: point.lng }));
        startAutoLocation();
      } else {
        stopAutoLocation();
        setState(await setDriverOnline({ is_online: false, country_code: countryCode }));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t(lang, 'changeStatusFailed'));
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    void load();
    return () => stopAutoLocation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const confirmed = isConfirmedDriver(profile);

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">{t(lang, 'driver')}</p>
            <h1 className="title">{t(lang, 'driverAir')}</h1>
            <p className="subtitle mt-2">{t(lang, 'driverAirHint')}</p>
          </div>
          <Radio className="text-brand-yellow" size={34} />
        </div>
      </section>

      {error ? <p className="error">{error}</p> : null}

      {!loading && !confirmed ? (
        <section className="card stack">
          <div className="row">
            <div>
              <p className="metric-label">{t(lang, 'status')}</p>
              <h2 className="title" style={{ fontSize: 22 }}>{t(lang, 'needDriverCheck')}</h2>
              <p className="subtitle mt-2">{t(lang, 'driverCheckHint')}</p>
            </div>
            <ShieldAlert className="text-brand-yellow" />
          </div>
          <Link href="/driver/register" className="button primary">{t(lang, 'applyDriver')}</Link>
        </section>
      ) : null}

      <section className="metric-grid">
        <div className="metric-card"><div className="metric-label">{t(lang, 'status')}</div><div className="metric-value">{loading ? '...' : statusLabel(lang, state)}</div></div>
        <div className="metric-card"><div className="metric-label">{t(lang, 'country')}</div><div className="metric-value">{countryCode.toUpperCase()}</div></div>
        <div className="metric-card"><div className="metric-label">{t(lang, 'busy')}</div><div className="metric-value">{state?.is_busy ? t(lang, 'busy') : t(lang, 'free')}</div></div>
        <div className="metric-card"><div className="metric-label">{t(lang, 'check')}</div><div className="metric-value">{confirmed ? t(lang, 'ok') : t(lang, 'no')}</div></div>
      </section>

      <section className="card stack">
        <div className="row">
          <div>
            <p className="metric-label">{t(lang, 'location')}</p>
            <h2 className="title" style={{ fontSize: 22 }}>{t(lang, 'locationQuestion')}</h2>
            <p className="subtitle mt-2">{t(lang, 'locationHint')}</p>
          </div>
          <MapPin className="text-brand-yellow" />
        </div>
        <div className="wallet-box"><code>{locationLabel || t(lang, 'locationNotUpdated')}</code></div>
        <p className="subtitle">{autoLocation && state?.is_online ? t(lang, 'autoLocationOn') : t(lang, 'autoLocationOff')}</p>
        <button className="button secondary" type="button" onClick={useMyLocation} disabled={locating || saving}>{locating ? t(lang, 'locating') : t(lang, 'refreshLocation')}</button>
        <label className="label">{t(lang, 'countryCode')}
          <input className="input" value={countryCode.toUpperCase()} onChange={(event) => setCountryCode(event.target.value.toLowerCase().slice(0, 2))} placeholder="UZ" />
        </label>
      </section>

      <section className="card stack">
        <div className="row">
          <div>
            <p className="metric-label">{t(lang, 'air')}</p>
            <h2 className="title" style={{ fontSize: 22 }}>{state?.is_online ? t(lang, 'youAreOnline') : t(lang, 'youAreOffline')}</h2>
            <p className="subtitle mt-2">{t(lang, 'airHint')}</p>
          </div>
          <Power className={state?.is_online ? 'text-brand-yellow' : 'text-slate-300'} />
        </div>
        <div className="grid grid-2">
          <button className="button primary" type="button" disabled={saving || loading || !confirmed || state?.is_online} onClick={() => toggle(true)}>
            {t(lang, 'goOnline')}
          </button>
          <button className="button secondary" type="button" disabled={saving || loading || !state?.is_online} onClick={() => toggle(false)}>
            {t(lang, 'goOffline')}
          </button>
        </div>
      </section>

      {confirmed ? (
        <section className="grid grid-2">
          <Link href={APP_ROUTES.cityOffers} className="intercity-action primary">
            <CarFront size={22} /><div><strong>{t(lang, 'city')}</strong><span>{t(lang, 'cityAir')}</span></div>
          </Link>
          <Link href={APP_ROUTES.intercityOffers} className="intercity-action dark">
            <Radio size={22} /><div><strong>{t(lang, 'intercity')}</strong><span>{t(lang, 'intercityAir')}</span></div>
          </Link>
        </section>
      ) : null}
      <BottomNav />
    </main>
  );
}
