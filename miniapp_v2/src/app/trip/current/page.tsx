'use client';

import { useEffect, useState } from 'react';
import { Globe2, RefreshCw } from 'lucide-react';
import {
  getCurrentCityTrip,
  getCurrentIntercityTrip,
  getDriverPaymentMethodsForTrip,
  getMe,
  updateCityTripStatus,
  updateIntercityTripStatus,
} from '@/lib/api';
import type { CityTrip, DriverPaymentMethod, IntercityTrip, UserMe } from '@/lib/types';
import { TripCard } from '@/components/TripCard';
import { t } from '@/lib/i18n';

const PAYMENT_METHOD_LABELS: Record<string, string> = {
  card: 'Карта',
  bank_transfer: 'Банковский перевод',
  cash: 'Наличные',
  crypto: 'Криптовалюта',
};

function statusLabel(lang: string | undefined | null, value?: string | null, driverView = false) {
  if (value === 'accepted') return t(lang, driverView ? 'driverFoundDriver' : 'driverFoundPassenger');
  if (value === 'driver_on_way') return t(lang, driverView ? 'driverOnWayDriver' : 'driverOnWayPassenger');
  if (value === 'driver_arrived') return t(lang, driverView ? 'driverArrivedDriver' : 'driverArrivedPassenger');
  if (value === 'in_progress') return t(lang, driverView ? 'tripInProgressDriver' : 'tripInProgressPassenger');
  if (value === 'completed') return t(lang, 'completedStatus');
  if (value === 'cancelled') return t(lang, 'cancelledStatus');
  return t(lang, 'unknownStatus');
}

function sourceLabel(lang: string | undefined | null, value?: string | null) {
  const normalized = String(value || '').toLowerCase();
  if (normalized.includes('request')) return t(lang, 'requestKind');
  if (normalized.includes('route')) return t(lang, 'routeKind');
  return t(lang, 'unknownStatus');
}

function modeLabel(lang: string | undefined | null, value?: string | null) {
  if (value === 'regular') return t(lang, 'regularMode');
  if (value === 'women') return t(lang, 'womenMode');
  return t(lang, 'unknownMode');
}

function paymentMethodLabel(value?: string | null) {
  return value ? PAYMENT_METHOD_LABELS[value] || value : '';
}

function isTripDriver(me: UserMe | null, trip?: { driver_user_id?: number | null } | null) {
  return Boolean(me?.id && trip?.driver_user_id && me.id === trip.driver_user_id);
}

function isTripPassenger(me: UserMe | null, trip?: { passenger_user_id?: number | null } | null) {
  return Boolean(me?.id && trip?.passenger_user_id && me.id === trip.passenger_user_id);
}

