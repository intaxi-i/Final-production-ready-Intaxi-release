"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import BottomNav from "@/components/BottomNav";
import MapBox from "@/components/MapBox";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { api, CityOrder } from "@/lib/api";
import { APP_ROUTES } from "@/lib/constants";
import { t } from "@/lib/i18n";

export default function CityOfferDetailClient({ id }: { id: string }) {
  const { lang, sessionToken, isReady } = useApp();
  const [item, setItem] = useState<CityOrder | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!isReady || !sessionToken) return;

    try {
      const data = await api.cityOfferDetail(sessionToken, Number(id));
      setItem(data.item);
    } catch {
      setItem(null);
    }
  }, [id, isReady, sessionToken]);

  useEffect(() => {
    void load();
  }, [load]);

  async function acceptOffer() {
    if (!sessionToken || !item) return;

    try {
      setLoading(true);
      const data = await api.acceptCityOffer(sessionToken, item.id);
      window.location.href = `${APP_ROUTES.currentTrip}?tripType=city_trip&tripId=${data.trip_id}`;
    } finally {
      setLoading(false);
    }
  }

  const canAccept =
    item &&
    !item.is_mine &&
    !item.active_trip_id &&
    item.status === "active";

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title={t(lang, "routeCard")} subtitle={t(lang, "cityMode")} />

        {!item ? (
          <div className="card">{t(lang, "loading")}</div>
        ) : (
          <>
            <div className="card stack">
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

              <div className="info-grid">
                <div className="info-block">
                  <div className="info-label">{t(lang, "fromAddress")}</div>
                  <div className="info-value">{item.from_address}</div>
                </div>

                <div className="info-block">
                  <div className="info-label">{t(lang, "toAddress")}</div>
                  <div className="info-value">{item.to_address || "—"}</div>
                </div>

                <div className="info-block">
                  <div className="info-label">{t(lang, "price")}</div>
                  <div className="info-value">{item.price}</div>
                </div>

                <div className="info-block">
                  <div className="info-label">{t(lang, "tripDistance")}</div>
                  <div className="info-value">
                    {item.estimated_distance_km ?? "—"} km
                  </div>
                </div>

                <div className="info-block">
                  <div className="info-label">{t(lang, "driverDistance")}</div>
                  <div className="info-value">
                    {item.driver_distance_km ?? "—"} km
                  </div>
                </div>

                <div className="info-block">
                  <div className="info-label">{t(lang, "eta")}</div>
                  <div className="info-value">{item.driver_eta_min ?? "—"} min</div>
                </div>
              </div>

              {item.role === "driver" && item.vehicle ? (
                <div className="info-grid">
                  <div className="info-block">
                    <div className="info-label">{t(lang, "otherSide")}</div>
                    <div className="info-value">{item.creator_name || "—"}</div>
                  </div>

                  <div className="info-block">
                    <div className="info-label">{t(lang, "car")}</div>
                    <div className="info-value">
                      {item.vehicle.brand || ""} {item.vehicle.model || ""}
                    </div>
                  </div>
                </div>
              ) : null}

              {item.comment ? (
                <div className="info-block">
                  <div className="info-label">{t(lang, "comment")}</div>
                  <div className="info-value">{item.comment}</div>
                </div>
              ) : null}

              <div className="actions-row">
                {item.active_trip_id ? (
                  <Link
                    href={`${APP_ROUTES.currentTrip}?tripType=city_trip&tripId=${item.active_trip_id}`}
                    className="button-main"
                  >
                    {t(lang, "openTrip")}
                  </Link>
                ) : null}

                {canAccept ? (
                  <button className="button-main" onClick={acceptOffer}>
                    {loading ? t(lang, "loading") : t(lang, "acceptOffer")}
                  </button>
                ) : null}
              </div>
            </div>

            <MapBox
              title={t(lang, "map")}
              fromLabel="A"
              toLabel="B"
              subtitle={`${t(lang, "tripDistance")}: ${
                item.estimated_distance_km ?? "—"
              } km · ${t(lang, "eta")}: ${item.estimated_trip_min ?? "—"} min`}
            />
          </>
        )}
      </div>

      <BottomNav />
    </main>
  );
}