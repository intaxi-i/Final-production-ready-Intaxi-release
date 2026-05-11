'use client';

import { useEffect, useState } from 'react';
import { Globe2, RefreshCw } from 'lucide-react';
import {
  getCurrentCityTrip,
  getCurrentIntercityTrip,
  getDriverPaymentMethodsForTrip,
  updateCityTripStatus,
  updateIntercityTripStatus,
} from '@/lib/api';
import type { CityTrip, DriverPaymentMethod, IntercityTrip } from '@/lib/types';
import { TripCard } from '@/components/TripCard';

export default function CurrentTripPage() {
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
      const [city, intercity] = await Promise.all([
        getCurrentCityTrip().catch(() => null),
        getCurrentIntercityTrip().catch(() => null),
      ]);
      setCityTrip(city);
      setIntercityTrip(intercity);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить поездку');
    } finally {
      setLoading(false);
    }
  }

  async function changeCityStatus(status: string) {
    if (!cityTrip) return;
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
    if (!intercityTrip) return;
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
    if (!cityTrip) return;
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
          <TripCard trip={cityTrip} onStatus={changeCityStatus} disabled={action} />
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
                    <strong>{method.method_type}</strong>
                    <p className="subtitle">Карта: {method.card_number_masked || 'не указана'}</p>
                    <p className="subtitle">Владелец: {method.card_holder_name || 'не указан'}</p>
                    <p className="subtitle">Банк: {method.bank_name || 'не указан'}</p>
                  </div>
                ))}
              </div>
            ) : null}
          </section>
        </>
      ) : null}

      {intercityTrip ? (
        <section className="order-card">
          <div className="order-card-inner stack">
            <div className="order-topline">
              <span className="order-badge">Межгород · №{intercityTrip.id}</span>
              <Globe2 className="text-brand-yellow" />
            </div>
            <div className="metric-grid">
              <div className="metric-card"><div className="metric-label">Цена</div><div className="metric-value">{Math.round(intercityTrip.final_price).toLocaleString('ru-RU')} {intercityTrip.currency}</div></div>
              <div className="metric-card"><div className="metric-label">Статус</div><div className="metric-value">{intercityTrip.status}</div></div>
              <div className="metric-card"><div className="metric-label">Источник</div><div className="metric-value">{intercityTrip.source_type}</div></div>
              <div className="metric-card"><div className="metric-label">Режим</div><div className="metric-value">{intercityTrip.mode === 'women' ? 'Женский' : 'Обычный'}</div></div>
            </div>
            <div className="grid grid-2">
              <button className="button secondary" type="button" disabled={action} onClick={() => changeIntercityStatus('driver_on_way')}>Выехал</button>
              <button className="button secondary" type="button" disabled={action} onClick={() => changeIntercityStatus('in_progress')}>В пути</button>
              <button className="button primary" type="button" disabled={action} onClick={() => changeIntercityStatus('completed')}>Завершить</button>
              <button className="button secondary" type="button" disabled={action} onClick={() => changeIntercityStatus('cancelled')}>Отменить</button>
            </div>
          </div>
        </section>
      ) : null}
    </main>
  );
}
