"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import BottomNav from "@/components/BottomNav";
import MapBox from "@/components/MapBox";
import PageHeader from "@/components/PageHeader";
import TripChat from "@/components/TripChat";
import { useApp } from "@/context/AppContext";
import { api } from "@/lib/api";
import { getCurrentPosition } from "@/lib/geo";
import { t } from "@/lib/i18n";

function fallbackActionLabel(lang: string): string {
  if (lang === "ru") return "Открыть маршрут";
  if (lang === "uz") return "Marshrutni ochish";
  if (lang === "ar") return "فتح المسار";
  if (lang === "kz") return "Маршрутты ашу";
  return "Open route";
}

function pickupModeLabel(lang: string, mode?: string) {
  if (mode === "driver_location") return lang === "ru" ? "Встреча у водителя" : "Meet at driver location";
  if (mode === "driver_pickup") return lang === "ru" ? "Водитель заберёт пассажира" : "Driver pickup";
  return lang === "ru" ? "Уточнить в чате" : "Clarify in chat";
}

function cancelLabel(lang: string) {
  if (lang === "ru") return "Отменить";
  if (lang === "uz") return "Bekor qilish";
  if (lang === "ar") return "إلغاء";
  if (lang === "kz") return "Болдырмау";
  return "Cancel";
}

function vehicleDetailsLabel(lang: string) {
  if (lang === "ru") return "Данные машины";
  if (lang === "uz") return "Mashina ma'lumotlari";
  if (lang === "ar") return "بيانات السيارة";
  if (lang === "kz") return "Көлік деректері";
  return "Vehicle details";
}

function nextPointLabel(lang: string) {
  if (lang === "ru") return "Следующая точка";
  if (lang === "uz") return "Keyingi nuqta";
  if (lang === "ar") return "النقطة التالية";
  if (lang === "kz") return "Келесі нүкте";
  return "Next point";
}

