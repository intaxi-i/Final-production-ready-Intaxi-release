'use client';

import { useEffect, useState } from 'react';
import {
  getCurrentCityTrip,
  getDriverPaymentMethodsForTrip,
  updateCityTripStatus,
} from '@/lib/api';
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

  useEffect(() => {
    load();
  }, []);

  return (
    <main className="shell stack">
      <section className="card stack">
        <div className="row">
          <div>
            <h1 className="title">Текущая поездка</h1>
            <p className="subtitle">Статусы меняются только через Backend V2.</p>
          </div>
          <button className="button secondary" type="button" onClick={load} disabled={loading}>
            Обновить
          </button>
        </div>
        {error ? <p className="error">{error}</p> : null}
      </section>

      {loading ? <p className="subtitle">Загрузка...</p> : null}
      {!loading && !trip ? <p className="subtitle">Активной city-поездки нет.</p> : null}

      {trip ? (
        <>
          <TripCard trip={trip} onStatus={changeStatus} disabled={action} />
          <section className="card stack">
            <div>
              <h2 className="title" style={{ fontSize: 22 }}>Оплата водителю</h2>
              <p className="subtitle">
                На первом этапе пассажир платит напрямую водителю. Реквизиты доступны только участнику поездки.
              </p>
            </div>
            <button className="button secondary" type="button" onClick={loadPaymentMethods} disabled={action}>
              Показать реквизиты водителя
            </button>
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
