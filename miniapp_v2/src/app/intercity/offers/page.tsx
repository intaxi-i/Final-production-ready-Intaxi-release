'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { CalendarDays, RefreshCw, Route, Users } from 'lucide-react';
import { APP_ROUTES } from '@/lib/constants';
import { acceptIntercityOffer, getMe, listIntercityOffers } from '@/lib/api';
import { getDriverProfile } from '@/lib/api-extra';
import type { DriverProfile, IntercityOffer, UserMe } from '@/lib/types';

function kindLabel(kind: string) {
  if (kind === 'request') return 'Заявка пассажира';
  if (kind === 'route') return 'Маршрут водителя';
  return 'Неизвестный тип';
}

function actionLabel(kind: string) {
  if (kind === 'request') return 'Принять как водитель';
  if (kind === 'route') return 'Поехать пассажиром';
  return 'Открыть предложение';
}

function statusLabel(value?: string | null) {
  if (value === 'search') return 'Идёт поиск';
  if (value === 'active') return 'Активно';
  if (value === 'accepted') return 'Принято';
  if (value === 'completed') return 'Завершено';
  if (value === 'cancelled') return 'Отменено';
  return 'Неизвестный статус';
}

function modeLabel(value?: string | null) {
  if (value === 'regular') return 'Обычный режим';
  if (value === 'women') return 'Женский режим';
  return 'Неизвестный режим';
}

function isConfirmedDriver(profile: DriverProfile | null) {
  if (!profile?.status) return false;
  return ['approved', 'verified', 'active'].includes(profile.status.toLowerCase());
}

function normalizeRouteText(value: string) {
  return value.trim().toLowerCase().replace(/\s+/g, ' ');
}

function routeMatches(item: IntercityOffer, from: string, to: string) {
  const fromQuery = normalizeRouteText(from);
  const toQuery = normalizeRouteText(to);
  const itemFrom = normalizeRouteText(item.from_text || '');
  const itemTo = normalizeRouteText(item.to_text || '');
  return (!fromQuery || itemFrom.includes(fromQuery)) && (!toQuery || itemTo.includes(toQuery));
}

export default function IntercityOffersPage() {
  const [items, setItems] = useState<IntercityOffer[]>([]);
  const [me, setMe] = useState<UserMe | null>(null);
  const [driverProfile, setDriverProfile] = useState<DriverProfile | null>(null);
  const [filter, setFilter] = useState<'all' | 'request' | 'route'>('all');
  const [fromFilter, setFromFilter] = useState('');
  const [toFilter, setToFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const confirmedDriver = me?.active_role === 'driver' && isConfirmedDriver(driverProfile);
  const filterOptions: Array<'all' | 'request' | 'route'> = confirmedDriver ? ['all', 'request', 'route'] : ['all', 'route'];

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const user = await getMe();
      setMe(user);
      const profile = user.active_role === 'driver' ? await getDriverProfile().catch(() => null) : null;
      setDriverProfile(profile);
      setItems(await listIntercityOffers());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить предложения');
    } finally {
      setLoading(false);
    }
  }

  async function accept(item: IntercityOffer) {
    if (item.kind === 'request' && !confirmedDriver) {
      setError('Заявки пассажиров доступны только подтверждённым водителям.');
      return;
    }

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

  useEffect(() => { void load(); }, []);

  const visibleItems = useMemo(() => {
    const roleSafeItems = confirmedDriver ? items : items.filter((item) => item.kind !== 'request');
    const kindItems = filter === 'all' ? roleSafeItems : roleSafeItems.filter((item) => item.kind === filter);
    return kindItems.filter((item) => routeMatches(item, fromFilter, toFilter));
  }, [confirmedDriver, filter, fromFilter, items, toFilter]);

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">Межгород</p>
            <h1 className="title">Предложения</h1>
            <p className="subtitle mt-2">{confirmedDriver ? 'Активные заявки пассажиров и маршруты водителей.' : 'Укажите направление и смотрите маршруты водителей по вашему пути.'}</p>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={load} disabled={loading} aria-label="Обновить">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {error ? <p className="error mt-4">{error}</p> : null}
      </section>

      <section className="card stack">
        <p className="metric-label">Фильтр маршрута</p>
        <div className="grid grid-2">
          <label className="label">Откуда<input className="input" value={fromFilter} onChange={(event) => setFromFilter(event.target.value)} placeholder="Например: Ташкент" /></label>
          <label className="label">Куда<input className="input" value={toFilter} onChange={(event) => setToFilter(event.target.value)} placeholder="Например: Самарканд" /></label>
        </div>
        <p className="subtitle">Пассажиру не показывается всё подряд: список сужается по направлению.</p>
      </section>

      <section className={`grid gap-2 ${confirmedDriver ? 'grid-cols-3' : 'grid-cols-2'}`}>
        {filterOptions.map((item) => (
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
          <p className="subtitle">По этому направлению пока нет активных предложений.</p>
          <div className="grid grid-2">
            <Link href={APP_ROUTES.intercityRequest} className="button primary">Создать заявку</Link>
            {confirmedDriver ? <Link href={APP_ROUTES.intercityRoute} className="button secondary">Опубликовать маршрут</Link> : null}
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
                    <div><strong>{statusLabel(item.status)}</strong><p className="subtitle mt-1">{modeLabel(item.mode)}</p></div>
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
    </main>
  );
}
