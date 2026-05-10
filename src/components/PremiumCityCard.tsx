"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { CityOrder } from "@/lib/api";
import { APP_ROUTES, AppLanguage, currencyForCountry } from "@/lib/constants";
import { t } from "@/lib/i18n";

type PremiumCityCardProps = {
  item: CityOrder;
  lang: AppLanguage;
  isDriver: boolean;
  onRaisePrice?: (orderId: number, price: number) => Promise<void>;
};

const COUNTRY_STEPS: Record<string, number[]> = {
  uz: [1000, 5000, 10000],
  kz: [500, 1000, 3000],
  tr: [20, 50, 100],
  sa: [5, 10, 20],
};

function formatNumber(value?: number | null) {
  if (value == null || Number.isNaN(Number(value))) return "-";
  return Number(value).toLocaleString("ru-RU");
}

function formatMoney(value?: number | null, currency?: string | null) {
  if (value == null || Number.isNaN(Number(value))) return "-";
  return `${Number(value).toLocaleString("ru-RU")} ${currency || ""}`.trim();
}

export default function PremiumCityCard({ item, lang, isDriver, onRaisePrice }: PremiumCityCardProps) {
  const currency = item.currency || currencyForCountry(item.country);
  const basePrice = Number(item.price || item.recommended_price || 0);
  const steps = COUNTRY_STEPS[(item.country || "").toLowerCase()] || COUNTRY_STEPS.uz;
  const [manualPrice, setManualPrice] = useState(basePrice ? String(basePrice) : "");
  const [isSending, setIsSending] = useState(false);
  const [localError, setLocalError] = useState("");

  const percentOffers = useMemo(() => {
    return [10, 20, 30].map((percent) => ({
      percent,
      value: Math.round(basePrice + basePrice * (percent / 100)),
    }));
  }, [basePrice]);

  async function submitPrice(nextPrice: number) {
    if (!onRaisePrice || !nextPrice || nextPrice <= 0) return;
    try {
      setIsSending(true);
      setLocalError("");
      await onRaisePrice(item.id, nextPrice);
      setManualPrice(String(nextPrice));
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : t(lang, "operationFailed"));
    } finally {
      setIsSending(false);
    }
  }

  return (
    <article className="order-card">
      <div className="order-card-inner">
        <div className="order-card-role">
          <span className={`pill ${item.role === "driver" ? "role-driver" : "role-passenger"}`}>
            {item.role === "driver" ? t(lang, "driverMode") : t(lang, "passengerMode")}
          </span>
        </div>

        <div className="order-card-head">
          <div className="order-city">{item.city || "City"}</div>
          <h3 className="order-price-main">{formatMoney(item.price || item.recommended_price, currency)}</h3>
        </div>

        <div className="route-panel">
          <div className="route-rail">
            <span className="route-dot route-dot-a" />
            <span className="route-line" />
            <span className="route-dot route-dot-b" />
          </div>
          <div className="route-copy">
            <div className="route-label">A</div>
            <div className="route-address">{item.from_address || "-"}</div>
            <div className="route-label route-label-b">B</div>
            <div className="route-address">{item.to_address || "-"}</div>
          </div>
        </div>

        <div className="order-metrics">
          <div className="order-metric">
            <div className="metric-label">Route</div>
            <div className="metric-value">{formatNumber(item.estimated_distance_km)} km</div>
            <div className="metric-sub">{formatNumber(item.estimated_trip_min)} min</div>
          </div>
          <div className="order-metric">
            <div className="metric-label">To client</div>
            <div className="metric-value">{formatNumber(item.driver_distance_km)} km</div>
            <div className="metric-sub">{formatNumber(item.driver_eta_min)} min</div>
          </div>
        </div>

        <div className="order-metrics">
          <div className="order-metric order-metric-strong">
            <div className="metric-label">{t(lang, "price")}</div>
            <div className="metric-value big">{formatMoney(item.price, currency)}</div>
          </div>
          <div className="order-metric order-metric-strong">
            <div className="metric-label">{t(lang, "driversSeen")}</div>
            <div className="metric-value big">{item.seen_by_drivers ?? 0}</div>
          </div>
        </div>

        {isDriver && onRaisePrice ? (
          <div className="bid-panel">
            <div className="bid-head">
              <div>
                <div className="bid-title">Counter offer</div>
                <div className="bid-subtitle">Large buttons for fast bidding</div>
              </div>
              <span className="pill small">Bid</span>
            </div>

            <div className="bid-grid percent-grid">
              {percentOffers.map((offer) => (
                <button key={offer.percent} type="button" disabled={isSending || !basePrice} onClick={() => submitPrice(offer.value)} className="bid-button">
                  +{offer.percent}%
                  <span>{formatMoney(offer.value, currency)}</span>
                </button>
              ))}
            </div>

            <div className="bid-grid amount-grid">
              {steps.map((step) => (
                <button key={step} type="button" disabled={isSending || !basePrice} onClick={() => submitPrice(basePrice + step)} className="bid-button secondary">
                  +{formatNumber(step)}
                  <span>{currency}</span>
                </button>
              ))}
            </div>

            <div className="manual-bid-row">
              <input className="field" inputMode="numeric" type="number" min="0" value={manualPrice} onChange={(event) => setManualPrice(event.target.value)} placeholder="Your price" />
              <button type="button" disabled={isSending || !manualPrice} onClick={() => submitPrice(Number(manualPrice))} className="button-main manual-bid-button">
                {isSending ? "..." : t(lang, "send")}
              </button>
            </div>

            {localError ? <div className="bid-error">{localError}</div> : null}
          </div>
        ) : null}

        <div className="order-actions">
          <Link href={`${APP_ROUTES.cityOffers}/${item.id}`} className="button-secondary order-action">{t(lang, "details")}</Link>
          {item.active_trip_id ? <Link href={`${APP_ROUTES.currentTrip}?tripType=city_trip&tripId=${item.active_trip_id}`} className="button-main order-action">{t(lang, "openTrip")}</Link> : null}
        </div>

        {item.comment ? <div className="order-comment">{item.comment}</div> : null}
      </div>
    </article>
  );
}
