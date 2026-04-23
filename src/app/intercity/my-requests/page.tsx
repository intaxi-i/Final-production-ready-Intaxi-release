"use client";

import { useEffect, useState } from "react";
import BottomNav from "@/components/BottomNav";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { api, IntercityMyRequest } from "@/lib/api";
import { t } from "@/lib/i18n";

export default function MyRequestsPage() {
  const { lang, sessionToken, isReady } = useApp();
  const [items, setItems] = useState<IntercityMyRequest[]>([]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!isReady || !sessionToken) return;
      try {
        const data = await api.myIntercityRequests(sessionToken);
        if (!cancelled) {
          setItems(data.items);
        }
      } catch {
        if (!cancelled) {
          setItems([]);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [isReady, sessionToken]);

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title={t(lang, "myRequests")} subtitle={t(lang, "passengerMode")} />
        <div className="card">
          {items.length === 0 ? (
            <div className="muted">{t(lang, "noRequests")}</div>
          ) : (
            items.map((item) => (
              <div key={item.id} className="list-item">
                <div className="card-title">
                  {item.from_city} → {item.to_city}
                </div>
                <div className="menu-card-text">
                  {item.date} · {item.time}
                </div>
                <div className="menu-card-text">
                  {t(lang, "people")}: {item.seats_needed} · {t(lang, "price")}: {item.price_offer}
                </div>
                <div className="menu-card-text">
                  {t(lang, "status")}: {item.status}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
      <BottomNav />
    </main>
  );
}