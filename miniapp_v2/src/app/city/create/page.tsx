'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { AddressField } from '@/components/AddressField';
import { BottomNav } from '@/components/BottomNav';
import { MapPointPicker } from '@/components/MapPointPicker';
import { ModeToggle } from '@/components/ModeToggle';
import { OrderCard } from '@/components/OrderCard';
import { PageHeader } from '@/components/PageHeader';
import { APP_ROUTES } from '@/lib/constants';
import { createCityOrder, listMyCityOrders, raiseCityOrderPrice } from '@/lib/api';
import { haversineKm } from '@/lib/geo';
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

function parseCoordinate(value: string): number | null {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export default function CityCreatePage() {
  const [mode, setMode] = useState<RideMode>('regular');
  const [country, setCountry] = useState('uz');
  const [pickup, setPickup] = useState('');
  const [pickupLat, setPickupLat] = useState('');
  const [pickupLng, setPickupLng] = useState('');
  const [destination, setDestination] = useState('');
  const [destinationLat, setDestinationLat] = useState('');
  const [destinationLng, setDestinationLng] = useState('');
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
  const pickupLatNum = parseCoordinate(pickupLat);
  const pickupLngNum = parseCoordinate(pickupLng);
  const destinationLatNum = parseCoordinate(destinationLat);
  const destinationLngNum = parseCoordinate(destinationLng);
  
  const estimatedDistance = useMemo(() => {
    if (pickupLatNum == null || pickupLngNum == null || destinationLatNum == null || destinationLngNum == null) return null;
    return haversineKm(pickupLatNum, pickupLngNum, destinationLatNum, destinationLngNum);
  }, [pickupLatNum, pickupLngNum, destinationLatNum, destinationLngNum]);
  
  const recommendedPrice = useMemo(() => {
    if (estimatedDistance != null) {
      return Math.max(Math.round(estimatedDistance * tariff.pricePerKm), Number(country === 'uz' ? 10000 : 1));
    }
    const value = Number(price || 0);
    return Number.isFinite(value) && value > 0 ? value : 30000;
  }, [country, estimatedDistance, price, tariff.pricePerKm]);

  useEffect(() => {
    if (estimatedDistance != null) setPrice(String(recommendedPrice));
  }, [estimatedDistance, recommendedPrice]);

  useEffect(() => {
    if (!created?.id) return;
    const timer = window.setInterval(() => setSecondsPassed((prev) => prev + 1), 1000);
    return () => window.clearInterval(timer);
  }, [created?.id]);

  useEffect(() => {
    if (!created?.id) return;
    let cancelled = false;
    async function pollOrder() {
      try {
        const orders = await listMyCityOrders();
        if (cancelled) return;
        const current = orders?.find((item) => item?.id === created?.id);
        if (!current) return;
        setCreated(current);
        setDriversSeen(current?.seen_by_drivers ?? 0);
        setPrice(String(current?.passenger_price ?? 0));
        if (current?.accepted_trip_id) {
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
        pickup_lat: pickupLatNum,
        pickup_lng: pickupLngNum,
        destination_address: destination.trim(),
        destination_lat: destinationLatNum,
        destination_lng: destinationLngNum,
        seats: Number(seats || 1),
        passenger_price: Number(price || recommendedPrice),
        comment: comment.trim() || null,
      });
      setCreated(order);
      setDriversSeen(order?.seen_by_drivers ?? 0);
      setSecondsPassed(0);
    } catch (err) {
      setError(err instanceof Error ? err?.message : 'Не удалось создать заказ');
    } finally {
      setLoading(false);
    }
  }

  async function raisePrice() {
    if (!created?.id) return;
    const nextPrice = Math.round(Number(price || created?.passenger_price || 0) * 1.1);
    setError(null);
    try {
      const next = await raiseCityOrderPrice(created.id, nextPrice);
      setCreated(next);
      setPrice(String(next?.passenger_price ?? 0));
      setMessage(t('ru', 'updatedSuccessfully'));
    } catch (err) {
      setError(err instanceof Error ? err?.message : t('ru', 'operationFailed'));
    }
  }

  return (
    <main className={`shell stack with-bottom-nav ${mode === 'women' ? 'women-mode' : ''}`}>
      <section className="card stack">
        <PageHeader title="Создать city-заказ" subtitle="Пассажир предлагает цену. Можно выбрать адрес вручную, по текущей локации или точкой на карте." backHref={APP_ROUTES.home} />
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

          <AddressField lang="ru" label={t('ru', 'fromAddress')} address={pickup} setAddress={setPickup} lat={pickupLat} setLat={setPickupLat} lng={pickupLng} setLng={setPickupLng} onResolved={(payload) => { if (payload?.countryCode && ['uz', 'tr', 'kz', 'sa'].includes(payload.countryCode)) setCountry(payload.countryCode); }} />
          <MapPointPicker lang="ru" triggerLabel="Выбрать точку отправления на карте" title="Точка отправления" confirmLabel="Подтвердить" cancelLabel="Отмена" initialLat={pickupLatNum} initialLng={pickupLngNum} onConfirm={(payload) => { setPickup(payload?.address ?? ''); setPickupLat(payload?.lat ?? ''); setPickupLng(payload?.lng ?? ''); if (payload?.countryCode && ['uz', 'tr', 'kz', 'sa'].includes(payload.countryCode)) setCountry(payload.countryCode); }} />

          <AddressField lang="ru" label={t('ru', 'toAddress')} address={destination} setAddress={setDestination} lat={destinationLat} setLat={setDestinationLat} lng={destinationLng} setLng={setDestinationLng} allowCurrentLocation={false} manualHint="Можно указать адрес текстом или выбрать точку на карте" />
          <MapPointPicker lang="ru" triggerLabel="Выбрать точку назначения на карте" title="Точка назначения" confirmLabel="Подтвердить" cancelLabel="Отмена" initialLat={destinationLatNum} initialLng={destinationLngNum} onConfirm={(payload) => { setDestination(payload?.address ?? ''); setDestinationLat(payload?.lat ?? ''); setDestinationLng(payload?.lng ?? ''); }} />

          <div className="grid grid-2">
            <div className="card-soft">
              <strong>{recommendedPrice} {tariff.currency}</strong>
              <p className="subtitle">{t('ru', 'recommendedPrice')} · ~{tariff.pricePerKm} {tariff.currency}/km</p>
              {estimatedDistance != null ? <p className="subtitle">{t('ru', 'distance')}: {estimatedDistance.toFixed(1)} km</p> : null}
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
          <button className="button" type="submit" disabled={loading}>{loading ? 'Создаём...' : t('ru', 'createOrder')}</button>
        </form>
      </section>

      {created ? (
        <section className="card stack">
          <h2 className="title" style={{ fontSize: 22 }}>Ищем водителя{searchDots(secondsPassed)}</h2>
          <p className="subtitle">{t('ru', 'searchStarted')}</p>
          <div className="info-grid">
            <div className="card-soft"><strong>{driversSeen}</strong><p className="subtitle">{t('ru', 'driversSeen')}</p></div>
            <div className="card-soft"><strong>{created?.status}</strong><p className="subtitle">{t('ru', 'status')}</p></div>
            <div className="card-soft"><strong>{created?.passenger_price} {created?.currency}</strong><p className="subtitle">{t('ru', 'yourPrice')}</p></div>
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