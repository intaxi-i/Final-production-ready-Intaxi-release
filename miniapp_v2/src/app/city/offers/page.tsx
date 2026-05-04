'use client';

import { useEffect, useState } from 'react';
import { acceptCityOrder, listAvailableCityOrders } from '@/lib/api';
import type { CityOrder } from '@/lib/types';
import { OrderCard } from '@/components/OrderCard';

export default function CityOffersPage() {
  const [orders, setOrders] = useState<CityOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      setOrders(await listAvailableCityOrders());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить заказы');
    } finally {
      setLoading(false);
    }
  }

  async function accept(orderId: number) {
    setActionId(orderId);
    setError(null);
    try {
      await acceptCityOrder(orderId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось принять заказ');
    } finally {
      setActionId(null);
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
            <h1 className="title">Доступные city-заказы</h1>
            <p className="subtitle">Backend V2 показывает только заказы, подходящие текущему водителю.</p>
          </div>
          <button className="button secondary" type="button" onClick={load} disabled={loading}>
            Обновить
          </button>
        </div>
        {error ? <p className="error">{error}</p> : null}
      </section>

      {loading ? <p className="subtitle">Загрузка...</p> : null}
      {!loading && orders.length === 0 ? <p className="subtitle">Пока нет доступных заказов.</p> : null}
      <section className="grid grid-2">
        {orders.map((order) => (
          <OrderCard
            key={order.id}
            order={order}
            actionLabel="Принять заказ"
            disabled={actionId === order.id}
            onAction={() => accept(order.id)}
          />
        ))}
      </section>
    </main>
  );
}
