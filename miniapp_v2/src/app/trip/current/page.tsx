'use client';

import { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { getCurrentCityTrip, getDriverPaymentMethodsForTrip, updateCityTripStatus } from '@/lib/api';
import type { CityTrip, DriverPaymentMethod } from '@/lib/types';
import { TripCard } from '@/components/TripCard';

export default function CurrentTripPage() {
  const [trip, setTrip] = useState<CityTrip | null>(null);
  const [paymentMethods, setPaymentMethods] = useState<DriverPaymentMethod[]>([]);
  const [showPayment, setShowPayment] = useState(false);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      setTrip(await getCurrentCityTrip());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить поездку');
    } finally {
      setLoading(false);
    }
  }

  async function changeStatus(status: string) {
    if (!trip) return;
    setAction(true);
    setError(null);
    try {
      setTrip(await updateCityTripStatus(trip.id, status));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось изменить статус');
    } finally {
      setAction(false);
    }
  }

  async function loadPaymentMethods() {
    if (!trip) return;
    setAction(true);
    setError(null);
    try {
      setPaymentMethods(await getDriverPaymentMethodsForTrip(trip.id));
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
            <p className="subtitle mt-2">Здесь появится активный городской заказ после принятия водителем.</p>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={load} disabled={loading} aria-label="Обновить">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {error ? <p className="error mt-4">{error}</p> : null}
      </section>

      {loading ? <section className="card"><p className="subtitle">Загрузка...</p></section> : null}
      {!loading && !trip ? <section className="card"><p className="subtitle">Активной поездки нет.</p></section> : null}

      {trip ? (
        <>
          <TripCard trip={trip} onStatus={changeStatus} disabled={action} />
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
    </main>
  );
}
