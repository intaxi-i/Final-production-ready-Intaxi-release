'use client';

import { useEffect, useState } from 'react';
import { History, RefreshCw } from 'lucide-react';
import { cancelCityOrder, getMe, listMyCityOrders, raiseCityOrderPrice } from '@/lib/api';
import type { CityOrder, UserMe } from '@/lib/types';
import { OrderCard } from '@/components/OrderCard';
import { t } from '@/lib/i18n';

function roundPassengerRaise(value: number, currency: string) {
  if (currency === 'UZS') return Math.round((value * 1.1) / 1000) * 1000;
  if (currency === 'KZT') return Math.round((value * 1.1) / 100) * 100;
  return Math.round(value * 1.1);
}

function isLiveStatus(status: string) {
  return ['search', 'active', 'accepted'].includes(status);
}

export default function MyCityOrdersPage() {
  const [orders, setOrders] = useState<CityOrder[]>([]);
  const [me, setMe] = useState<UserMe | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const lang = me?.language;

  async function load(silent = false) {
    setError(null);
    if (!silent) setLoading(true);
    try {
      const user = await getMe().catch(() => null);
      setMe(user);
      setOrders(await listMyCityOrders());
    } catch (err) {
      setError(err instanceof Error ? err.message : t(lang, 'loadOrdersFailed'));
    } finally {
      if (!silent) setLoading(false);
    }
  }

  async function raise(order: CityOrder) {
    setActionId(order.id);
    setError(null);
    try {
      await raiseCityOrderPrice(order.id, roundPassengerRaise(order.passenger_price, order.currency));
      await load(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t(lang, 'raisePriceFailed'));
    } finally {
      setActionId(null);
    }
  }

  async function cancel(order: CityOrder) {
    setActionId(order.id);
    setError(null);
    try {
      await cancelCityOrder(order.id, 'cancelled_by_passenger');
      await load(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t(lang, 'cancelOrderFailed'));
    } finally {
      setActionId(null);
    }
  }

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(true), 10000);
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

  const activeOrders = orders.filter((order) => isLiveStatus(order.status));
  const historyOrders = orders.filter((order) => !isLiveStatus(order.status));

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">{t(lang, 'passengerMode')}</p>
            <h1 className="title">{t(lang, 'myOrders')}</h1>
            <p className="subtitle mt-2">{t(lang, 'myOrdersHint')}</p>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={() => load()} disabled={loading} aria-label={t(lang, 'refreshLocation')}>
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {error ? <p className="error mt-4">{error}</p> : null}
      </section>

      <section className="metric-grid">
        <div className="metric-card"><div className="metric-label">{t(lang, 'total')}</div><div className="metric-value">{orders.length}</div></div>
        <div className="metric-card"><div className="metric-label">{t(lang, 'active')}</div><div className="metric-value">{activeOrders.length}</div></div>
      </section>

      {loading ? <section className="card"><p className="subtitle">{t(lang, 'loading')}</p></section> : null}
      {!loading && orders.length === 0 ? (
        <section className="card stack text-center">
          <History className="mx-auto text-brand-yellow" size={34} />
          <h2 className="title" style={{ fontSize: 22 }}>{t(lang, 'emptyHistory')}</h2>
          <p className="subtitle">{t(lang, 'emptyHistoryHint')}</p>
        </section>
      ) : null}

      {activeOrders.length > 0 ? (
        <section className="stack">
          <h2 className="title" style={{ fontSize: 22 }}>{t(lang, 'active')}</h2>
          {activeOrders.map((order) => (
            <div className="stack" key={order.id}>
              <OrderCard order={order} lang={lang} />
              <div className="actions">
                <button className="button secondary" type="button" disabled={actionId === order.id} onClick={() => raise(order)}>
                  {t(lang, 'raisePrice10')}
                </button>
                <button className="button danger" type="button" disabled={actionId === order.id} onClick={() => cancel(order)}>
                  {t(lang, 'cancel')}
                </button>
              </div>
            </div>
          ))}
        </section>
      ) : null}

      {historyOrders.length > 0 ? (
        <section className="stack">
          <h2 className="title" style={{ fontSize: 22 }}>{t(lang, 'history')}</h2>
          <div className="grid grid-2">
            {historyOrders.map((order) => <OrderCard key={order.id} order={order} lang={lang} />)}
          </div>
        </section>
      ) : null}
    </main>
  );
}
