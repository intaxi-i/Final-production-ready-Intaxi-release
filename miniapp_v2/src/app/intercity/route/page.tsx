'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { CalendarDays, CheckCircle2, Route, ShieldAlert } from 'lucide-react';
import { BottomNav } from '@/components/BottomNav';
import { ModeToggle } from '@/components/ModeToggle';
import { APP_ROUTES, currencyForCountry } from '@/lib/constants';
import { createIntercityRoute, getMe } from '@/lib/api';
import { getDriverProfile } from '@/lib/api-extra';
import { getWorldCountryOptions } from '@/lib/world-countries';
import type { DriverProfile, RideMode, UserMe } from '@/lib/types';

const CREATED_STATUS_LABELS: Record<string, string> = {
  search: 'Ищем пассажира',
  active: 'Активно',
  accepted: 'Принято',
  cancelled: 'Отменено',
};

function createdStatusLabel(value?: string | null) {
  return value ? CREATED_STATUS_LABELS[value] || 'Неизвестный статус' : 'Неизвестный статус';
}

function isConfirmedDriver(profile: DriverProfile | null) {
  if (!profile?.status) return false;
  return ['approved', 'verified', 'active'].includes(profile.status.toLowerCase());
}

function roundPrice(value: number, country: string) {
  if (country === 'uz') return Math.round(value / 1000) * 1000;
  if (country === 'kz') return Math.round(value / 100) * 100;
  return Math.round(value);
}

