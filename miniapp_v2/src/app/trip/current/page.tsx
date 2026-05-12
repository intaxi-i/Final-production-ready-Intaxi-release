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

const STATUS_LABELS: Record<string, string> = {
  accepted: 'Принято',
  driver_on_way: 'Водитель едет',
  driver_arrived: 'Водитель прибыл',
  in_progress: 'В пути',
  completed: 'Завершено',
  cancelled: 'Отменено',
};

const SOURCE_LABELS: Record<string, string> = {
  request: 'Заявка пассажира',
  route: 'Маршрут водителя',
};

const MODE_LABELS: Record<string, string> = {
  regular: 'Обычный',
  women: 'Женский',
};

const PAYMENT_METHOD_LABELS: Record<string, string> = {
  card: 'Карта',
  bank_transfer: 'Банковский перевод',
  cash: 'Наличные',
  crypto: 'Криптовалюта',
};

function statusLabel(value?: string | null) {
  return value ? STATUS_LABELS[value] || 'Неизвестный статус' : 'Неизвестный статус';
}

function sourceLabel(value?: string | null) {
  return value ? SOURCE_LABELS[value] || 'Неизвестный источник' : 'Неизвестный источник';
}

function modeLabel(value?: string | null) {
  return value ? MODE_LABELS[value] || 'Неизвестный режим' : 'Неизвестный режим';
}

function paymentMethodLabel(value?: string | null) {
  return value ? PAYMENT_METHOD_LABELS[value] || 'Неизвестный способ' : 'Неизвестный способ';
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
      setError(err instanceof Error ? err.message : 'Не удалось загрузить поездку');
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
      setError(err instanceof Error ? err.message : 'Не удалось изменить статус');
    } finally {
      setAction(false);
    }
  }

  async function changeIntercityStatus(status: string) {
    if (!intercityTrip || !isTripDriver(me, intercityTrip)) return;
    setAction(true);
    setError(null);
    try {
      setIntercityTrip(await updateIntercityTripStatus(intercityTrip.id, status));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось изменить статус');
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
      setError(err instanceof Error ? err.message : 'Реквизиты пока недоступны');
    } finally {
      setAction(false);
    }
  }

  useEffect(() => { load(); }, []);

  const canControlCityTrip = isTripDriver(me, cityTrip);
  const canPayCityDriver = isTripPassenger(me, cityTrip);
  const canControlIntercityTrip = isTripDriver(me, intercityTrip);

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">Поездка</p>
            <h1 className="title">Текущая поездка</h1>
            <p className="subtitle mt-2">Активные городские и межгородские поездки.</p>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={load} disabled={loading} aria-label="Обновить">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {error ? <p className="error mt-4">{error}</p> : null}
      </section>

      {loading ? <section className="card"><p className="subtitle">Загрузка...</p></section> : null}
      {!loading && !cityTrip && !intercityTrip ? <section className="card"><p className="subtitle">Активной поездки нет.</p></section> : null}

      {cityTrip ? (
        <>
          <TripCard trip={cityTrip} onStatus={changeCityStatus} disabled={action} canControl={canControlCityTrip} />
          {canPayCityDriver ? (
            <section className="card stack">
              <div>
                <h2 className="title" style={{ fontSize: 22 }}>Оплата водителю</h2>
                <p className="subtitle">Реквизиты доступны только участникам поездки.</p>
              </div>
              <button className="button secondary" type="button" onClick={loadPaymentMethods} disabled={action}>Показать реквизиты водителя</button>
              {showPayment ? (
                <div className="grid grid-2">
                  {paymentMethods.length === 0 ? <p className="subtitle">Водитель ещё не добавил реквизиты.</p> : null}
                  {paymentMethods.map((method) => (
                    <div className="card-soft" key={method.id}>
                      <strong>{paymentMethodLabel(method.method_type)}</strong>
                      <p className="subtitle">Карта: {method.card_number_masked || 'не указана'}</p>
                      <p className="subtitle">Владелец: {method.card_holder_name || 'не указан'}</p>
                      <p className="subtitle">Банк: {method.bank_name || 'не указан'}</p>
                    </div>
                  ))}
                </div>
              ) : null}
            </section>
          ) : null}
        </>
      ) : null}

      {intercityTrip ? (
        <section className="order-card">
          <div className="order-card-inner stack">
            <div className="order-topline">
              <span className="order-badge">Межгород · №{intercityTrip.id}</span>
              <span className="order-badge bg-brand-yellow text-brand-dark">{statusLabel(intercityTrip.status)}</span>
            </div>
            <div className="row rounded-3xl bg-slate-50 p-4">
              <div>
                <p className="metric-label">Цена</p>
                <h2 className="title" style={{ fontSize: 28 }}>{Math.round(intercityTrip.final_price).toLocaleString('ru-RU')} {intercityTrip.currency}</h2>
                <p className="subtitle mt-1">{sourceLabel(intercityTrip.source_type)}</p>
              </div>
              <Globe2 className="text-brand-yellow" />
            </div>
            <div className="metric-grid">
              <div className="metric-card"><div className="metric-label">Статус</div><div className="metric-value">{statusLabel(intercityTrip.status)}</div></div>
              <div className="metric-card"><div className="metric-label">Источник</div><div className="metric-value">{sourceLabel(intercityTrip.source_type)}</div></div>
              <div className="metric-card"><div className="metric-label">Режим</div><div className="metric-value">{modeLabel(intercityTrip.mode)}</div></div>
              <div className="metric-card"><div className="metric-label">Поездка</div><div className="metric-value">#{intercityTrip.id}</div></div>
            </div>
            {canControlIntercityTrip ? (
              <div className="grid grid-2">
                <button className="button secondary" type="button" disabled={action} onClick={() => changeIntercityStatus('driver_on_way')}>Выехал</button>
                <button className="button secondary" type="button" disabled={action} onClick={() => changeIntercityStatus('in_progress')}>В пути</button>
                <button className="button primary" type="button" disabled={action} onClick={() => changeIntercityStatus('completed')}>Завершить</button>
                <button className="button danger" type="button" disabled={action} onClick={() => changeIntercityStatus('cancelled')}>Отменить</button>
              </div>
            ) : null}
          </div>
        </section>
      ) : null}
    </main>
  );
}
