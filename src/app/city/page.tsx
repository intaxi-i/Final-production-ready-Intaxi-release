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
  if (lang === "ru") return value ? "Онлайн включен" : "Онлайн выключен";
  if (lang === "uz") return value ? "On line yoqilgan" : "On line o‘chiq";
  if (lang === "ar") return value ? "متصل الآن" : "غير متصل";
  if (lang === "kz") return value ? "Онлайн қосулы" : "Онлайн өшірулі";
  return value ? "Online enabled" : "Online disabled";
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
            <ActionCard href={`${APP_ROUTES.cityOffers}?kind=passenger`} title={t(lang, "cityOrdersPassengers")} text={onlineLabel(lang, online)} />
            <button className="button-secondary full" onClick={toggleOnline}>{onlineLabel(lang, online)}</button>
            <ActionCard href={`${APP_ROUTES.cityCreate}?role=driver`} title={t(lang, "createOffer")} text={t(lang, "status")} />
            <ActionCard href={APP_ROUTES.cityMyOrders} title={t(lang, "cityMyOrders")} text={t(lang, "status")} />
            <ActionCard href={APP_ROUTES.currentTrip} title={t(lang, "currentTrip")} text={t(lang, "chat")} />
          </>
        ) : (
          <>
            <ActionCard href={`${APP_ROUTES.cityCreate}?role=passenger`} title={t(lang, "fastOrder")} text={t(lang, "cityMode")} />
            <ActionCard href={`${APP_ROUTES.cityOffers}?kind=driver`} title={t(lang, "availableOffers")} text={t(lang, "cityOffersDrivers")} />
            <ActionCard href={APP_ROUTES.cityMyOrders} title={t(lang, "cityMyOrders")} text={t(lang, "status")} />
            <ActionCard href={APP_ROUTES.currentTrip} title={t(lang, "currentTrip")} text={t(lang, "chat")} />
          </>
        )}
      </div>

      <BottomNav />
    </main>
  );
}
