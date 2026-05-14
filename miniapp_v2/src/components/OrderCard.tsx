"use client";

import { useMemo, useState } from "react";
import { Check, Clock, Eye, Navigation } from "lucide-react";
import { t } from "@/lib/i18n";

const COUNTRY_STEPS: Record<string, number[]> = {
  uz: [1000, 5000, 10000],
  kz: [500, 1000, 3000],
  tr: [20, 50, 100],
  sa: [5, 10, 20],
};

function formatNumber(value?: number | null) {
  if (value == null || Number.isNaN(Number(value))) return "--";
  return Number(value).toLocaleString("ru-RU");
}

function formatMoney(value?: number | null, currency?: string | null) {
  if (value == null || Number.isNaN(Number(value))) return "--";
  return `${Number(value).toLocaleString("ru-RU")} ${currency || ""}`.trim();
}

function roundCounterPrice(value: number, countryCode: string) {
  if (countryCode === "uz") return Math.round(value / 1000) * 1000;
  if (countryCode === "kz") return Math.round(value / 100) * 100;
  return Math.round(value);
}

export function OrderCard({ order, actionLabel, onAction, onCounterOffer, disabled, lang }: any) {
  const countryCode = String(order.country_code || "uz").toLowerCase();
  const basePrice = Number(order.passenger_price || 0);
  const currency = order.currency || "";
  const steps = COUNTRY_STEPS[countryCode] || COUNTRY_STEPS.uz;
  const [value, setValue] = useState(basePrice ? String(basePrice) : "");

  const percentOffers = useMemo(
    () => [10, 20, 30].map((percent) => ({ percent, value: roundCounterPrice(basePrice + basePrice * (percent / 100), countryCode) })),
    [basePrice, countryCode],
  );

  function sendCounterOffer(nextPrice: number) {
    if (!onCounterOffer || !nextPrice || nextPrice <= 0) return;
    const rounded = roundCounterPrice(nextPrice, countryCode);
    onCounterOffer(rounded);
    setValue(String(rounded));
  }

  return (
    <article className="order-card min-w-0 overflow-hidden">
      <div className="order-card-inner min-w-0">
        <div className="order-topline min-w-0 gap-2">
          <span className="order-badge min-w-0 max-w-full truncate">{t(lang, 'order')} №{order.id}</span>
          <span className="order-seen shrink-0"><Eye size={14} /> {order.seen_by_drivers ?? 0}</span>
        </div>

        <div className="route-panel min-w-0 overflow-hidden">
          <div className="route-line" />
          <div className="route-point min-w-0">
            <span className="route-dot shrink-0" />
            <div className="min-w-0">
              <div className="route-kicker">{t(lang, 'fromWhere')}</div>
              <p className="route-address break-words">{order.pickup_address || t(lang, 'pickupAddressMissing')}</p>
            </div>
          </div>
          <div className="route-point min-w-0">
            <span className="route-dot end shrink-0" />
            <div className="min-w-0">
              <div className="route-kicker">{t(lang, 'toWhere')}</div>
              <p className="route-address muted break-words">{order.destination_address || t(lang, 'destinationAddressMissing')}</p>
            </div>
          </div>
        </div>

        <div className="metric-grid">
          <div className="metric-card min-w-0 overflow-hidden">
            <div className="metric-label">{t(lang, 'distance')}</div>
            <div className="metric-value flex items-center gap-1.5 break-words"><Navigation size={15} className="shrink-0" /> {formatNumber(order.estimated_distance_km)} km</div>
          </div>
          <div className="metric-card min-w-0 overflow-hidden">
            <div className="metric-label">{t(lang, 'duration')}</div>
            <div className="metric-value flex items-center gap-1.5 break-words"><Clock size={15} className="shrink-0" /> {formatNumber(order.estimated_duration_min)} min</div>
          </div>
        </div>

        <div className="price-row min-w-0 gap-3">
          <div className="min-w-0">
            <div className="metric-label">{t(lang, 'passengerPrice')}</div>
            <div className="price-value break-words">{formatNumber(order.passenger_price)}<span className="price-currency">{currency}</span></div>
          </div>
          {actionLabel ? (
            <button type="button" onClick={onAction} disabled={disabled} className="button primary min-w-[132px] shrink-0">
              {disabled ? t(lang, 'processing') : actionLabel}
            </button>
          ) : null}
        </div>

        {onCounterOffer ? (
          <div className="bid-panel min-w-0 overflow-hidden">
            <div className="min-w-0">
              <h3 className="bid-title break-words">{t(lang, 'counterOffer')}</h3>
              <p className="bid-subtitle break-words">{t(lang, 'counterOfferHint')}</p>
            </div>

            <div className="bid-grid">
              {percentOffers.map((offer) => (
                <button key={offer.percent} type="button" disabled={disabled || !basePrice} onClick={() => sendCounterOffer(offer.value)} className="bid-button min-w-0 overflow-hidden">
                  +{offer.percent}%
                  <span className="break-words">{formatMoney(offer.value, currency)}</span>
                </button>
              ))}
            </div>

            <div className="bid-grid">
              {steps.map((step) => (
                <button key={step} type="button" disabled={disabled || !basePrice} onClick={() => sendCounterOffer(basePrice + step)} className="bid-button min-w-0 overflow-hidden">
                  +{formatNumber(step)}
                  <span className="break-words">{currency}</span>
                </button>
              ))}
            </div>

            <div className="manual-bid min-w-0">
              <input
                type="number"
                min="0"
                inputMode="numeric"
                value={value}
                onChange={(event) => setValue(event.target.value)}
                className="it-input min-w-0"
                placeholder={t(lang, 'customPrice')}
              />
              <button type="button" disabled={disabled || !value} onClick={() => sendCounterOffer(Number(value))} className="send-bid shrink-0" aria-label={t(lang, 'sendPrice')}>
                <Check size={24} />
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </article>
  );
}
