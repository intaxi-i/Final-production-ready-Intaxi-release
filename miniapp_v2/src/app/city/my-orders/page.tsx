'use client';

import { useEffect, useState } from 'react';
import { cancelCityOrder, listMyCityOrders, raiseCityOrderPrice } from '@/lib/api';
import type { CityOrder } from '@/lib/types';
import { OrderCard } from '@/components/OrderCard';

export default function MyCityOrdersPage() {
  const [orders, setOrders] = useState<CityOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      setOrders(await listMyCityOrders());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить мои заказы');
    } finally {
      setLoading(false);
    }
  }

  async function raise(order: CityOrder) {
    setActionId(order.id);
    setError(null);
    try {
      await raiseCityOrderPrice(order.id, Math.round(order.passenger_price * 1.1));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось поднять цену');
    } finally {
      setActionId(null);
    }
  }

  async function cancel(order: CityOrder) {
    setActionId(order.id);
    setError(null);
    try {
      await cancelCityOrder(order.id, 'cancelled_by_passenger');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отменить заказ');
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
            <h1 className="title">Мои city-заказы</h1>
            <p className="subtitle">Пассажир видит свои заявки, может поднять цену или отменить активный заказ.</p>
          </div>
          <button className="button secondary" type="button" onClick={load} disabled={loading}>Обновить</button>
        </div>
        {error ? <p className="error">{error}</p> : null}
      </section>

      {loading ? <p className="subtitle">Загрузка...</p> : null}
      {!loading && orders.length === 0 ? <p className="subtitle">Заказов пока нет.</p> : null}
      <section className="grid grid-2">
        {orders.map((order) => (
          <div className="stack" key={order.id}>
            <OrderCard order={order} />
            {order.status === 'active' ? (
              <div className="actions">
                <button className="button secondary" type="button" disabled={actionId === order.id} onClick={() => raise(order)}>
                  Поднять цену на 10%
                </button>
                <button className="button danger" type="button" disabled={actionId === order.id} onClick={() => cancel(order)}>
                  Отменить
                </button>
              </div>
            ) : null}
          </div>
        ))}
      </section>
    </main>
  );
}
