'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { BottomNav } from '@/components/BottomNav';
import { ModeToggle } from '@/components/ModeToggle';
import { OrderCard } from '@/components/OrderCard';
import { PageHeader } from '@/components/PageHeader';
import { APP_ROUTES } from '@/lib/constants';
import { createCityOrder, listMyCityOrders, raiseCityOrderPrice } from '@/lib/api';
import { t } from '@/lib/i18n';
import type { CityOrder, RideMode } from '@/lib/types';

const FALLBACK_PRICE_PER_KM: Record<string, { currency: string; pricePerKm: number }> = {
  uz: { currency: 'UZS', pricePerKm: 2500 },
  tr: { currency: 'TRY', pricePerKm: 45 },
  kz: { currency: 'KZT', pricePerKm: 120 },
  sa: { currency: 'SAR', pricePerKm: 2.5 },
};

function searchDots(seconds: number) {
  return '.'.repeat((seconds % 3) + 1);
}

export default function CityCreatePage() {
  const [mode, setMode] = useState<RideMode>('regular');
  const [country, setCountry] = useState('uz');
  const [pickup, setPickup] = useState('');
  const [destination, setDestination] = useState('');
  const [price, setPrice] = useState('30000');
  const [seats, setSeats] = useState('1');
  const [comment, setComment] = useState('');
  const [created, setCreated] = useState<CityOrder | null>(null);
  const [driversSeen, setDriversSeen] = useState(0);
  const [secondsPassed, setSecondsPassed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const tariff = FALLBACK_PRICE_PER_KM[country] || FALLBACK_PRICE_PER_KM.uz;
  const recommendedPrice = useMemo(() => {
    const value = Number(price || 0);
    return Number.isFinite(value) && value > 0 ? value : 30000;
  }, [price]);

  useEffect(() => {
    if (!created) return;
    const timer = window.setInterval(() => setSecondsPassed((prev) => prev + 1), 1000);
    return () => window.clearInterval(timer);
  }, [created]);

  useEffect(() => {
    if (!created) return;
    let cancelled = false;
    async function pollOrder() {
      try {
        const orders = await listMyCityOrders();
        if (cancelled) return;
        const current = orders.find((item) => item.id === created.id);
        if (!current) return;
        setCreated(current);
        setDriversSeen(current.seen_by_drivers || 0);
        setPrice(String(current.passenger_price));
        if (current.accepted_trip_id) {
          window.location.href = APP_ROUTES.currentTrip;
        }
      } catch {
        // polling must not break the visible order screen
      }
    }
    void pollOrder();
    const timer = window.setInterval(() => void pollOrder(), 6000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [created?.id]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setLoading(true);
    try {
      const order = await createCityOrder({
        mode,
        country_code: country,
        city_id: null,
        pickup_address: pickup.trim(),
        destination_address: destination.trim(),
        seats: Number(seats || 1),
        passenger_price: Number(price || recommendedPrice),
      });
      setCreated(order);
      setDriversSeen(order.seen_by_drivers || 0);
      setSecondsPassed(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать заказ');
    } finally {
      setLoading(false);
    }
  }

  async function raisePrice() {
    if (!created) return;
    const nextPrice = Math.round(Number(price || created.passenger_price || 0) * 1.1);
    setError(null);
    try {
      const next = await raiseCityOrderPrice(created.id, nextPrice);
      setCreated(next);
      setPrice(String(next.passenger_price));
      setMessage(t('ru', 'updatedSuccessfully'));
    } catch (err) {
      setError(err instanceof Error ? err.message : t('ru', 'operationFailed'));
    }
  }

  return (
    <main className={`shell stack with-bottom-nav ${mode === 'women' ? 'women-mode' : ''}`}>
      <section className="card stack">
        <PageHeader
          title="Создать city-заказ"
          subtitle="Пассажир предлагает цену. Backend V2 проверяет роль, режим, страну и создаёт заказ."
          backHref={APP_ROUTES.home}
        />
        <ModeToggle value={mode} onChange={setMode} />
        <form className="stack" onSubmit={submit}>
          <div className="grid grid-2">
            <label className="label">
              Страна
              <select className="select" value={country} onChange={(event) => setCountry(event.target.value)}>
                <option value="uz">Uzbekistan</option>
                <option value="tr">Turkey</option>
                <option value="kz">Kazakhstan</option>
                <option value="sa">Saudi Arabia</option>
              </select>
            </label>
            <label className="label">
              Мест
              <input className="input" inputMode="numeric" min="1" value={seats} onChange={(event) => setSeats(event.target.value)} required />
            </label>
          </div>
          <label className="label">
            {t('ru', 'fromAddress')}
            <input className="input" value={pickup} onChange={(event) => setPickup(event.target.value)} required placeholder="Например: Юнусабад, дом 10" />
          </label>
          <label className="label">
            {t('ru', 'toAddress')}
            <input className="input" value={destination} onChange={(event) => setDestination(event.target.value)} required placeholder="Например: аэропорт / вокзал / адрес" />
          </label>
          <div className="grid grid-2">
            <div className="card-soft">
              <strong>{recommendedPrice} {tariff.currency}</strong>
              <p className="subtitle">{t('ru', 'recommendedPrice')} · ~{tariff.pricePerKm} {tariff.currency}/km</p>
            </div>
            <label className="label">
              {t('ru', 'yourPrice')}
              <input className="input" inputMode="numeric" value={price} onChange={(event) => setPrice(event.target.value)} required />
            </label>
          </div>
          <label className="label">
            {t('ru', 'comment')}
            <textarea className="input" value={comment} onChange={(event) => setComment(event.target.value)} rows={3} placeholder={t('ru', 'writeComment')} />
          </label>
          {error ? <p className="error">{error}</p> : null}
          {message ? <p className="success">{message}</p> : null}
          <button className="button" type="submit" disabled={loading}>
            {loading ? 'Создаём...' : t('ru', 'createOrder')}
          </button>
        </form>
      </section>

      {created ? (
        <section className="card stack">
          <h2 className="title" style={{ fontSize: 22 }}>Ищем водителя{searchDots(secondsPassed)}</h2>
          <p className="subtitle">{t('ru', 'searchStarted')}</p>
          <div className="info-grid">
            <div className="card-soft"><strong>{driversSeen}</strong><p className="subtitle">{t('ru', 'driversSeen')}</p></div>
            <div className="card-soft"><strong>{created.status}</strong><p className="subtitle">{t('ru', 'status')}</p></div>
            <div className="card-soft"><strong>{created.passenger_price} {created.currency}</strong><p className="subtitle">{t('ru', 'yourPrice')}</p></div>
          </div>
          <OrderCard order={created} />
          <div className="actions">
            {secondsPassed >= 30 ? <button className="button" type="button" onClick={raisePrice}>{t('ru', 'raisePrice')}</button> : null}
            <Link className="button secondary" href={APP_ROUTES.cityMyOrders}>Открыть мои заказы</Link>
          </div>
          {secondsPassed < 30 ? <p className="subtitle">{secondsPassed}s · {t('ru', 'raisePriceHint')}</p> : null}
        </section>
      ) : null}
      <BottomNav />
    </main>
  );
}
