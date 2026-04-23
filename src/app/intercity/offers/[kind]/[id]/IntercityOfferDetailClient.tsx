"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import BottomNav from "@/components/BottomNav";
import MapBox from "@/components/MapBox";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { api, IntercityOffer } from "@/lib/api";
import { APP_ROUTES } from "@/lib/constants";
import { t } from "@/lib/i18n";

type IntercityOfferDetailClientProps = {
  kind: string;
  id: string;
};

function pickupModeLabel(lang: string, mode?: string | null) {
  if (mode === "driver_location") return lang === "ru" ? "Встреча у водителя" : "Meet at driver location";
  if (mode === "driver_pickup") return lang === "ru" ? "Водитель сам заберёт" : "Driver pickup";
  return lang === "ru" ? "Уточнить в чате" : "Clarify in chat";
}

export default function IntercityOfferDetailClient({ kind, id }: IntercityOfferDetailClientProps) {
  const { lang, sessionToken, isReady } = useApp();
  const [item, setItem] = useState<IntercityOffer | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function load() {
    if (!isReady || !sessionToken) return;
    try {
      const data = await api.intercityOfferDetail(sessionToken, kind, Number(id));
      setItem(data.item);
    } catch {
      setItem(null);
    }
  }

  useEffect(() => { void load(); }, [kind, id, isReady, sessionToken]);

  async function accept() {
    if (!sessionToken) return;
    try {
      setBusy(true);
      const result = await api.acceptIntercityOffer(sessionToken, kind, Number(id));
      window.location.href = `${APP_ROUTES.currentTrip}?tripType=${result.trip_type}&tripId=${result.trip_id}`;
    } catch (error) {
      setMessage(error instanceof Error ? error.message : t(lang, "operationFailed"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title={t(lang, "routeCard")} subtitle={t(lang, "details")} />
        {message ? <div className="notice">{message}</div> : null}

        {!item ? (
          <div className="card">{t(lang, "loading")}</div>
        ) : (
          <>
            <div className="card stack">
              <div className="list-row">
                <div className="card-title">{item.from_city} → {item.to_city}</div>
                <span className="pill">{item.kind}</span>
              </div>

              <div className="info-grid">
                <div className="info-block"><div className="info-label">{t(lang, "date")}</div><div className="info-value">{item.date}</div></div>
                <div className="info-block"><div className="info-label">{t(lang, "time")}</div><div className="info-value">{item.time}</div></div>
                <div className="info-block"><div className="info-label">{t(lang, "seats")}</div><div className="info-value">{item.seats}</div></div>
                <div className="info-block"><div className="info-label">{t(lang, "price")}</div><div className="info-value">{item.price}</div></div>
              </div>

              <div className="info-block">
                <div className="info-label">Pickup</div>
                <div className="info-value">{pickupModeLabel(lang, item.pickup_mode)}</div>
              </div>

              {item.comment ? <div className="info-block"><div className="info-label">{t(lang, "comment")}</div><div className="info-value">{item.comment}</div></div> : null}

              <div className="actions-row">
                {item.can_accept ? <button className="button-main" onClick={accept}>{busy ? t(lang, "loading") : t(lang, "acceptOffer")}</button> : null}
                {item.active_trip_id || item.status === "accepted" || item.status === "in_progress" ? (
                  <Link href={`${APP_ROUTES.currentTrip}?tripType=intercity_${item.kind}&tripId=${item.id}`} className="button-secondary">{t(lang, "openTrip")}</Link>
                ) : null}
              </div>
            </div>

            <MapBox title={t(lang, "map")} fromLabel="A" toLabel="B" embedUrl={item.map_embed_url || undefined} actionHref={item.map_action_url || undefined} provider={item.map_provider || undefined} />
          </>
        )}
      </div>

      <BottomNav />
    </main>
  );
}
