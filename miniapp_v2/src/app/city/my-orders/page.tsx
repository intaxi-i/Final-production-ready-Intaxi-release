'use client';

import { useEffect, useState } from 'react';
import { listMyCityOrders } from '@/lib/api';
import type { CityOrder } from '@/lib/types';
import { OrderCard } from '@/components/OrderCard';

export default function MyCityOrdersPage() {
  const [orders, setOrders] = useState<CityOrder[]>([]);
  const [loading, setLoading] = useState(true);
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

  useEffect(() => {
    load();
  }, []);

  return (
    <main className="shell stack">
      <section className="card stack">
        <div className="row">
          <div>
            <h1 className="title">Мои city-заказы</h1>
            <p className="subtitle">Пассажир видит свои активные и прошлые заявки из Backend V2.</p>
          </div>
          <button className="button secondary" type="button" onClick={load} disabled={loading}>Обновить</button>
        </div>
        {error ? <p className="error">{error}</p> : null}
      </section>

      {loading ? <p className="subtitle">Загрузка...</p> : null}
      {!loading && orders.length === 0 ? <p className="subtitle">Заказов пока нет.</p> : null}
      <section className="grid grid-2">
        {orders.map((order) => <OrderCard key={order.id} order={order} />)}
      </section>
    </main>
  );
}
