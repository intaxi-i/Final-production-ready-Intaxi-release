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
  if (lang === "ru") return value ? "Вы получаете ближайшие городские заказы и видны в списке активных водителей." : "Включите активность, чтобы получать ближайшие городские заказы.";
  if (lang === "uz") return value ? "Yaqin shahar buyurtmalarini olasiz va faol haydovchilar ro‘yxatida ko‘rinasiz." : "Yaqin shahar buyurtmalarini olish uchun faollikni yoqing.";
  if (lang === "ar") return value ? "أنت تتلقى الطلبات القريبة وتظهر ضمن السائقين النشطين." : "فعّل النشاط لتلقي أقرب الطلبات داخل المدينة.";
  if (lang === "kz") return value ? "Сіз жақын қалалық тапсырыстарды алып, белсенді жүргізушілер тізімінде көрінесіз." : "Жақын қалалық тапсырыстарды алу үшін белсенділікті қосыңыз.";
  return value ? "You receive nearby city orders and appear as an active driver." : "Turn activity on to receive nearby city orders.";
}

function toggleText(lang: string, value: boolean) {
  if (lang === "ru") return value ? "Отключить активность" : "Стать активным водителем";
  if (lang === "uz") return value ? "Faollikni o‘chirish" : "Faol haydovchi bo‘lish";
  if (lang === "ar") return value ? "إيقاف النشاط" : "تفعيل السائق";
  if (lang === "kz") return value ? "Белсенділікті өшіру" : "Белсенді жүргізуші болу";
  return value ? "Turn activity off" : "Become active driver";
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
    return () => {
      cancelled = true;
    };
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
              <button className="button-secondary full" onClick={toggleOnline}>{toggleText(lang, online)}</button>
            </div>
            <ActionCard href={`${APP_ROUTES.cityOffers}?kind=passenger`} title={t(lang, "cityOrdersPassengers")} text={lang === "ru" ? "Лист заказов, ожидающих водителя." : t(lang, "availableOffers")} />
            <ActionCard href={APP_ROUTES.currentTrip} title={t(lang, "currentTrip")} text={lang === "ru" ? "Текущая поездка, карта и статус." : t(lang, "chat")} />
            <ActionCard href={APP_ROUTES.profile} title={t(lang, "profile")} text={lang === "ru" ? "Смена роли и данные водителя." : t(lang, "profileDescription")} />
          </>
        ) : (
          <>
            <ActionCard href={`${APP_ROUTES.cityCreate}?role=passenger`} title={t(lang, "fastOrder")} text={lang === "ru" ? "Создать городской заказ." : t(lang, "cityMode")} />
            <ActionCard href={APP_ROUTES.cityMyOrders} title={t(lang, "cityMyOrders")} text={lang === "ru" ? "Ваши заказы и поиск водителя." : t(lang, "status")} />
            <ActionCard href={APP_ROUTES.currentTrip} title={t(lang, "currentTrip")} text={lang === "ru" ? "Поездка, водитель и карта." : t(lang, "chat")} />
          </>
        )}
      </div>

      <BottomNav />
    </main>
  );
}
