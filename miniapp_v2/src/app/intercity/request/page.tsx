'use client';

import { FormEvent, useMemo, useState } from 'react';
import Link from 'next/link';
import { CalendarDays, CheckCircle2, MapPinned } from 'lucide-react';
import { BottomNav } from '@/components/BottomNav';
import { ModeToggle } from '@/components/ModeToggle';
import { APP_ROUTES, currencyForCountry } from '@/lib/constants';
import { createIntercityRequest } from '@/lib/api';
import { getWorldCountryOptions } from '@/lib/world-countries';
import type { RideMode } from '@/lib/types';

function roundedIntercityPrice(value: number, country: string) {
  if (country === 'uz') return Math.round(value / 1000) * 1000;
  if (country === 'kz') return Math.round(value / 100) * 100;
  return Math.round(value);
}

function statusLabel(value: string) {
  if (value === 'search') return 'Ищем водителя';
  if (value === 'active') return 'Активно';
  if (value === 'accepted') return 'Принято';
  if (value === 'cancelled') return 'Отменено';
  return 'Статус неизвестен';
}

export default function IntercityRequestPage() {
  const countries = useMemo(() => getWorldCountryOptions('ru'), []);
  const [mode, setMode] = useState<RideMode>('regular');
  const [countryCode, setCountryCode] = useState('uz');
  const [fromText, setFromText] = useState('');
  const [toText, setToText] = useState('');
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [seats, setSeats] = useState('1');
  const [price, setPrice] = useState('');
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [created, setCreated] = useState<{ id: number; status: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const currency = currencyForCountry(countryCode);
  const canSubmit = fromText.trim().length > 1 && toText.trim().length > 1 && Number(price) > 0;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!canSubmit) {
      setError('Укажите города, дату при необходимости и свою цену.');
      return;
    }

    setLoading(true);
    try {
      const result = await createIntercityRequest({
        mode,
        country_code: countryCode,
        from_city_id: null,
        to_city_id: null,
        from_text: fromText.trim(),
        to_text: toText.trim(),
        date: date || null,
        time: time || null,
        seats: Math.max(1, Number(seats || 1)),
        passenger_price: roundedIntercityPrice(Number(price), countryCode),
        comment: comment.trim() || null,
      });
      setCreated(result);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать межгород-заявку');
    } finally {
      setLoading(false);
    }
  }

  if (created) {
    return (
      <main className="shell stack with-bottom-nav">
        <section className="premium-hero text-center">
          <div className="relative z-10 mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-3xl bg-brand-yellow text-brand-dark">
            <CheckCircle2 size={34} />
          </div>
          <div className="relative z-10">
            <p className="metric-label">Межгород</p>
            <h1 className="title">Заявка создана</h1>
            <p className="subtitle mt-2">Водители увидят направление и смогут принять поездку.</p>
          </div>
        </section>
        <section className="card stack">
          <div className="route-panel">
            <div className="route-line" />
            <div className="route-point"><div className="route-dot" /><div><div className="route-kicker">Откуда</div><div className="route-address">{fromText}</div></div></div>
            <div className="route-point"><div className="route-dot end" /><div><div className="route-kicker">Куда</div><div className="route-address muted">{toText}</div></div></div>
          </div>
          <div className="metric-grid">
            <div className="metric-card"><div className="metric-label">Цена</div><div className="metric-value">{roundedIntercityPrice(Number(price), countryCode).toLocaleString('ru-RU')} {currency}</div></div>
            <div className="metric-card"><div className="metric-label">Статус</div><div className="metric-value">{statusLabel(created.status)}</div></div>
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
          <p className="metric-label">Межгородская поездка</p>
          <h1 className="title">Создать заявку</h1>
          <p className="subtitle mt-2">Укажите направление, дату, места и цену, которую готовы предложить.</p>
        </div>
      </section>

      <form className="stack" onSubmit={submit}>
        <section className="card stack">
          <div className="row">
            <div><p className="metric-label">Маршрут</p><h2 className="title" style={{ fontSize: 22 }}>Откуда и куда?</h2></div>
            <MapPinned className="text-brand-yellow" />
          </div>
          <label className="label">Страна
            <select className="select" value={countryCode} onChange={(event) => setCountryCode(event.target.value)}>
              {countries.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}
            </select>
          </label>
          <label className="label">Откуда
            <input className="input" value={fromText} onChange={(event) => setFromText(event.target.value)} placeholder="Город, область или адрес отправления" required />
          </label>
          <label className="label">Куда
            <input className="input" value={toText} onChange={(event) => setToText(event.target.value)} placeholder="Город, область или адрес назначения" required />
          </label>
        </section>

        <section className="card stack">
          <div className="row"><div><p className="metric-label">Время и места</p><h2 className="title" style={{ fontSize: 22 }}>Когда едем?</h2></div><CalendarDays className="text-brand-yellow" /></div>
          <div className="grid grid-2">
            <label className="label">Дата<input className="input" type="date" value={date} onChange={(event) => setDate(event.target.value)} /></label>
            <label className="label">Время<input className="input" type="time" value={time} onChange={(event) => setTime(event.target.value)} /></label>
          </div>
          <div className="grid grid-2">
            <label className="label">Мест<input className="input" inputMode="numeric" min="1" value={seats} onChange={(event) => setSeats(event.target.value)} required /></label>
            <label className="label">Ваша цена, {currency}<input className="input price-input" inputMode="numeric" min="1" value={price} onChange={(event) => setPrice(event.target.value)} placeholder="Например 150000" required /></label>
          </div>
          <ModeToggle value={mode} onChange={setMode} />
        </section>

        <section className="card-soft stack">
          <label className="label">Комментарий
            <textarea className="input" rows={3} value={comment} onChange={(event) => setComment(event.target.value)} placeholder="Багаж, точка встречи, пожелания" />
          </label>
        </section>

        {error ? <p className="error">{error}</p> : null}
        <button className="button primary full-submit" type="submit" disabled={loading || !canSubmit}>{loading ? 'Создаём...' : 'Создать межгород-заявку'}</button>
      </form>
      <BottomNav />
    </main>
  );
}
