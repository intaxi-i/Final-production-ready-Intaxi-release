"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import BottomNav from "@/components/BottomNav";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { api, CityOrder } from "@/lib/api";
import { APP_ROUTES } from "@/lib/constants";
import { t } from "@/lib/i18n";

function repeatLabel(lang: string) {
  if (lang === "ru") return "Повторить маршрут";
  if (lang === "uz") return "Marshrutni takrorlash";
  if (lang === "ar") return "تكرار المسار";
  if (lang === "kz") return "Маршрутты қайталау";
  return "Repeat route";
}

function swapLabel(lang: string) {
  if (lang === "ru") return "Поменять точки";
  if (lang === "uz") return "Nuqtalarni almashtirish";
  if (lang === "ar") return "تبديل النقطتين";
  if (lang === "kz") return "Нүктелерді ауыстыру";
  return "Swap points";
}

function statusHint(lang: string, item: CityOrder) {
  if (item.active_trip_id) {
    if (lang === "ru") return "Водитель найден. Откройте текущую поездку.";
    return t(lang, "openTrip");
  }
  if (item.status === "active") {
    if (lang === "ru") return `Поиск водителя активен. Заказ уже показан ${item.seen_by_drivers ?? 0} водителям.`;
    return `${t(lang, "driversSeen")}: ${item.seen_by_drivers ?? 0}`;
  }
  if (lang === "ru") return `Статус заказа: ${item.status || "—"}`;
  return `${t(lang, "status")}: ${item.status || "—"}`;
}

export default function CityMyOrdersPage() {
  const { lang, sessionToken, isReady } = useApp();
  const [items, setItems] = useState<CityOrder[]>([]);

  const load = useCallback(async () => {
    if (!isReady || !sessionToken) return;
    try {
      const data = await api.myCityOrders(sessionToken);
      const next = (data.items || []).filter((item) => item.role === "passenger");
      setItems(next);
      const activeTrip = next.find((item) => item.active_trip_id);
      if (activeTrip?.active_trip_id) {
        window.location.href = `${APP_ROUTES.currentTrip}?tripType=city_trip&tripId=${activeTrip.active_trip_id}`;
      }
    } catch {
      setItems([]);
    }
  }, [isReady, sessionToken]);

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 8000);
    return () => window.clearInterval(timer);
  }, [load]);

  async function handleClose(id: number) {
    if (!sessionToken) return;
    try {
      await api.closeCityOrder(sessionToken, id);
      await load();
    } catch {}
  }

  function buildRepeatHref(item: CityOrder, swapped = false) {
    const params = new URLSearchParams();
    params.set("role", "passenger");
    if (item.country) params.set("country", item.country);
    if (item.city) params.set("city", item.city);
    params.set("from", swapped ? (item.to_address || "") : item.from_address);
    params.set("to", swapped ? item.from_address : (item.to_address || ""));
    params.set("seats", String(item.seats || 1));
    params.set("price", String(item.price || 0));
    if (item.comment) params.set("comment", item.comment);
    return `${APP_ROUTES.cityCreate}?${params.toString()}`;
  }

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title={t(lang, "cityMyOrders")} subtitle={lang === "ru" ? "Ваши городские заказы и поиск водителя" : t(lang, "status")} />
        <div className="card">
          {items.length === 0 ? (
            <div className="muted">{lang === "ru" ? "У вас пока нет активных городских заказов. Здесь появится поиск водителя и повторная активация маршрута." : t(lang, "noOrders")}</div>
          ) : (
            items.map((item) => (
              <div key={item.id} className="list-item">
                <div className="list-row">
                  <div className="card-title">{item.city}</div>
                  <span className="pill role-passenger">{t(lang, "passengerMode")}</span>
                </div>
                <div className="menu-card-text">{item.from_address}{item.to_address ? ` → ${item.to_address}` : ""}</div>
                <div className="menu-card-text">{statusHint(lang, item)}</div>
                <div className="actions-row" style={{ marginTop: 12 }}>
                  {item.active_trip_id ? (
                    <Link href={`${APP_ROUTES.currentTrip}?tripType=city_trip&tripId=${item.active_trip_id}`} className="button-main">{t(lang, "openTrip")}</Link>
                  ) : null}
                  <Link href={buildRepeatHref(item, false)} className="button-secondary">{repeatLabel(lang)}</Link>
                  {item.to_address ? <Link href={buildRepeatHref(item, true)} className="button-secondary">{swapLabel(lang)}</Link> : null}
                  {item.status !== "closed" && !item.active_trip_id ? (
                    <button className="button-danger" onClick={() => handleClose(item.id)}>{t(lang, "close")}</button>
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
