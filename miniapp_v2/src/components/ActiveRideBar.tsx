'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { getCurrentCityTrip, getMe, listMyCityOrders } from '@/lib/api';
import { APP_ROUTES } from '@/lib/constants';
import { t } from '@/lib/i18n';
import type { CityOrder, CityTrip, UserMe } from '@/lib/types';

type Activity =
  | { kind: 'trip'; id: number; status: string; from: string; to: string; price: number; currency: string; orderId: number | null }
  | { kind: 'order'; id: number; status: string; from: string; to: string; price: number; currency: string; seen: number; seats: number };

const LIVE_ORDER_STATUSES = new Set(['active', 'search', 'accepted']);
const LIVE_TRIP_STATUSES = new Set(['accepted', 'driver_on_way', 'driver_arrived', 'in_progress']);

function statusText(lang: string | undefined | null, status: string, role: string | undefined | null) {
  const isDriver = role === 'driver';
  if (status === 'active' || status === 'search') return t(lang, 'searchingDriver');
  if (status === 'accepted') return t(lang, isDriver ? 'driverFoundDriver' : 'driverFoundPassenger');
  if (status === 'driver_on_way') return t(lang, isDriver ? 'driverOnWayDriver' : 'driverOnWayPassenger');
  if (status === 'driver_arrived') return t(lang, isDriver ? 'driverArrivedDriver' : 'driverArrivedPassenger');
  if (status === 'in_progress') return t(lang, isDriver ? 'tripInProgressDriver' : 'tripInProgressPassenger');
  return status || t(lang, 'activeStatus');
}

function tripToActivity(trip: CityTrip | null): Activity | null {
  if (!trip || !LIVE_TRIP_STATUSES.has(trip.status)) return null;
  return {
    kind: 'trip',
    id: trip.id,
    orderId: trip.order_id || null,
    status: trip.status,
    from: trip.pickup_address || '',
    to: trip.destination_address || '',
    price: Number(trip.final_price || 0),
    currency: trip.currency || 'UZS',
  };
}

function orderToActivity(order: CityOrder | null): Activity | null {
  if (!order || !LIVE_ORDER_STATUSES.has(order.status)) return null;
  return {
    kind: 'order',
    id: order.id,
    status: order.status,
    from: order.pickup_address || '',
    to: order.destination_address || '',
    price: Number(order.passenger_price || 0),
    currency: order.currency || 'UZS',
    seen: Number(order.seen_by_drivers || 0),
    seats: Number(order.seats || 1),
  };
}

export function ActiveRideBar() {
  const [activity, setActivity] = useState<Activity | null>(null);
  const [me, setMe] = useState<UserMe | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const user = await getMe().catch(() => null);
        if (!cancelled) setMe(user);
        const trip = tripToActivity(await getCurrentCityTrip());
        if (cancelled) return;
        if (trip) {
          setActivity(trip);
          return;
        }
        const orders = await listMyCityOrders();
        if (cancelled) return;
        const activeOrder = orders.find((item) => LIVE_ORDER_STATUSES.has(item.status));
        setActivity(orderToActivity(activeOrder || null));
      } catch {
        if (!cancelled) setActivity(null);
      }
    }

    void load();
    const timer = window.setInterval(() => void load(), 5000);
    const onFocus = () => void load();
    window.addEventListener('focus', onFocus);
    document.addEventListener('visibilitychange', onFocus);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
      window.removeEventListener('focus', onFocus);
      document.removeEventListener('visibilitychange', onFocus);
    };
  }, []);

  const href = useMemo(() => {
    if (!activity) return APP_ROUTES.home;
    return activity.kind === 'trip' ? APP_ROUTES.currentTrip : APP_ROUTES.cityMyOrders;
  }, [activity]);

  if (!activity) return null;

  const lang = me?.language;
  const fallbackFrom = t(lang, 'fromWhere');
  const fallbackTo = t(lang, 'toWhere');

  return (
    <div className="active-ride-wrap">
      <Link href={href} className="active-ride-bar">
        <span className="active-ride-dot" />
        <span className="active-ride-main">
          <strong>{statusText(lang, activity.status, me?.active_role)}</strong>
          <small>{activity.from || fallbackFrom} → {activity.to || fallbackTo}</small>
        </span>
        <span className="active-ride-price">
          {Math.round(activity.price).toLocaleString('ru-RU')} {activity.currency}
          {activity.kind === 'order' ? <small>{activity.seen} {t(lang, 'seenShort')} · {activity.seats}</small> : null}
        </span>
      </Link>
    </div>
  );
}
