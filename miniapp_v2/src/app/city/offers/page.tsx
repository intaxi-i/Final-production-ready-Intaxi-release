'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Radio, RefreshCw, ShieldAlert } from 'lucide-react';
import { acceptCityOrder, createCityCounteroffer, getMe, listAvailableCityOrders } from '@/lib/api';
import { getDriverProfile } from '@/lib/api-extra';
import type { CityOrder, DriverProfile, UserMe } from '@/lib/types';
import { OrderCard } from '@/components/OrderCard';
import { BottomNav } from '@/components/BottomNav';

function isConfirmedDriver(profile: DriverProfile | null) {
  if (!profile?.status) return false;
  return ['approved', 'verified', 'active'].includes(profile.status.toLowerCase());
}

export default function CityOffersPage() {
  const [orders, setOrders] = useState<CityOrder[]>([]);
  const [me, setMe] = useState<UserMe | null>(null);
  const [profile, setProfile] = useState<DriverProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const confirmedDriver = me?.active_role === 'driver' && isConfirmedDriver(profile);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const user = await getMe();
      setMe(user);
      const driverProfile = user.active_role === 'driver' ? await getDriverProfile().catch(() => null) : null;
      setProfile(driverProfile);

      if (user.active_role !== 'driver' || !isConfirmedDriver(driverProfile)) {
        setOrders([]);
        return;
      }

      setOrders(await listAvailableCityOrders());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить заказы');
    } finally {
      setLoading(false);
    }
  }

  async function accept(orderId: number) {
    if (!confirmedDriver) return;
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
    if (!confirmedDriver) return;
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

      {!loading && !confirmedDriver ? (
        <section className="card stack text-center">
          <ShieldAlert className="mx-auto text-brand-yellow" size={34} />
          <p className="text-lg font-black text-slate-950">Эфир доступен после проверки водителя</p>
          <p className="subtitle mt-2">Подайте заявку и дождитесь подтверждения. До этого городские заказы недоступны.</p>
          <Link href="/driver/register" className="button primary">Открыть заявку водителя</Link>
        </section>
      ) : null}

      {confirmedDriver ? (
        <section className="metric-grid">
          <div className="metric-card"><div className="metric-label">Доступно</div><div className="metric-value">{orders.length}</div></div>
          <div className="metric-card"><div className="metric-label">Эфир</div><div className="metric-value">Город</div></div>
        </section>
      ) : null}

      {loading ? (
        <section className="card text-center">
          <p className="subtitle">Загрузка эфира...</p>
        </section>
      ) : null}

      {!loading && confirmedDriver && orders.length === 0 ? (
        <section className="card stack text-center">
          <Radio className="mx-auto text-brand-yellow" size={34} />
          <p className="text-lg font-black text-slate-950">Пока нет заказов рядом</p>
          <p className="subtitle mt-2">Обновите эфир или проверьте, включён ли онлайн-статус водителя.</p>
        </section>
      ) : null}

      {!loading && confirmedDriver && orders.length > 0 ? (
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
