'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { RefreshCw } from 'lucide-react';
import { acceptCityOrder, createCityCounteroffer, listAvailableCityOrders } from '@/lib/api';
import type { CityOrder } from '@/lib/types';
import { OrderCard } from '@/components/OrderCard';

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
      setError(err instanceof Error ? err.message : 'Ошибка загрузки');
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
      setError(err instanceof Error ? err.message : 'Ошибка принятия');
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
      setError(err instanceof Error ? err.message : 'Ошибка отправки цены');
    } finally {
      setActionId(null);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <main className="shell stack">
      <section className="card sticky top-3 z-10 backdrop-blur">
        <div className="row">
          <div>
            <p className="mb-1 text-[10px] font-black uppercase tracking-[0.2em] text-brand-yellow">Driver live feed</p>
            <h1 className="title">Доступные заказы</h1>
            <p className="subtitle mt-1">Выберите цену пассажира или отправьте встречное предложение.</p>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={load} disabled={loading}>
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {error ? <p className="error mt-4">{error}</p> : null}
      </section>

      {loading ? (
        <section className="card text-center">
          <p className="subtitle">Загрузка эфира...</p>
        </section>
      ) : null}

      {!loading && orders.length === 0 ? (
        <section className="card text-center">
          <p className="text-lg font-black text-slate-950">Пока нет заказов в вашем радиусе</p>
          <p className="subtitle mt-2">Нажмите обновить или вернитесь позже.</p>
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
    </main>
  );
}
