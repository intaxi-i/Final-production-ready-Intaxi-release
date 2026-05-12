'use client';

import { useEffect, useState } from 'react';
import { History, RefreshCw } from 'lucide-react';
import { cancelCityOrder, listMyCityOrders, raiseCityOrderPrice } from '@/lib/api';
import type { CityOrder } from '@/lib/types';
import { OrderCard } from '@/components/OrderCard';
import { BottomNav } from '@/components/BottomNav';

function roundPassengerRaise(value: number, currency: string) {
  if (currency === 'UZS') return Math.round((value * 1.1) / 1000) * 1000;
  if (currency === 'KZT') return Math.round((value * 1.1) / 100) * 100;
  return Math.round(value * 1.1);
}

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
      await raiseCityOrderPrice(order.id, roundPassengerRaise(order.passenger_price, order.currency));
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

  useEffect(() => { load(); }, []);

  const activeCount = orders.filter((order) => ['search', 'active'].includes(order.status)).length;

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">Пассажир</p>
            <h1 className="title">Мои заказы</h1>
            <p className="subtitle mt-2">История городских заявок, активные заказы и быстрые действия по цене.</p>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={load} disabled={loading} aria-label="Обновить">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {error ? <p className="error mt-4">{error}</p> : null}
      </section>

      <section className="metric-grid">
        <div className="metric-card"><div className="metric-label">Всего</div><div className="metric-value">{orders.length}</div></div>
        <div className="metric-card"><div className="metric-label">Активных</div><div className="metric-value">{activeCount}</div></div>
      </section>

      {loading ? <section className="card"><p className="subtitle">Загрузка...</p></section> : null}
      {!loading && orders.length === 0 ? (
        <section className="card stack text-center">
          <History className="mx-auto text-brand-yellow" size={34} />
          <p className="subtitle">Заказов пока нет. Создайте городскую поездку, чтобы она появилась здесь.</p>
        </section>
      ) : null}

      <section className="grid grid-2">
        {orders.map((order) => (
          <div className="stack" key={order.id}>
            <OrderCard order={order} />
            {['search', 'active'].includes(order.status) ? (
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
      <BottomNav />
    </main>
  );
}
