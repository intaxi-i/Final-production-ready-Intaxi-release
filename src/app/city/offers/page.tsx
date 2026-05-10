"use client";

import { useEffect, useMemo, useState } from "react";
import BottomNav from "@/components/BottomNav";
import PageHeader from "@/components/PageHeader";
import PremiumCityCard from "@/components/PremiumCityCard";
import { useApp } from "@/context/AppContext";
import { api, CityOrder } from "@/lib/api";
import { t } from "@/lib/i18n";

function emptyText(isDriver: boolean) {
  return isDriver ? "No passenger orders are waiting for a driver right now." : "No city orders are available right now.";
}

function sortItems(items: CityOrder[]) {
  return [...items].sort((a, b) => {
    const aActiveTrip = a.active_trip_id ? 1 : 0;
    const bActiveTrip = b.active_trip_id ? 1 : 0;
    if (aActiveTrip !== bActiveTrip) return aActiveTrip - bActiveTrip;
    const aDistance = Number(a.driver_distance_km ?? 999999);
    const bDistance = Number(b.driver_distance_km ?? 999999);
    if (aDistance !== bDistance) return aDistance - bDistance;
    return Number(b.id) - Number(a.id);
  });
}

export default function CityOffersPage() {
  const { lang, sessionToken, isReady, user } = useApp();
  const isDriver = user?.active_role === "driver";
  const [items, setItems] = useState<CityOrder[]>([]);
  const [message, setMessage] = useState("");

  async function load() {
    if (!isReady || !sessionToken) return;
    try {
      const data = await api.cityOffers(sessionToken, isDriver ? "passenger" : "all");
      setItems(isDriver ? data.items.filter((item) => item.role === "passenger") : data.items);
    } catch {
      setItems([]);
    }
  }

  useEffect(() => {
    let cancelled = false;
    async function safeLoad() {
      if (!cancelled) await load();
    }
    void safeLoad();
    const timer = window.setInterval(() => void safeLoad(), 8000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [isReady, sessionToken, isDriver]);

  const ordered = useMemo(() => sortItems(items), [items]);

  async function handleRaisePrice(orderId: number, price: number) {
    if (!sessionToken) return;
    await api.raiseCityOrderPrice(sessionToken, orderId, price);
    setMessage(t(lang, "updatedSuccessfully"));
    await load();
  }

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title={isDriver ? t(lang, "cityOrdersPassengers") : t(lang, "availableOffers")} subtitle={isDriver ? t(lang, "cityOrdersPassengers") : t(lang, "cityOffersDrivers")} />
        {message ? <div className="notice">{message}</div> : null}
        {ordered.length === 0 ? (
          <div className="card"><div className="muted">{emptyText(isDriver)}</div></div>
        ) : (
          <div className="stack">
            {ordered.map((item) => (
              <PremiumCityCard key={item.id} item={item} lang={lang} isDriver={isDriver} onRaisePrice={isDriver ? handleRaisePrice : undefined} />
            ))}
          </div>
        )}
      </div>
      <BottomNav />
    </main>
  );
}
