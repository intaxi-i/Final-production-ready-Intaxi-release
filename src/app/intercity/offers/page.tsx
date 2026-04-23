"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import BottomNav from "@/components/BottomNav";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { api, IntercityOffer } from "@/lib/api";
import { APP_ROUTES } from "@/lib/constants";
import { t } from "@/lib/i18n";

type Tab = "all" | "route" | "request";

export default function IntercityOffersPage() {
  const { lang, sessionToken, isReady } = useApp();
  const [tab, setTab] = useState<Tab>("all");
  const [items, setItems] = useState<IntercityOffer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function loadItems() {
      if (!isReady || !sessionToken) return;
      try {
        setLoading(true);
        const data = await api.intercityOffers(sessionToken);
        if (!cancelled) setItems(data.items);
      } catch {
        if (!cancelled) setItems([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void loadItems();
    return () => { cancelled = true; };
  }, [isReady, sessionToken]);

  const filtered = useMemo(() => tab === "all" ? items : items.filter((item) => item.kind === tab), [items, tab]);

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title={t(lang, "availableOffers")} subtitle={t(lang, "routeCard")} />

        <div className="tabs">
          <button className={`tab-button${tab === "all" ? " active" : ""}`} onClick={() => setTab("all")}>{t(lang, "tabsAll")}</button>
          <button className={`tab-button${tab === "route" ? " active" : ""}`} onClick={() => setTab("route")}>{t(lang, "tabsRoutes")}</button>
          <button className={`tab-button${tab === "request" ? " active" : ""}`} onClick={() => setTab("request")}>{t(lang, "tabsRequests")}</button>
        </div>

        <div className="card">
          {loading ? <div className="muted">{t(lang, "loading")}</div> : filtered.length === 0 ? <div className="muted">{t(lang, "noOffers")}</div> : filtered.map((item) => (
            <div key={`${item.kind}-${item.id}`} className="list-item">
              <div className="list-row">
                <div className="card-title">{item.from_city} → {item.to_city}</div>
                <span className="pill">{item.kind}</span>
              </div>
              <div className="menu-card-text">{item.date} · {item.time}</div>
              <div className="menu-card-text">{t(lang, "seats")}: {item.seats} · {t(lang, "price")}: {item.price}</div>
              <div className="menu-card-text">{item.status || "active"}</div>
              {item.comment ? <div className="menu-card-text">{item.comment}</div> : null}
              <div className="actions-row" style={{ marginTop: 12 }}>
                <Link href={`${APP_ROUTES.intercityOffers}/${item.kind}/${item.id}`} className="button-secondary">{t(lang, "details")}</Link>
                {item.active_trip_id || item.status === "accepted" || item.status === "in_progress" ? (
                  <Link href={`${APP_ROUTES.currentTrip}?tripType=intercity_${item.kind}&tripId=${item.id}`} className="button-main">{t(lang, "openTrip")}</Link>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </div>

      <BottomNav />
    </main>
  );
}
