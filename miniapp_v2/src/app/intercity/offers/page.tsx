'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { CalendarDays, RefreshCw, Route, Users } from 'lucide-react';
import { APP_ROUTES } from '@/lib/constants';
import { acceptIntercityOffer, getMe, listIntercityOffers } from '@/lib/api';
import { getDriverProfile } from '@/lib/api-extra';
import { t } from '@/lib/i18n';
import type { DriverProfile, IntercityOffer, UserMe } from '@/lib/types';

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

function parseKind(value: string | null): 'request' | 'route' | null {
  return value === 'request' || value === 'route' ? value : null;
}

function readKindQuery(): 'request' | 'route' | null {
  if (typeof window === 'undefined') return null;
  return parseKind(new URLSearchParams(window.location.search).get('kind'));
}

export default function IntercityOffersPage() {
  const [items, setItems] = useState<IntercityOffer[]>([]);
  const [me, setMe] = useState<UserMe | null>(null);
  const [driverProfile, setDriverProfile] = useState<DriverProfile | null>(null);
  const [kindOverride, setKindOverride] = useState<'request' | 'route' | null>(null);
  const [fromFilter, setFromFilter] = useState('');
  const [toFilter, setToFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const lang = me?.language;
  const confirmedDriver = me?.active_role === 'driver' && isConfirmedDriver(driverProfile);
  const roleBasedKind = confirmedDriver ? 'request' : 'route';
  const targetKind = kindOverride || roleBasedKind;

  function kindLabel(kind: string) {
    if (kind === 'request') return t(lang, 'requestKind');
    if (kind === 'route') return t(lang, 'routeKind');
    return t(lang, 'unknownMode');
  }

  function actionLabel(kind: string) {
    if (kind === 'request') return t(lang, 'acceptAsDriver');
    if (kind === 'route') return t(lang, 'goAsPassenger');
    return t(lang, 'openOffer');
  }

  function statusLabel(value?: string | null) {
    if (value === 'search') return t(lang, 'searchStatus');
    if (value === 'active') return t(lang, 'activeStatus');
    if (value === 'accepted') return t(lang, 'acceptedStatus');
    if (value === 'completed') return t(lang, 'completedStatus');
    if (value === 'cancelled') return t(lang, 'cancelledStatus');
    return t(lang, 'unknownStatus');
  }

  function modeLabel(value?: string | null) {
    if (value === 'regular') return t(lang, 'regularMode');
    if (value === 'women') return t(lang, 'womenMode');
    return t(lang, 'unknownMode');
  }

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
      setError(err instanceof Error ? err.message : t(lang, 'operationFailed'));
    } finally {
      setLoading(false);
    }
  }

  async function accept(item: IntercityOffer) {
    if (item.kind === 'request' && !confirmedDriver) {
      setError(t(lang, 'driverRequestsOnly'));
      return;
    }

    const key = `${item.kind}:${item.id}`;
    setActionId(key);
    setError(null);
    try {
      await acceptIntercityOffer(item.kind, item.id);
      window.location.href = APP_ROUTES.currentTrip;
    } catch (err) {
      setError(err instanceof Error ? err.message : t(lang, 'operationFailed'));
    } finally {
      setActionId(null);
    }
  }

  useEffect(() => {
    setKindOverride(readKindQuery());
    void load();
  }, []);

  const visibleItems = useMemo(() => {
    return items
      .filter((item) => item.kind === targetKind)
      .filter((item) => routeMatches(item, fromFilter, toFilter));
  }, [fromFilter, items, targetKind, toFilter]);

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">{t(lang, 'intercity')}</p>
            <h1 className="title">{t(lang, 'intercityOffersTitle')}</h1>
            <p className="subtitle mt-2">{confirmedDriver ? t(lang, 'intercityDriverHint') : t(lang, 'intercityPassengerHint')}</p>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={load} disabled={loading} aria-label={t(lang, 'refreshLocation')}>
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {error ? <p className="error mt-4">{error}</p> : null}
      </section>

      <section className="card stack">
        <p className="metric-label">{t(lang, 'routeFilter')}</p>
        <div className="grid grid-2">
          <label className="label">{t(lang, 'fromWhere')}<input className="input" value={fromFilter} onChange={(event) => setFromFilter(event.target.value)} placeholder={t(lang, 'exampleFrom')} /></label>
          <label className="label">{t(lang, 'toWhere')}<input className="input" value={toFilter} onChange={(event) => setToFilter(event.target.value)} placeholder={t(lang, 'exampleTo')} /></label>
        </div>
        <p className="subtitle">{targetKind === 'request' ? t(lang, 'driverRequestsOnly') : t(lang, 'passengerRoutesOnly')}</p>
      </section>

      {loading ? <section className="card"><p className="subtitle">{t(lang, 'loadingOffers')}</p></section> : null}
      {!loading && visibleItems.length === 0 ? (
        <section className="card stack text-center">
          <p className="subtitle">{t(lang, 'noRouteOffers')}</p>
          <div className="grid grid-2">
            <Link href={APP_ROUTES.intercityRequest} className="button primary">{t(lang, 'createRequest')}</Link>
            {confirmedDriver ? <Link href={APP_ROUTES.intercityRoute} className="button secondary">{t(lang, 'publishRoute')}</Link> : null}
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
                    <div><div className="route-kicker">{t(lang, 'fromWhere')}</div><div className="route-address">{item.from_text}</div></div>
                  </div>
                  <div className="route-point">
                    <div className="route-dot end" />
                    <div><div className="route-kicker">{t(lang, 'toWhere')}</div><div className="route-address muted">{item.to_text}</div></div>
                  </div>
                </div>

                <div className="metric-grid">
                  <div className="metric-card"><div className="metric-label">{t(lang, 'price')}</div><div className="metric-value">{Math.round(item.price).toLocaleString('ru-RU')} {item.currency}</div></div>
                  <div className="metric-card"><div className="metric-label">{t(lang, 'country')}</div><div className="metric-value">{item.country_code.toUpperCase()}</div></div>
                  <div className="metric-card"><div className="metric-label">{t(lang, 'date')}</div><div className="metric-value">{item.date || t(lang, 'flexible')}</div></div>
                  <div className="metric-card"><div className="metric-label">{t(lang, 'time')}</div><div className="metric-value">{item.time || t(lang, 'flexible')}</div></div>
                </div>

                <div className="row rounded-3xl bg-slate-50 p-4">
                  <div className="flex items-center gap-3">
                    {item.kind === 'request' ? <Route className="text-brand-yellow" /> : <CalendarDays className="text-brand-yellow" />}
                    <div><strong>{statusLabel(item.status)}</strong><p className="subtitle mt-1">{modeLabel(item.mode)}</p></div>
                  </div>
                </div>

                <button className="button primary mt-4 w-full" type="button" onClick={() => accept(item)} disabled={actionId === key}>
                  {actionId === key ? t(lang, 'accepting') : actionLabel(item.kind)}
                </button>
              </div>
            </article>
          );
        })}
      </section>
    </main>
  );
}
