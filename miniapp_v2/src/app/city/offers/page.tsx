'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Radio, RefreshCw } from 'lucide-react';
import { acceptCityOrder, createCityCounteroffer, listAvailableCityOrders } from '@/lib/api';
import type { CityOrder } from '@/lib/types';
import { OrderCard } from '@/components/OrderCard';
import { BottomNav } from '@/components/BottomNav';

export default function CityOffersPage() {
  const [orders, setOrders] = useState<CityOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

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
      router.push('/trip/current');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось принять заказ');
      setActionId(null);
    }
  }

  async function counterOffer(orderId: number, price: number) {
    setActionId(orderId);
    setError(null);
    try {
      await createCityCounteroffer(orderId, price);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отправить цену');
    } finally {
      setActionId(null);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">Водитель</p>
            <h1 className="title">Эфир заказов</h1>
            <p className="subtitle mt-2">Принимайте цену пассажира или отправляйте встречное предложение.</p>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={load} disabled={loading} aria-label="Обновить">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {error ? <p className="error mt-4">{error}</p> : null}
      </section>

      <section className="metric-grid">
        <div className="metric-card"><div className="metric-label">Доступно</div><div className="metric-value">{orders.length}</div></div>
        <div className="metric-card"><div className="metric-label">Эфир</div><div className="metric-value">Город</div></div>
      </section>

      {loading ? (
        <section className="card text-center">
          <p className="subtitle">Загрузка эфира...</p>
        </section>
      ) : null}

      {!loading && orders.length === 0 ? (
        <section className="card stack text-center">
          <Radio className="mx-auto text-brand-yellow" size={34} />
          <p className="text-lg font-black text-slate-950">Пока нет заказов рядом</p>
          <p className="subtitle mt-2">Обновите эфир или проверьте, включён ли онлайн-статус водителя.</p>
        </section>
      ) : null}

      {!loading && orders.length > 0 ? (
        <section className="stack">
          {orders.map((order) => (
            <OrderCard
              key={order.id}
              order={order}
              actionLabel="Принять"
              disabled={actionId === order.id}
              onAction={() => accept(order.id)}
              onCounterOffer={(price: number) => counterOffer(order.id, price)}
            />
          ))}
        </section>
      ) : null}
      <BottomNav />
    </main>
  );
}