export default function CurrentTripPage() {
  const [me, setMe] = useState<UserMe | null>(null);
  const [cityTrip, setCityTrip] = useState<CityTrip | null>(null);
  const [intercityTrip, setIntercityTrip] = useState<IntercityTrip | null>(null);
  const [paymentMethods, setPaymentMethods] = useState<DriverPaymentMethod[]>([]);
  const [showPayment, setShowPayment] = useState(false);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const [user, city, intercity] = await Promise.all([
        getMe().catch(() => null),
        getCurrentCityTrip().catch(() => null),
        getCurrentIntercityTrip().catch(() => null),
      ]);
      setMe(user);
      setCityTrip(city);
      setIntercityTrip(intercity);
      setShowPayment(false);
      setPaymentMethods([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : t(me?.language, 'operationFailed'));
    } finally {
      setLoading(false);
    }
  }

  async function changeCityStatus(status: string) {
    if (!cityTrip || !isTripDriver(me, cityTrip)) return;
    setAction(true);
    setError(null);
    try {
      setCityTrip(await updateCityTripStatus(cityTrip.id, status));
    } catch (err) {
      setError(err instanceof Error ? err.message : t(me?.language, 'changeStatusFailed'));
    } finally {
      setAction(false);
    }
  }

  async function changeIntercityStatus(status: string) {
    if (!intercityTrip || !isTripDriver(me, intercityTrip)) return;
    setAction(true);
    setError(null);
    try {
      setIntercityTrip(await updateIntercityTripStatus(intercityTrip.id, status, intercityTrip.source_type));
    } catch (err) {
      setError(err instanceof Error ? err.message : t(me?.language, 'changeStatusFailed'));
    } finally {
      setAction(false);
    }
  }

  async function loadPaymentMethods() {
    if (!cityTrip || !isTripPassenger(me, cityTrip)) return;
    setAction(true);
    setError(null);
    try {
      setPaymentMethods(await getDriverPaymentMethodsForTrip(cityTrip.id));
      setShowPayment(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t(me?.language, 'operationFailed'));
    } finally {
      setAction(false);
    }
  }

  useEffect(() => { load(); }, []);

  const lang = me?.language;
  const canControlCityTrip = isTripDriver(me, cityTrip);
  const canPayCityDriver = isTripPassenger(me, cityTrip);
  const canControlIntercityTrip = isTripDriver(me, intercityTrip);
  const cityViewerRole = canControlCityTrip ? 'driver' : canPayCityDriver ? 'passenger' : 'unknown';

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div className="min-w-0">
            <p className="metric-label">{cityTrip ? t(lang, 'cityTrip') : t(lang, 'intercity')}</p>
            <h1 className="title break-words">{t(lang, 'currentTrip')}</h1>
            <p className="subtitle mt-2 break-words">{t(lang, 'activeTrip')}</p>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={load} disabled={loading} aria-label={t(lang, 'refreshLocation')}>
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {error ? <p className="error mt-4 break-words">{error}</p> : null}
      </section>

      {loading ? <section className="card"><p className="subtitle">{t(lang, 'loading')}</p></section> : null}
      {!loading && !cityTrip && !intercityTrip ? <section className="card"><p className="subtitle">{t(lang, 'noData')}</p></section> : null}

      {cityTrip ? (
        <>
          <TripCard trip={cityTrip} onStatus={changeCityStatus} disabled={action} canControl={canControlCityTrip} viewerRole={cityViewerRole} lang={lang} />
          {canPayCityDriver ? (
            <section className="card stack min-w-0 overflow-hidden">
              <div className="min-w-0">
                <h2 className="title break-words" style={{ fontSize: 22 }}>{t(lang, 'paymentMethods')}</h2>
                <p className="subtitle break-words">{t(lang, 'createdOrderHint')}</p>
              </div>
              <button className="button secondary" type="button" onClick={loadPaymentMethods} disabled={action}>{t(lang, 'paymentMethods')}</button>
              {showPayment ? (
                <div className="grid grid-2">
                  {paymentMethods.length === 0 ? <p className="subtitle">{t(lang, 'noData')}</p> : null}
                  {paymentMethods.map((method) => (
                    <div className="card-soft min-w-0 overflow-hidden" key={method.id}>
                      <strong className="break-words">{paymentMethodLabel(method.method_type)}</strong>
                      <p className="subtitle break-words">{method.card_number_masked || ''}</p>
                      <p className="subtitle break-words">{method.card_holder_name || ''}</p>
                      <p className="subtitle break-words">{method.bank_name || ''}</p>
                    </div>
                  ))}
                </div>
              ) : null}
            </section>
          ) : null}
        </>
      ) : null}

      {intercityTrip ? (
        <section className="order-card min-w-0 overflow-hidden">
          <div className="order-card-inner stack min-w-0">
            <div className="order-topline min-w-0 gap-2">
              <span className="order-badge min-w-0 max-w-full truncate">{t(lang, 'intercity')} · №{intercityTrip.id}</span>
              <span className="order-badge shrink-0 bg-brand-yellow text-brand-dark">{statusLabel(lang, intercityTrip.status, canControlIntercityTrip)}</span>
            </div>
            <div className="row rounded-3xl bg-slate-50 p-4">
              <div className="min-w-0">
                <p className="metric-label">{t(lang, 'price')}</p>
                <h2 className="title break-words" style={{ fontSize: 28 }}>{Math.round(intercityTrip.final_price).toLocaleString('ru-RU')} {intercityTrip.currency}</h2>
                <p className="subtitle mt-1 break-words">{sourceLabel(lang, intercityTrip.source_type)}</p>
              </div>
              <Globe2 className="shrink-0 text-brand-yellow" />
            </div>
            <div className="metric-grid">
              <div className="metric-card min-w-0 overflow-hidden"><div className="metric-label">{t(lang, 'status')}</div><div className="metric-value break-words">{statusLabel(lang, intercityTrip.status, canControlIntercityTrip)}</div></div>
              <div className="metric-card min-w-0 overflow-hidden"><div className="metric-label">{t(lang, 'route')}</div><div className="metric-value break-words">{sourceLabel(lang, intercityTrip.source_type)}</div></div>
              <div className="metric-card min-w-0 overflow-hidden"><div className="metric-label">{t(lang, 'passengerMode')}</div><div className="metric-value break-words">{modeLabel(lang, intercityTrip.mode)}</div></div>
              <div className="metric-card min-w-0 overflow-hidden"><div className="metric-label">{t(lang, 'order')}</div><div className="metric-value break-words">#{intercityTrip.id}</div></div>
            </div>
            {canControlIntercityTrip ? (
              <div className="grid grid-2">
                <button className="button secondary" type="button" disabled={action} onClick={() => changeIntercityStatus('in_progress')}>{t(lang, 'tripInProgressDriver')}</button>
                <button className="button primary" type="button" disabled={action} onClick={() => changeIntercityStatus('completed')}>{t(lang, 'completedStatus')}</button>
                <button className="button danger" type="button" disabled={action} onClick={() => changeIntercityStatus('cancelled')}>{t(lang, 'cancelledStatus')}</button>
              </div>
            ) : null}
          </div>
        </section>
      ) : null}
    </main>
  );
}
