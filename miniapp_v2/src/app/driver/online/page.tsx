'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { CarFront, MapPin, Power, Radio, RefreshCw, ShieldAlert } from 'lucide-react';
import { BottomNav } from '@/components/BottomNav';
import { getDriverOnline, setDriverOnline, updateRole } from '@/lib/api';
import { getDriverProfile } from '@/lib/api-extra';
import { APP_ROUTES } from '@/lib/constants';
import { getCurrentPosition, reverseGeocode } from '@/lib/geo';
import type { DriverOnlineState, DriverProfile } from '@/lib/types';

function isConfirmedDriver(profile: DriverProfile | null) {
  if (!profile?.status) return false;
  return ['approved', 'verified', 'active'].includes(profile.status.toLowerCase());
}

function statusLabel(state: DriverOnlineState | null) {
  if (!state) return '—';
  if (state.is_busy) return 'В поездке';
  return state.is_online ? 'В эфире' : 'Не в эфире';
}

export default function DriverOnlinePage() {
  const [state, setState] = useState<DriverOnlineState | null>(null);
  const [profile, setProfile] = useState<DriverProfile | null>(null);
  const [countryCode, setCountryCode] = useState('uz');
  const [locationLabel, setLocationLabel] = useState('Геолокация не обновлена');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [locating, setLocating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const [onlineState, profileData] = await Promise.all([
        getDriverOnline().catch(() => null),
        getDriverProfile().catch(() => null),
      ]);
      setState(onlineState);
      setProfile(profileData);
      if (onlineState?.country_code) setCountryCode(onlineState.country_code);
      else if (profileData?.country_code) setCountryCode(profileData.country_code);
      if (onlineState?.lat != null && onlineState?.lng != null) {
        setLocationLabel(`${onlineState.lat.toFixed(5)}, ${onlineState.lng.toFixed(5)}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить статус водителя');
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
      if (state?.is_online) {
        setState(await setDriverOnline({ is_online: true, country_code: geo?.countryCode || countryCode, city_id: state.city_id ?? null }));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось получить геолокацию');
    } finally {
      setLocating(false);
    }
  }

  async function toggle(next: boolean) {
    setSaving(true);
    setError(null);
    try {
      await updateRole('driver');
      setState(await setDriverOnline({ is_online: next, country_code: countryCode }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось изменить статус');
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => { load(); }, []);

  const confirmed = isConfirmedDriver(profile);

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">Водитель</p>
            <h1 className="title">Эфир заказов</h1>
            <p className="subtitle mt-2">Включите эфир, чтобы получать городские и межгородские предложения.</p>
          </div>
          <Radio className="text-brand-yellow" size={34} />
        </div>
      </section>

      {error ? <p className="error">{error}</p> : null}

      {!loading && !confirmed ? (
        <section className="card stack">
          <div className="row">
            <div>
              <p className="metric-label">Доступ</p>
              <h2 className="title" style={{ fontSize: 22 }}>Нужна проверка водителя</h2>
              <p className="subtitle mt-2">После подтверждения профиля здесь появится полноценный выход в эфир.</p>
            </div>
            <ShieldAlert className="text-brand-yellow" />
          </div>
          <Link href="/driver/register" className="button primary">Подать заявку</Link>
        </section>
      ) : null}

      <section className="metric-grid">
        <div className="metric-card"><div className="metric-label">Статус</div><div className="metric-value">{loading ? '...' : statusLabel(state)}</div></div>
        <div className="metric-card"><div className="metric-label">Страна</div><div className="metric-value">{countryCode.toUpperCase()}</div></div>
        <div className="metric-card"><div className="metric-label">Занятость</div><div className="metric-value">{state?.is_busy ? 'Занят' : 'Свободен'}</div></div>
        <div className="metric-card"><div className="metric-label">Проверка</div><div className="metric-value">{confirmed ? 'ОК' : 'Нет'}</div></div>
      </section>

      <section className="card stack">
        <div className="row">
          <div>
            <p className="metric-label">Локация</p>
            <h2 className="title" style={{ fontSize: 22 }}>Где принимать заказы?</h2>
            <p className="subtitle mt-2">Для корректного эфира обновите текущую точку перед выходом online.</p>
          </div>
          <MapPin className="text-brand-yellow" />
        </div>
        <div className="wallet-box"><code>{locationLabel}</code></div>
        <button className="button secondary" type="button" onClick={useMyLocation} disabled={locating || saving}>{locating ? 'Определяем...' : 'Обновить геолокацию'}</button>
        <label className="label">Код страны
          <input className="input" value={countryCode.toUpperCase()} onChange={(event) => setCountryCode(event.target.value.toLowerCase().slice(0, 2))} placeholder="UZ" />
        </label>
      </section>

      <section className="card stack">
        <div className="row">
          <div>
            <p className="metric-label">Эфир</p>
            <h2 className="title" style={{ fontSize: 22 }}>{state?.is_online ? 'Вы сейчас в эфире' : 'Вы не в эфире'}</h2>
            <p className="subtitle mt-2">Когда эфир включён, водитель может видеть доступные заказы по своей зоне.</p>
          </div>
          <Power className={state?.is_online ? 'text-brand-yellow' : 'text-slate-300'} />
        </div>
        <div className="grid grid-2">
          <button className="button primary" type="button" disabled={saving || loading || !confirmed || state?.is_online} onClick={() => toggle(true)}>
            Выйти в эфир
          </button>
          <button className="button secondary" type="button" disabled={saving || loading || !state?.is_online} onClick={() => toggle(false)}>
            Завершить эфир
          </button>
        </div>
      </section>

      {confirmed ? (
        <section className="grid grid-2">
          <Link href={APP_ROUTES.cityOffers} className="intercity-action primary">
            <CarFront size={22} /><div><strong>Город</strong><span>Эфир заказов</span></div>
          </Link>
          <Link href={APP_ROUTES.intercityOffers} className="intercity-action dark">
            <Radio size={22} /><div><strong>Межгород</strong><span>Заявки и маршруты</span></div>
          </Link>
        </section>
      ) : null}
      <BottomNav />
    </main>
  );
}
