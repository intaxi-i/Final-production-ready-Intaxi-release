"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import BottomNav from "@/components/BottomNav";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { api, IntercityMyRoute } from "@/lib/api";
import { APP_ROUTES } from "@/lib/constants";
import { t } from "@/lib/i18n";

function pickupModeLabel(lang: string, mode?: string) {
  if (mode === "driver_location") return lang === "ru" ? "Место встречи: водитель" : "Driver location";
  if (mode === "driver_pickup") return lang === "ru" ? "Водитель заберёт пассажира" : "Driver pickup";
  return lang === "ru" ? "Уточнить в чате" : "Clarify in chat";
}

export default function MyRoutesPage() {
  const { lang, sessionToken, isReady } = useApp();
  const [items, setItems] = useState<IntercityMyRoute[]>([]);
  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!isReady || !sessionToken) return;
      try {
        const data = await api.myIntercityRoutes(sessionToken);
        if (!cancelled) setItems(data.items);
      } catch {
        if (!cancelled) setItems([]);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [isReady, sessionToken]);

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title={t(lang, "myRoutes")} subtitle={t(lang, "status")} />
        <div className="card">
          {items.length === 0 ? <div className="muted">{t(lang, "noRoutes")}</div> : items.map((item) => (
            <div key={item.id} className="list-item">
              <div className="card-title">{item.from_city} → {item.to_city}</div>
              <div className="menu-card-text">{item.date} · {item.time}</div>
              <div className="menu-card-text">{t(lang, "status")}: {item.status}</div>
              <div className="menu-card-text">{pickupModeLabel(lang, item.pickup_mode)}</div>
              <div className="actions-row" style={{ marginTop: 12 }}>
                <Link href={`${APP_ROUTES.currentTrip}?tripType=intercity_route&tripId=${item.id}`} className="button-main">{t(lang, "openTrip")}</Link>
              </div>
            </div>
          ))}
        </div>
      </div>
      <BottomNav />
    </main>
  );
}
