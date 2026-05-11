'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { CalendarDays, RefreshCw, Route, Users } from 'lucide-react';
import { BottomNav } from '@/components/BottomNav';
import { APP_ROUTES } from '@/lib/constants';
import { acceptIntercityOffer, listIntercityOffers } from '@/lib/api';
import type { IntercityOffer } from '@/lib/types';

function kindLabel(kind: string) {
  return kind === 'request' ? 'Заявка пассажира' : 'Маршрут водителя';
}

function actionLabel(kind: string) {
  return kind === 'request' ? 'Принять как водитель' : 'Поехать пассажиром';
}

export default function IntercityOffersPage() {
  const [items, setItems] = useState<IntercityOffer[]>([]);
  const [filter, setFilter] = useState<'all' | 'request' | 'route'>('all');
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      setItems(await listIntercityOffers());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить предложения');
    } finally {
      setLoading(false);
    }
  }

  async function accept(item: IntercityOffer) {
    const key = `${item.kind}:${item.id}`;
    setActionId(key);
    setError(null);
    try {
      await acceptIntercityOffer(item.kind, item.id);
      window.location.href = APP_ROUTES.currentTrip;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось принять предложение');
    } finally {
      setActionId(null);
    }
  }

  useEffect(() => { load(); }, []);

  const visibleItems = useMemo(() => {
    if (filter === 'all') return items;
    return items.filter((item) => item.kind === filter);
  }, [filter, items]);

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">Межгород</p>
            <h1 className="title">Предложения</h1>
            <p className="subtitle mt-2">Активные заявки пассажиров и маршруты водителей.</p>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={load} disabled={loading} aria-label="Обновить">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {error ? <p className="error mt-4">{error}</p> : null}
      </section>

      <section className="grid grid-cols-3 gap-2">
        {(['all', 'request', 'route'] as const).map((item) => (
          <button
            key={item}
            type="button"
            className={`min-h-[50px] rounded-2xl text-xs font-black uppercase tracking-[0.08em] transition active:scale-95 ${filter === item ? 'bg-brand-yellow text-brand-dark' : 'bg-white text-slate-500 border border-slate-100'}`}
            onClick={() => setFilter(item)}
          >
            {item === 'all' ? 'Все' : item === 'request' ? 'Заявки' : 'Маршруты'}
          </button>
        ))}
      </section>

      {loading ? <section className="card"><p className="subtitle">Загрузка предложений...</p></section> : null}
      {!loading && visibleItems.length === 0 ? (
        <section className="card stack text-center">
          <p className="subtitle">Пока нет активных предложений.</p>
          <div className="grid grid-2">
            <Link href={APP_ROUTES.intercityRequest} className="button primary">Создать заявку</Link>
            <Link href={APP_ROUTES.intercityRoute} className="button secondary">Опубликовать маршрут</Link>
          </div>
        </section>
      ) : null}

      <section className="stack">
        {visibleItems.map((item) => {
          const key = `${item.kind}:${item.id}`;
          return (
            <article className="order-card" key={key}>
              <div className="order-card-inner">
                <div className="order-topline">
                  <span className="order-badge">{kindLabel(item.kind)} · №{item.id}</span>
                  <span className="order-seen"><Users size={14} /> {item.seats}</span>
                </div>

                <div className="route-panel">
                  <div className="route-line" />
                  <div className="route-point">
                    <div className="route-dot" />
                    <div><div className="route-kicker">Откуда</div><div className="route-address">{item.from_text}</div></div>
                  </div>
                  <div className="route-point">
                    <div className="route-dot end" />
                    <div><div className="route-kicker">Куда</div><div className="route-address muted">{item.to_text}</div></div>
                  </div>
                </div>

                <div className="metric-grid">
                  <div className="metric-card"><div className="metric-label">Цена</div><div className="metric-value">{Math.round(item.price).toLocaleString('ru-RU')} {item.currency}</div></div>
                  <div className="metric-card"><div className="metric-label">Страна</div><div className="metric-value">{item.country_code.toUpperCase()}</div></div>
                  <div className="metric-card"><div className="metric-label">Дата</div><div className="metric-value">{item.date || 'Гибко'}</div></div>
                  <div className="metric-card"><div className="metric-label">Время</div><div className="metric-value">{item.time || 'Гибко'}</div></div>
                </div>

                <div className="row rounded-3xl bg-slate-50 p-4">
                  <div className="flex items-center gap-3">
                    {item.kind === 'request' ? <Route className="text-brand-yellow" /> : <CalendarDays className="text-brand-yellow" />}
                    <div><strong>{item.status}</strong><p className="subtitle mt-1">{item.mode === 'women' ? 'Женский режим' : 'Обычный режим'}</p></div>
                  </div>
                </div>

                <button className="button primary mt-4 w-full" type="button" onClick={() => accept(item)} disabled={actionId === key}>
                  {actionId === key ? 'Принимаем...' : actionLabel(item.kind)}
                </button>
              </div>
            </article>
          );
        })}
      </section>
      <BottomNav />
    </main>
  );
}
