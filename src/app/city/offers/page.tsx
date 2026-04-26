"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import BottomNav from "@/components/BottomNav";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { api, CityOrder } from "@/lib/api";
import { APP_ROUTES } from "@/lib/constants";
import { t } from "@/lib/i18n";

function emptyText(lang: string, isDriver: boolean) {
  if (lang === "ru") return isDriver ? "Сейчас нет заказов пассажиров, ожидающих водителя." : "Сейчас нет доступных городских заказов.";
  if (lang === "uz") return isDriver ? "Hozir haydovchini kutayotgan yo‘lovchi buyurtmalari yo‘q." : "Hozir mavjud shahar buyurtmalari yo‘q.";
  if (lang === "ar") return isDriver ? "لا توجد الآن طلبات ركاب تنتظر سائقًا." : "لا توجد الآن طلبات مدينة متاحة.";
  if (lang === "kz") return isDriver ? "Қазір жүргізушіні күтіп тұрған жолаушы тапсырыстары жоқ." : "Қазір қолжетімді қалалық тапсырыстар жоқ.";
  return isDriver ? "No passenger orders are waiting for a driver right now." : "No city orders are available right now.";
}

export default function CityOffersPage() {
  const { lang, sessionToken, isReady, user } = useApp();
  const isDriver = user?.active_role === "driver";
  const [items, setItems] = useState<CityOrder[]>([]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!isReady || !sessionToken) return;
      try {
        const data = await api.cityOffers(sessionToken, isDriver ? "passenger" : "all");
        if (!cancelled) setItems(isDriver ? data.items.filter((item) => item.role === "passenger") : data.items);
      } catch {
        if (!cancelled) setItems([]);
      }
    }

    void load();
    const timer = window.setInterval(() => void load(), 8000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [isReady, sessionToken, isDriver]);

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title={isDriver ? t(lang, "cityOrdersPassengers") : t(lang, "availableOffers")} subtitle={isDriver ? t(lang, "cityOrdersPassengers") : t(lang, "cityOffersDrivers")} />

        <div className="card">
          {items.length === 0 ? (
            <div className="muted">{emptyText(lang, isDriver)}</div>
          ) : (
            items.map((item) => (
              <div key={item.id} className="list-item">
                <div className="list-row">
                  <div className="card-title">{item.city}</div>
                  <span className={`pill ${item.role === "driver" ? "role-driver" : "role-passenger"}`}>
                    {item.role === "driver" ? t(lang, "driverMode") : t(lang, "passengerMode")}
                  </span>
                </div>
                <div className="menu-card-text">{item.from_address}{item.to_address ? ` → ${item.to_address}` : ""}</div>
                <div className="menu-card-text">{t(lang, "price")}: {item.price} · {t(lang, "tripDistance")}: {item.estimated_distance_km ?? "—"} km</div>
                <div className="menu-card-text">{t(lang, "driverDistance")}: {item.driver_distance_km ?? "—"} km · {t(lang, "eta")}: {item.driver_eta_min ?? "—"} min</div>
                <div className="actions-row" style={{ marginTop: 12 }}>
                  <Link href={`${APP_ROUTES.cityOffers}/${item.id}`} className="button-secondary">{t(lang, "details")}</Link>
                  {item.active_trip_id ? <Link href={`${APP_ROUTES.currentTrip}?tripType=city_trip&tripId=${item.active_trip_id}`} className="button-main">{t(lang, "openTrip")}</Link> : null}
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
