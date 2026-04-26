"use client";

import { useEffect, useState } from "react";
import ActionCard from "@/components/ActionCard";
import BottomNav from "@/components/BottomNav";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { APP_ROUTES } from "@/lib/constants";
import { t } from "@/lib/i18n";
import { api } from "@/lib/api";

function onlineLabel(lang: string, value: boolean) {
  if (lang === "ru") return value ? "Статус водителя: активен" : "Статус водителя: неактивен";
  if (lang === "uz") return value ? "Haydovchi holati: faol" : "Haydovchi holati: nofaol";
  if (lang === "ar") return value ? "حالة السائق: نشط" : "حالة السائق: غير نشط";
  if (lang === "kz") return value ? "Жүргізуші мәртебесі: белсенді" : "Жүргізуші мәртебесі: белсенді емес";
  return value ? "Driver status: active" : "Driver status: inactive";
}

function onlineHint(lang: string, value: boolean) {
  if (lang === "ru") return value ? "Вы получаете ближайшие городские заказы." : "Включите активность, чтобы получать ближайшие заказы.";
  if (lang === "uz") return value ? "Yaqin shahar buyurtmalarini qabul qilasiz." : "Yaqin buyurtmalarni olish uchun faollikni yoqing.";
  if (lang === "ar") return value ? "أنت تتلقى الطلبات القريبة داخل المدينة." : "فعّل النشاط لتلقي أقرب الطلبات.";
  if (lang === "kz") return value ? "Сіз жақын қалалық тапсырыстарды алып тұрсыз." : "Жақын тапсырыстарды алу үшін белсенділікті қосыңыз.";
  return value ? "You are receiving nearby city orders." : "Turn activity on to receive nearby orders.";
}

export default function CityPage() {
  const { lang, user, sessionToken } = useApp();
  const [forcedRole, setForcedRole] = useState("");
  const [online, setOnline] = useState(false);
  const role = forcedRole || user?.active_role || "passenger";

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setForcedRole(params.get("role") || "");
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!sessionToken || role !== "driver") return;
      try {
        const state = await api.driverOnline(sessionToken);
        if (!cancelled) setOnline(Boolean(state.is_online));
      } catch {}
    }
    void load();
    return () => { cancelled = true; };
  }, [sessionToken, role]);

  async function toggleOnline() {
    if (!sessionToken) return;
    const next = !online;
    try {
      const state = await api.setDriverOnline(sessionToken, next);
      setOnline(Boolean(state.is_online));
    } catch {}
  }

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title={t(lang, "city")} subtitle={t(lang, "cityDescription")} />

        {role === "driver" ? (
          <>
            <div className="card stack">
              <div className="card-title">{onlineLabel(lang, online)}</div>
              <div className="muted">{onlineHint(lang, online)}</div>
              <button className="button-secondary full" onClick={toggleOnline}>{onlineLabel(lang, online)}</button>
            </div>
            <ActionCard href={`${APP_ROUTES.cityOffers}?kind=passenger`} title={t(lang, "cityOrdersPassengers")} text={t(lang, "availableOffers")} />
            <ActionCard href={APP_ROUTES.cityMyOrders} title={t(lang, "cityMyOrders")} text={t(lang, "status")} />
            <ActionCard href={APP_ROUTES.currentTrip} title={t(lang, "currentTrip")} text={t(lang, "chat")} />
          </>
        ) : (
          <>
            <ActionCard href={`${APP_ROUTES.cityCreate}?role=passenger`} title={t(lang, "fastOrder")} text={t(lang, "cityMode")} />
            <ActionCard href={APP_ROUTES.cityMyOrders} title={t(lang, "cityMyOrders")} text={t(lang, "status")} />
            <ActionCard href={APP_ROUTES.currentTrip} title={t(lang, "currentTrip")} text={t(lang, "chat")} />
          </>
        )}
      </div>

      <BottomNav />
    </main>
  );
}
