'use client';
import { useEffect, useState } from 'react';
import { acceptCityOrder, listAvailableCityOrders, createCityCounteroffer } from '@/lib/api';
import type { CityOrder } from '@/lib/types';
import { OrderCard } from '@/components/OrderCard';
import { useRouter } from 'next/navigation';

export default function CityOffersPage() {
  const [orders, setOrders] = useState<CityOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function load() {
    setError(null); setLoading(true);
    try { setOrders(await listAvailableCityOrders()); } 
    catch (err) { setError(err instanceof Error ? err.message : 'Ошибка загрузки'); } 
    finally { setLoading(false); }
  }

  async function accept(orderId: number) {
    setActionId(orderId); setError(null);
    try { 
        await acceptCityOrder(orderId); 
        router.push('/trip/current');
    } catch (err) { 
        setError(err instanceof Error ? err.message : 'Ошибка принятия'); 
        setActionId(null); 
    }
  }

  async function counterOffer(orderId: number, price: number) {
    setActionId(orderId); setError(null);
    try {
        await createCityCounteroffer(orderId, price);
        await load(); // Перезагружаем список (заказ скроется, т.к. мы ждем ответа пассажира)
    } catch (err) {
        setError(err instanceof Error ? err.message : 'Ошибка отправки цены');
    } finally {
        setActionId(null);
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <main className="shell stack pb-24">
      <section className="card stack sticky top-0 z-10 shadow-sm">
        <div className="row">
          <div><h1 className="title">Доступные заказы</h1></div>
          <button className="button secondary text-sm px-4" type="button" onClick={load} disabled={loading}>Обновить</button>
        </div>
        {error ? <p className="error text-sm">{error}</p> : null}
      </section>
      
      {loading ? <p className="subtitle text-center mt-10">Загрузка эфира...</p> : null}
      {!loading && orders.length === 0 ? <p className="subtitle text-center mt-10">Пока нет заказов в вашем радиусе.</p> : null}
      
      <section className="grid grid-2 gap-4 mt-2">
        {orders.map((order) => (
          <OrderCard 
            key={order.id} 
            order={order} 
            actionLabel="Принять за эту цену" 
            disabled={actionId === order.id} 
            onAction={() => accept(order.id)} 
            onCounterOffer={(price: number) => counterOffer(order.id, price)} 
          />
        ))}
      </section>
    </main>
  );
}
