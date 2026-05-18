'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Radio, RefreshCw, ShieldAlert } from 'lucide-react';
import { acceptCityOrder, getMe, listAvailableCityOrders } from '@/lib/api';
import { getDriverProfile } from '@/lib/api-extra';
import type { CityOrder, DriverProfile, UserMe } from '@/lib/types';
import { OrderCard } from '@/components/OrderCard';
import { t } from '@/lib/i18n';

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

  const lang = me?.language;
  const confirmedDriver = me?.active_role === 'driver' && isConfirmedDriver(profile);

  async function load(silent = false) {
    setError(null);
    if (!silent) setLoading(true);
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
      setError(err instanceof Error ? err.message : t(lang, 'loadOrdersFailed'));
    } finally {
      if (!silent) setLoading(false);
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
      setError(err instanceof Error ? err.message : t(lang, 'acceptOrderFailed'));
      setActionId(null);
    }
  }

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(true), 5000);
    const onFocus = () => void load(true);
    window.addEventListener('focus', onFocus);
    document.addEventListener('visibilitychange', onFocus);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener('focus', onFocus);
      document.removeEventListener('visibilitychange', onFocus);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">{t(lang, 'driver')}</p>
            <h1 className="title">{t(lang, 'cityAir')}</h1>
            <p className="subtitle mt-2">{t(lang, 'cityAirHint')}</p>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={() => load()} disabled={loading} aria-label={t(lang, 'refreshLocation')}>
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {error ? <p className="error mt-4">{error}</p> : null}
      </section>

      {!loading && !confirmedDriver ? (
        <section className="card stack text-center">
          <ShieldAlert className="mx-auto text-brand-yellow" size={34} />
          <p className="text-lg font-black text-slate-950">{t(lang, 'needDriverCheck')}</p>
          <p className="subtitle mt-2">{t(lang, 'driverCheckHint')}</p>
          <Link href="/driver/register" className="button primary">{t(lang, 'applyDriver')}</Link>
        </section>
      ) : null}

      {confirmedDriver ? (
        <section className="metric-grid">
          <div className="metric-card"><div className="metric-label">{t(lang, 'available')}</div><div className="metric-value">{orders.length}</div></div>
          <div className="metric-card"><div className="metric-label">{t(lang, 'air')}</div><div className="metric-value">{t(lang, 'city')}</div></div>
        </section>
      ) : null}

      {loading ? (
        <section className="card text-center">
          <p className="subtitle">{t(lang, 'loadingOrders')}</p>
        </section>
      ) : null}

      {!loading && confirmedDriver && orders.length === 0 ? (
        <section className="card stack text-center">
          <Radio className="mx-auto text-brand-yellow" size={34} />
          <p className="text-lg font-black text-slate-950">{t(lang, 'noNearbyOrders')}</p>
          <p className="subtitle mt-2">{t(lang, 'noNearbyOrdersHint')}</p>
        </section>
      ) : null}

      {!loading && confirmedDriver && orders.length > 0 ? (
        <section className="stack">
          {orders.map((order) => (
            <OrderCard
              key={order.id}
              order={order}
              lang={lang}
              actionLabel={t(lang, 'accept')}
              disabled={actionId === order.id}
              onAction={() => accept(order.id)}
            />
          ))}
        </section>
      ) : null}
    </main>
  );
}
