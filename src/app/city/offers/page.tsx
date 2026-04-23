"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import BottomNav from "@/components/BottomNav";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { api, CityOrder } from "@/lib/api";
import { APP_ROUTES } from "@/lib/constants";
import { t } from "@/lib/i18n";

export default function CityOffersPage() {
  const { lang, sessionToken, isReady, user } = useApp();

  const defaultKind =
    user?.active_role === "driver" ? "passenger" : "driver";

  const [kind, setKind] = useState<"all" | "driver" | "passenger">(defaultKind);
  const [items, setItems] = useState<CityOrder[]>([]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const kindFromQuery = params.get("kind");

    if (
      kindFromQuery === "all" ||
      kindFromQuery === "driver" ||
      kindFromQuery === "passenger"
    ) {
      setKind(kindFromQuery);
    } else {
      setKind(defaultKind);
    }
  }, [defaultKind]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!isReady || !sessionToken) return;

      try {
        const data = await api.cityOffers(sessionToken, kind);
        if (!cancelled) setItems(data.items);
      } catch {
        if (!cancelled) setItems([]);
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [isReady, sessionToken, kind]);

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader
          title={t(lang, "availableOffers")}
          subtitle={
            kind === "passenger"
              ? t(lang, "cityOrdersPassengers")
              : t(lang, "cityOffersDrivers")
          }
        />

        <div className="tabs">
          <button
            className={`tab-button${kind === "driver" ? " active" : ""}`}
            onClick={() => setKind("driver")}
          >
            {t(lang, "tabsDrivers")}
          </button>

          <button
            className={`tab-button${kind === "passenger" ? " active" : ""}`}
            onClick={() => setKind("passenger")}
          >
            {t(lang, "tabsPassengers")}
          </button>

          <button
            className={`tab-button${kind === "all" ? " active" : ""}`}
            onClick={() => setKind("all")}
          >
            {t(lang, "all")}
          </button>
        </div>

        <div className="card">
          {items.length === 0 ? (
            <div className="muted">{t(lang, "noOffers")}</div>
          ) : (
            items.map((item) => (
              <div key={item.id} className="list-item">
                <div className="list-row">
                  <div className="card-title">{item.city}</div>
                  <span
                    className={`pill ${
                      item.role === "driver" ? "role-driver" : "role-passenger"
                    }`}
                  >
                    {item.role === "driver"
                      ? t(lang, "driverMode")
                      : t(lang, "passengerMode")}
                  </span>
                </div>

                <div className="menu-card-text">
                  {item.from_address}
                  {item.to_address ? ` → ${item.to_address}` : ""}
                </div>

                <div className="menu-card-text">
                  {t(lang, "price")}: {item.price} · {t(lang, "tripDistance")}:{" "}
                  {item.estimated_distance_km ?? "—"} km
                </div>

                <div className="menu-card-text">
                  {t(lang, "driverDistance")}: {item.driver_distance_km ?? "—"} km ·{" "}
                  {t(lang, "eta")}: {item.driver_eta_min ?? "—"} min
                </div>

                <div className="actions-row" style={{ marginTop: 12 }}>
                  <Link
                    href={`${APP_ROUTES.cityOffers}/${item.id}`}
                    className="button-secondary"
                  >
                    {t(lang, "details")}
                  </Link>

                  {item.active_trip_id ? (
                    <Link
                      href={`${APP_ROUTES.currentTrip}?tripType=city_trip&tripId=${item.active_trip_id}`}
                      className="button-main"
                    >
                      {t(lang, "openTrip")}
                    </Link>
                  ) : null}
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