export default function CurrentTripPage() {
  const { lang, sessionToken, isReady, user } = useApp();
  const [item, setItem] = useState<any | null>(null);
  const [queryTripId, setQueryTripId] = useState(0);
  const [queryTripType, setQueryTripType] = useState("");
  const tripId = Number(queryTripId || item?.id || 0);
  const tripType = queryTripType || item?.trip_type || "generic";

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setQueryTripId(Number(params.get("tripId") || 0));
    setQueryTripType(params.get("tripType") || "");
  }, []);

  const load = useCallback(async () => {
    if (!isReady || !sessionToken) return;
    try {
      if (queryTripType === "city_trip" && queryTripId) {
        const data = await api.cityTripDetail(sessionToken, queryTripId);
        setItem({ ...data.item, trip_type: "city_trip" });
        return;
      }
      if ((queryTripType === "intercity_route" || queryTripType === "intercity_request") && queryTripId) {
        const kind = queryTripType === "intercity_route" ? "route" : "request";
        const data = await api.intercityOfferDetail(sessionToken, kind, queryTripId);
        if (!data.item.is_mine && data.item.pickup_mode === "ask_driver") {
          try {
            await api.grantIntercityChatAccess(sessionToken, kind, queryTripId);
          } catch {}
        }
        setItem({ ...data.item, trip_type: queryTripType });
        return;
      }
      const data = await api.currentTrip(sessionToken);
      setItem(data.item);
    } catch {
      setItem(null);
    }
  }, [isReady, sessionToken, queryTripId, queryTripType]);

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 6000);
    return () => window.clearInterval(timer);
  }, [load]);

  async function updateCityStatus(status: string) {
    if (!sessionToken || !tripId) return;
    try {
      const data = await api.updateCityTripStatus(sessionToken, tripId, status);
      setItem({ ...data.item, trip_type: "city_trip" });
    } catch {}
  }

  async function updateIntercityStatus(status: string) {
    if (!sessionToken || !tripId) return;
    try {
      if (tripType === "intercity_route" || item?.trip_type === "intercity_route") {
        await api.updateIntercityRouteStatus(sessionToken, tripId, status);
      } else {
        await api.updateIntercityRequestStatus(sessionToken, tripId, status);
      }
      await load();
    } catch {}
  }

  const tripTitle = useMemo(() => {
    if (!item) return t(lang as any, "noData");
    if (item.trip_type === "city_trip" || item.trip_type === "city") {
      return `${item.city || ""}: ${item.from_address || ""}${item.to_address ? ` → ${item.to_address}` : ""}`;
    }
    return `${item.from_city || ""} → ${item.to_city || ""}`;
  }, [item, lang]);

  const isDriver = item?.driver_tg_id && user?.tg_id === item.driver_tg_id;
  const isIntercityParticipant = Boolean(item && user?.tg_id && [item.creator_tg_id, item.accepted_by_tg_id].includes(user.tg_id));
  const intercityAccepted = Boolean(item?.status === "accepted" || item?.status === "in_progress");

  useEffect(() => {
    if (!sessionToken || !tripId || item?.trip_type !== "city_trip" || !isDriver) return;
    if (["completed", "cancelled"].includes(String(item?.status || ""))) return;
    let cancelled = false;

    async function pushLocation() {
      try {
        const pos = await getCurrentPosition();
        if (cancelled) return;
        await api.updateDriverLocation(sessionToken, { trip_id: tripId, lat: pos.lat, lng: pos.lng });
      } catch {}
    }

    void pushLocation();
    const timer = window.setInterval(() => {
      void pushLocation();
    }, 15000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [sessionToken, tripId, item?.trip_type, item?.status, isDriver]);

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title={t(lang as any, "currentTrip")} subtitle={t(lang as any, "chat")} />

        <div className="card stack">
          {!item ? (
            <div className="muted">{t(lang as any, "noData")}</div>
          ) : (
            <>
              <div className="card-title">{tripTitle}</div>
              <div className="info-grid">
                <div className="info-block"><div className="info-label">{t(lang as any, "status")}</div><div className="info-value">{item.status || t(lang as any, "active")}</div></div>
                <div className="info-block"><div className="info-label">{t(lang as any, "price")}</div><div className="info-value">{item.price ?? 0}</div></div>
              </div>

              {item.trip_type === "city_trip" ? (
                <>
                  <div className="info-grid">
                    <div className="info-block"><div className="info-label">{t(lang as any, "otherSide")}</div><div className="info-value">{isDriver ? item.passenger_name || "—" : item.driver_name || "—"}</div></div>
                    <div className="info-block"><div className="info-label">{vehicleDetailsLabel(lang)}</div><div className="info-value">{item.vehicle ? `${item.vehicle.brand || ""} ${item.vehicle.model || ""}` : "—"}</div></div>
                    <div className="info-block"><div className="info-label">{t(lang as any, "vehiclePlate")}</div><div className="info-value">{item.vehicle?.plate || "—"}</div></div>
                    <div className="info-block"><div className="info-label">{t(lang as any, "vehicleColor")}</div><div className="info-value">{item.vehicle?.color || "—"}</div></div>
                  </div>

                  {item.status === "driver_arrived" || item.status === "in_progress" ? (
                    <div className="info-block">
                      <div className="info-label">{nextPointLabel(lang)}</div>
                      <div className="info-value">{item.to_address || "—"}</div>
                    </div>
                  ) : null}

                  {isDriver ? (
                    <div className="actions-row">
                      {(item.status === "accepted" || item.status === "driver_on_way") ? <button className="button-secondary" onClick={() => updateCityStatus("driver_on_way")}>{t(lang as any, "onWay")}</button> : null}
                      {(item.status === "accepted" || item.status === "driver_on_way") ? <button className="button-secondary" onClick={() => updateCityStatus("driver_arrived")}>{t(lang as any, "arrived")}</button> : null}
                      {item.status === "driver_arrived" ? <button className="button-main" onClick={() => updateCityStatus("in_progress")}>{t(lang as any, "inProgress")}</button> : null}
                      {item.status === "in_progress" ? <button className="button-main" onClick={() => updateCityStatus("completed")}>{t(lang as any, "completed")}</button> : null}
                    </div>
                  ) : null}
                </>
              ) : (
                <>
                  <div className="info-block"><div className="info-label">Pickup</div><div className="info-value">{pickupModeLabel(lang, item.pickup_mode)}</div></div>
                  {intercityAccepted && isIntercityParticipant ? (
                    <div className="actions-row">
                      <button className="button-secondary" onClick={() => updateIntercityStatus("in_progress")}>{t(lang as any, "inProgress")}</button>
                      <button className="button-main" onClick={() => updateIntercityStatus("completed")}>{t(lang as any, "completed")}</button>
                      <button className="button-danger" onClick={() => updateIntercityStatus("cancelled")}>{cancelLabel(lang)}</button>
                    </div>
                  ) : null}
                </>
              )}

              {item.comment ? <div className="info-block"><div className="info-label">{t(lang as any, "comment")}</div><div className="info-value">{item.comment}</div></div> : null}
            </>
          )}
        </div>

        <MapBox title={t(lang as any, "map")} fromLabel="A" toLabel="B" subtitle={item?.eta_min ? `${t(lang as any, "eta")}: ${item.eta_min} min` : t(lang as any, "waiting")} actionLabel={item?.map_action_url ? fallbackActionLabel(lang) : undefined} actionHref={item?.map_action_url} embedUrl={item?.map_embed_url} provider={item?.map_provider} />

        {tripId ? <TripChat tripId={tripId} tripType={tripType} /> : null}
      </div>
      <BottomNav />
    </main>
  );
}
