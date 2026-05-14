'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { AddressField } from '@/components/AddressField';
import { MapPointPicker } from '@/components/MapPointPicker';
import { ModeToggle } from '@/components/ModeToggle';
import { OrderCard } from '@/components/OrderCard';
import { APP_ROUTES } from '@/lib/constants';
import { createCityOrder, getMe, listMyCityOrders, raiseCityOrderPrice } from '@/lib/api';
import { haversineKm } from '@/lib/geo';
import { t } from '@/lib/i18n';
import type { CityOrder, RideMode, UserMe } from '@/lib/types';

const FALLBACK_PRICE_PER_KM: Record<string, { currency: string; pricePerKm: number; minPrice: number }> = {
  uz: { currency: 'UZS', pricePerKm: 2500, minPrice: 10000 },
  tr: { currency: 'TRY', pricePerKm: 45, minPrice: 60 },
  kz: { currency: 'KZT', pricePerKm: 120, minPrice: 800 },
  sa: { currency: 'SAR', pricePerKm: 2.5, minPrice: 15 },
};

function searchDots(seconds: number) {
  return '.'.repeat((seconds % 3) + 1);
}

function parseCoordinate(value: string): number | null {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function roundPrice(value: number, country: string) {
  if (country === 'uz') return Math.round(value / 1000) * 1000;
  if (country === 'kz') return Math.round(value / 100) * 100;
  return Math.round(value);
}

function formatMoney(value: number, currency: string) {
  return `${Math.round(value).toLocaleString('ru-RU')} ${currency}`;
}

function hasPoint(address: string, lat: string, lng: string) {
  return Boolean(address.trim()) && parseCoordinate(lat) != null && parseCoordinate(lng) != null;
}

export default function CityCreatePage() {
  const [me, setMe] = useState<UserMe | null>(null);
  const [mode, setMode] = useState<RideMode>('regular');
  const [country, setCountry] = useState('uz');
  const [pickup, setPickup] = useState('');
  const [pickupLat, setPickupLat] = useState('');
  const [pickupLng, setPickupLng] = useState('');
  const [destination, setDestination] = useState('');
  const [destinationLat, setDestinationLat] = useState('');
  const [destinationLng, setDestinationLng] = useState('');
  const [price, setPrice] = useState('');
  const [seats, setSeats] = useState('1');
  const [comment, setComment] = useState('');
  const [routeOpen, setRouteOpen] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [commentOpen, setCommentOpen] = useState(false);
  const [created, setCreated] = useState<CityOrder | null>(null);
  const [driversSeen, setDriversSeen] = useState(0);
  const [secondsPassed, setSecondsPassed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const lang = me?.language;

  const tariff = FALLBACK_PRICE_PER_KM[country] || FALLBACK_PRICE_PER_KM.uz;
  const pickupLatNum = parseCoordinate(pickupLat);
  const pickupLngNum = parseCoordinate(pickupLng);
  const destinationLatNum = parseCoordinate(destinationLat);
  const destinationLngNum = parseCoordinate(destinationLng);
  const routeReady = hasPoint(pickup, pickupLat, pickupLng) && hasPoint(destination, destinationLat, destinationLng);

  const estimatedDistance = useMemo(() => {
    if (pickupLatNum == null || pickupLngNum == null || destinationLatNum == null || destinationLngNum == null) return null;
    return haversineKm(pickupLatNum, pickupLngNum, destinationLatNum, destinationLngNum);
  }, [pickupLatNum, pickupLngNum, destinationLatNum, destinationLngNum]);

  const recommendedPrice = useMemo(() => {
    if (estimatedDistance == null) return tariff.minPrice;
    return Math.max(roundPrice(estimatedDistance * tariff.pricePerKm, country), tariff.minPrice);
  }, [country, estimatedDistance, tariff.minPrice, tariff.pricePerKm]);

  function createdStatusLabel(value?: string | null) {
    if (value === 'search') return t(lang, 'searchStatus');
    if (value === 'active') return t(lang, 'activeStatus');
    if (value === 'accepted') return t(lang, 'acceptedStatus');
    if (value === 'finished' || value === 'completed') return t(lang, 'completedStatus');
    if (value === 'cancelled') return t(lang, 'cancelledStatus');
    return t(lang, 'unknownStatus');
  }

  useEffect(() => {
    void getMe().then(setMe).catch(() => null);
  }, []);

  useEffect(() => {
    if (routeReady && estimatedDistance != null) {
      setPrice((current) => current || String(recommendedPrice));
    }
  }, [estimatedDistance, recommendedPrice, routeReady]);

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

    if (!pickup.trim() || !destination.trim()) {
      setError(t(lang, 'routeRequired'));
      setRouteOpen(true);
      return;
    }

    if (!routeReady) {
      setError(t(lang, 'chooseAddressFromSuggestions'));
      setRouteOpen(true);
      return;
    }

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
        passenger_price: Math.round(Number(price || recommendedPrice)),
        comment: comment.trim() || null,
      });
      setCreated(order);
      setDriversSeen(order?.seen_by_drivers ?? 0);
      setSecondsPassed(0);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setError(err instanceof Error ? err?.message : t(lang, 'createOrderFailed'));
    } finally {
      setLoading(false);
    }
  }

  async function raisePrice() {
    if (!created?.id) return;
    const nextPrice = roundPrice(Number(price || created?.passenger_price || 0) * 1.1, country);
    setError(null);
    try {
      const next = await raiseCityOrderPrice(created.id, nextPrice);
      setCreated(next);
      setPrice(String(next?.passenger_price ?? 0));
      setMessage(t(lang, 'updatedSuccessfully'));
    } catch (err) {
      setError(err instanceof Error ? err?.message : t(lang, 'operationFailed'));
    }
  }

  if (created) {
    return (
      <main className={`shell stack with-bottom-nav ${mode === 'women' ? 'women-mode' : ''}`}>
        <section className="premium-hero">
          <div className="relative z-10">
            <p className="metric-label">{t(lang, 'orderCreated')}</p>
            <h1 className="title">{t(lang, 'searchingDriver')}{searchDots(secondsPassed)}</h1>
            <p className="subtitle mt-2">{t(lang, 'createdOrderHint')}</p>
          </div>
        </section>
        <section className="metric-grid">
          <div className="metric-card"><div className="metric-label">{t(lang, 'seen')}</div><div className="metric-value">{driversSeen}</div></div>
          <div className="metric-card"><div className="metric-label">{t(lang, 'status')}</div><div className="metric-value">{createdStatusLabel(created.status)}</div></div>
          <div className="metric-card"><div className="metric-label">{t(lang, 'price')}</div><div className="metric-value">{created.passenger_price} {created.currency}</div></div>
          <div className="metric-card"><div className="metric-label">{t(lang, 'time')}</div><div className="metric-value">{secondsPassed}s</div></div>
        </section>
        <OrderCard order={created} lang={lang} />
        <section className="card stack">
          {error ? <p className="error">{error}</p> : null}
          {message ? <p className="success">{message}</p> : null}
          {secondsPassed >= 30 ? <button className="button primary" type="button" onClick={raisePrice}>{t(lang, 'raisePrice')}</button> : <p className="subtitle">{t(lang, 'raisePriceHint')}</p>}
          <Link className="button secondary" href={APP_ROUTES.cityMyOrders}>{t(lang, 'openMyOrders')}</Link>
        </section>
      </main>
    );
  }

  return (
    <main className={`shell stack with-bottom-nav ${mode === 'women' ? 'women-mode' : ''}`}>
      <section className="premium-hero">
        <div className="relative z-10">
          <p className="metric-label">{t(lang, 'cityTrip')}</p>
          <h1 className="title">{t(lang, 'whereGo')}</h1>
          <p className="subtitle mt-2">{t(lang, 'cityCreateHint')}</p>
        </div>
      </section>
      <form className="stack" onSubmit={submit}>
        <section className="card stack">
          <button type="button" className="route-summary" onClick={() => setRouteOpen((prev) => !prev)}>
            <span><strong>{t(lang, 'route')}</strong><small>{routeReady ? `${pickup} → ${destination}` : t(lang, 'routeEmptyHint')}</small></span>
            {routeOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
          {routeOpen ? (
            <div className="stack">
              <AddressField lang={lang || 'ru'} label={t(lang, 'fromWhere')} address={pickup} setAddress={setPickup} lat={pickupLat} setLat={setPickupLat} lng={pickupLng} setLng={setPickupLng} countryCode={country} placeholder={t(lang, 'pickupPlaceholder')} onResolved={(payload) => { if (payload?.countryCode) setCountry(payload.countryCode); }} />
              <MapPointPicker lang={lang || 'ru'} triggerLabel={t(lang, 'pickPickupOnMap')} title={t(lang, 'pickupPoint')} confirmLabel={t(lang, 'confirmPoint')} cancelLabel={t(lang, 'cancel')} initialLat={pickupLatNum} initialLng={pickupLngNum} onConfirm={(payload) => { setPickup(payload?.address ?? ''); setPickupLat(payload?.lat ?? ''); setPickupLng(payload?.lng ?? ''); if (payload?.countryCode) setCountry(payload.countryCode); }} />
              <AddressField lang={lang || 'ru'} label={t(lang, 'toWhere')} address={destination} setAddress={setDestination} lat={destinationLat} setLat={setDestinationLat} lng={destinationLng} setLng={setDestinationLng} countryCode={country} allowCurrentLocation={false} placeholder={t(lang, 'destinationPlaceholder')} />
              <MapPointPicker lang={lang || 'ru'} triggerLabel={t(lang, 'pickDestinationOnMap')} title={t(lang, 'destinationPoint')} confirmLabel={t(lang, 'confirmPoint')} cancelLabel={t(lang, 'cancel')} initialLat={destinationLatNum || pickupLatNum} initialLng={destinationLngNum || pickupLngNum} onConfirm={(payload) => { setDestination(payload?.address ?? ''); setDestinationLat(payload?.lat ?? ''); setDestinationLng(payload?.lng ?? ''); }} />
            </div>
          ) : null}
        </section>
        {routeReady ? (
          <section className="card stack">
            <div><p className="metric-label">{t(lang, 'price')}</p><h2 className="title" style={{ fontSize: 24 }}>{t(lang, 'offerYourPrice')}</h2><p className="subtitle mt-1">{t(lang, 'priceHint')}</p></div>
            <button type="button" className="recommended-price" onClick={() => setPrice(String(recommendedPrice))}>
              <Sparkles size={18} /><span><strong>{formatMoney(recommendedPrice, tariff.currency)}</strong><small>{estimatedDistance != null ? `${t(lang, 'about')} ${estimatedDistance.toFixed(1)} km · ${t(lang, 'systemCalculation')}` : t(lang, 'systemCalculation')}</small></span><em>{t(lang, 'choose')}</em>
            </button>
            <label className="label">{t(lang, 'yourPrice')}<input className="input price-input" inputMode="numeric" value={price} onChange={(event) => setPrice(event.target.value)} placeholder={formatMoney(recommendedPrice, tariff.currency)} required /></label>
          </section>
        ) : null}
        <section className="card-soft stack">
          <button type="button" className="route-summary" onClick={() => setSettingsOpen((prev) => !prev)}><span><strong>{t(lang, 'additional')}</strong><small>{t(lang, 'additionalHint')}</small></span>{settingsOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}</button>
          {settingsOpen ? (
            <div className="stack">
              <div className="grid grid-2">
                <label className="label">{t(lang, 'country')}<input className="input" value={country.toUpperCase()} onChange={(event) => setCountry(event.target.value.toLowerCase().slice(0, 2))} placeholder="UZ" /></label>
                <label className="label">{t(lang, 'seats')}<input className="input" inputMode="numeric" min="1" value={seats} onChange={(event) => setSeats(event.target.value)} required /></label>
              </div>
              <ModeToggle value={mode} onChange={setMode} />
              <button type="button" className="button secondary" onClick={() => setCommentOpen((prev) => !prev)}>{commentOpen ? t(lang, 'hideComment') : t(lang, 'addComment')}</button>
              {commentOpen ? <label className="label">{t(lang, 'comment')}<textarea className="input" value={comment} onChange={(event) => setComment(event.target.value)} rows={3} placeholder={t(lang, 'commentPlaceholder')} /></label> : null}
            </div>
          ) : null}
        </section>
        {error ? <p className="error">{error}</p> : null}
        {message ? <p className="success">{message}</p> : null}
        <button className="button primary full-submit" type="submit" disabled={loading || !routeReady}>{loading ? t(lang, 'creating') : t(lang, 'confirmOrder')}</button>
      </form>
    </main>
  );
}
