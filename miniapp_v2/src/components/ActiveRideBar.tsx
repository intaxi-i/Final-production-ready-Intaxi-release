'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { getCurrentCityTrip, listMyCityOrders } from '@/lib/api';
import { APP_ROUTES } from '@/lib/constants';
import type { CityOrder, CityTrip } from '@/lib/types';

type Activity =
  | { kind: 'trip'; id: number; status: string; from: string; to: string; price: number; currency: string }
  | { kind: 'order'; id: number; status: string; from: string; to: string; price: number; currency: string; seen: number };

const LIVE_ORDER_STATUSES = new Set(['active', 'search', 'accepted']);
const LIVE_TRIP_STATUSES = new Set(['accepted', 'driver_on_way', 'driver_arrived', 'in_progress']);

function statusText(status: string) {
  const map: Record<string, string> = {
    active: 'Ищем водителя',
    search: 'Ищем водителя',
    accepted: 'Водитель найден',
    driver_on_way: 'Водитель в пути',
    driver_arrived: 'Водитель прибыл',
    in_progress: 'Поездка идёт',
  };
  return map[status] || status || 'Активно';
}

function tripToActivity(trip: CityTrip | null): Activity | null {
  if (!trip || !LIVE_TRIP_STATUSES.has(trip.status)) return null;
  return {
    kind: 'trip',
    id: trip.id,
    status: trip.status,
    from: trip.pickup_address || 'Точка A',
    to: trip.destination_address || 'Точка B',
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
    from: order.pickup_address || 'Точка A',
    to: order.destination_address || 'Точка B',
    price: Number(order.passenger_price || 0),
    currency: order.currency || 'UZS',
    seen: Number(order.seen_by_drivers || 0),
  };
}

export function ActiveRideBar() {
  const [activity, setActivity] = useState<Activity | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
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
    const timer = window.setInterval(() => void load(), 8000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  const href = useMemo(() => {
    if (!activity) return APP_ROUTES.home;
    return activity.kind === 'trip' ? APP_ROUTES.currentTrip : APP_ROUTES.cityMyOrders;
  }, [activity]);

  if (!activity) return null;

  return (
    <div className="active-ride-wrap">
      <Link href={href} className="active-ride-bar">
        <span className="active-ride-dot" />
        <span className="active-ride-main">
          <strong>{statusText(activity.status)}</strong>
          <small>{activity.from} → {activity.to}</small>
        </span>
        <span className="active-ride-price">
          {Math.round(activity.price).toLocaleString('ru-RU')} {activity.currency}
          {activity.kind === 'order' ? <small>{activity.seen} вод.</small> : null}
        </span>
      </Link>
    </div>
  );
}