export default function IntercityRoutePage() {
  const countries = useMemo(() => getWorldCountryOptions('ru'), []);
  const [me, setMe] = useState<UserMe | null>(null);
  const [driverProfile, setDriverProfile] = useState<DriverProfile | null>(null);
  const [checkingAccess, setCheckingAccess] = useState(true);
  const [mode, setMode] = useState<RideMode>('regular');
  const [countryCode, setCountryCode] = useState('uz');
  const [fromText, setFromText] = useState('');
  const [toText, setToText] = useState('');
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [seatsAvailable, setSeatsAvailable] = useState('1');
  const [pricePerSeat, setPricePerSeat] = useState('');
  const [pickupMode, setPickupMode] = useState('ask_driver');
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [created, setCreated] = useState<{ id: number; status: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadAccess() {
      try {
        const user = await getMe();
        if (cancelled) return;
        setMe(user);
        if (user.active_role === 'driver') {
          const profile = await getDriverProfile().catch(() => null);
          if (!cancelled) setDriverProfile(profile);
        }
      } catch {
        // Access guard will show safe fallback if profile cannot be loaded.
      } finally {
        if (!cancelled) setCheckingAccess(false);
      }
    }
    void loadAccess();
    return () => {
      cancelled = true;
    };
  }, []);

  const confirmedDriver = me?.active_role === 'driver' && isConfirmedDriver(driverProfile);
  const currency = currencyForCountry(countryCode);
  const canSubmit = fromText.trim().length > 1 && toText.trim().length > 1 && Number(pricePerSeat) > 0;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!confirmedDriver) {
      setError('Публикация маршрута доступна только подтверждённому водителю.');
      return;
    }

    if (!canSubmit) {
      setError('Укажите маршрут, количество мест и цену за место.');
      return;
    }

    setLoading(true);
    try {
      const result = await createIntercityRoute({
        mode,
        country_code: countryCode,
        from_city_id: null,
        to_city_id: null,
        from_text: fromText.trim(),
        to_text: toText.trim(),
        date: date || null,
        time: time || null,
        seats_available: Math.max(1, Number(seatsAvailable || 1)),
        price_per_seat: roundPrice(Number(pricePerSeat), countryCode),
        pickup_mode: pickupMode,
        comment: comment.trim() || null,
      });
      setCreated(result);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать маршрут');
    } finally {
      setLoading(false);
    }
  }

  if (checkingAccess) {
    return (
      <main className="shell stack with-bottom-nav">
        <section className="card"><p className="subtitle">Проверяем статус водителя...</p></section>
        <BottomNav />
      </main>
    );
  }

  if (!confirmedDriver) {
    return (
      <main className="shell stack with-bottom-nav">
        <section className="premium-hero text-center">
          <div className="relative z-10 mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-3xl bg-brand-yellow text-brand-dark">
            <ShieldAlert size={34} />
          </div>
          <div className="relative z-10">
            <p className="metric-label">Водитель межгород</p>
            <h1 className="title">Нужна проверка водителя</h1>
            <p className="subtitle mt-2">Публикация межгород-маршрута доступна только после подтверждения водителя администратором.</p>
          </div>
        </section>
        <section className="card stack">
          <Link className="button primary" href="/driver/register">Открыть заявку водителя</Link>
          <Link className="button secondary" href={APP_ROUTES.intercity}>Вернуться в межгород</Link>
        </section>
        <BottomNav />
      </main>
    );
  }

  if (created) {
    return (
      <main className="shell stack with-bottom-nav">
        <section className="premium-hero text-center">
          <div className="relative z-10 mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-3xl bg-brand-yellow text-brand-dark">
            <CheckCircle2 size={34} />
          </div>
          <div className="relative z-10">
            <p className="metric-label">Маршрут водителя</p>
            <h1 className="title">Маршрут опубликован</h1>
            <p className="subtitle mt-2">Пассажиры увидят ваше направление и смогут принять предложение.</p>
          </div>
        </section>
        <section className="card stack">
          <div className="route-panel">
            <div className="route-line" />
            <div className="route-point"><div className="route-dot" /><div><div className="route-kicker">Откуда</div><div className="route-address">{fromText}</div></div></div>
            <div className="route-point"><div className="route-dot end" /><div><div className="route-kicker">Куда</div><div className="route-address muted">{toText}</div></div></div>
          </div>
          <div className="metric-grid">
            <div className="metric-card"><div className="metric-label">За место</div><div className="metric-value">{roundPrice(Number(pricePerSeat), countryCode).toLocaleString('ru-RU')} {currency}</div></div>
            <div className="metric-card"><div className="metric-label">Статус</div><div className="metric-value">{createdStatusLabel(created.status)}</div></div>
          </div>
          <Link className="button primary" href={APP_ROUTES.intercityOffers}>Смотреть предложения</Link>
          <Link className="button secondary" href={APP_ROUTES.intercity}>Межгород</Link>
        </section>
        <BottomNav />
      </main>
    );
  }

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10">
          <p className="metric-label">Водитель межгород</p>
          <h1 className="title">Еду по маршруту</h1>
          <p className="subtitle mt-2">Опубликуйте свободные места, направление и цену за место.</p>
        </div>
      </section>

      <form className="stack" onSubmit={submit}>
        <section className="card stack">
          <div className="row">
            <div><p className="metric-label">Маршрут</p><h2 className="title" style={{ fontSize: 22 }}>Откуда и куда?</h2></div>
            <Route className="text-brand-yellow" />
          </div>
          <label className="label">Страна
            <select className="select" value={countryCode} onChange={(event) => setCountryCode(event.target.value)}>
              {countries.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}
            </select>
          </label>
          <label className="label">Откуда
            <input className="input" value={fromText} onChange={(event) => setFromText(event.target.value)} placeholder="Город или точка отправления" required />
          </label>
          <label className="label">Куда
            <input className="input" value={toText} onChange={(event) => setToText(event.target.value)} placeholder="Город или точка прибытия" required />
          </label>
        </section>

        <section className="card stack">
          <div className="row"><div><p className="metric-label">Время и места</p><h2 className="title" style={{ fontSize: 22 }}>Когда едете?</h2></div><CalendarDays className="text-brand-yellow" /></div>
          <div className="grid grid-2">
            <label className="label">Дата<input className="input" type="date" value={date} onChange={(event) => setDate(event.target.value)} /></label>
            <label className="label">Время<input className="input" type="time" value={time} onChange={(event) => setTime(event.target.value)} /></label>
          </div>
          <div className="grid grid-2">
            <label className="label">Свободных мест<input className="input" inputMode="numeric" min="1" value={seatsAvailable} onChange={(event) => setSeatsAvailable(event.target.value)} required /></label>
            <label className="label">Цена за место, {currency}<input className="input price-input" inputMode="numeric" min="1" value={pricePerSeat} onChange={(event) => setPricePerSeat(event.target.value)} placeholder="Например 150000" required /></label>
          </div>
          <label className="label">Посадка
            <select className="select" value={pickupMode} onChange={(event) => setPickupMode(event.target.value)}>
              <option value="ask_driver">Договориться с водителем</option>
              <option value="fixed_point">Фиксированная точка</option>
              <option value="door_to_door">Забрать по адресу</option>
            </select>
          </label>
          <ModeToggle value={mode} onChange={setMode} />
        </section>

        <section className="card-soft stack">
          <label className="label">Комментарий
            <textarea className="input" rows={3} value={comment} onChange={(event) => setComment(event.target.value)} placeholder="Машина, багаж, остановки, ориентир" />
          </label>
        </section>

        {error ? <p className="error">{error}</p> : null}
        <button className="button primary full-submit" type="submit" disabled={loading || !canSubmit}>{loading ? 'Публикуем...' : 'Опубликовать маршрут'}</button>
      </form>
      <BottomNav />
    </main>
  );
}
