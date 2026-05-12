"use client";

import { useMemo, useState } from "react";
import { Check, Clock, Eye, Navigation } from "lucide-react";

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

export function OrderCard({ order, actionLabel, onAction, onCounterOffer, disabled }: any) {
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
    <article className="order-card">
      <div className="order-card-inner">
        <div className="order-topline">
          <span className="order-badge">Заказ №{order.id}</span>
          <span className="order-seen"><Eye size={14} /> {order.seen_by_drivers ?? 0}</span>
        </div>

        <div className="route-panel">
          <div className="route-line" />
          <div className="route-point">
            <span className="route-dot" />
            <div>
              <div className="route-kicker">Откуда</div>
              <p className="route-address">{order.pickup_address || "Адрес отправления не указан"}</p>
            </div>
          </div>
          <div className="route-point">
            <span className="route-dot end" />
            <div>
              <div className="route-kicker">Куда</div>
              <p className="route-address muted">{order.destination_address || "Адрес назначения не указан"}</p>
            </div>
          </div>
        </div>

        <div className="metric-grid">
          <div className="metric-card">
            <div className="metric-label">Дистанция</div>
            <div className="metric-value flex items-center gap-1.5"><Navigation size={15} /> {formatNumber(order.estimated_distance_km)} km</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Время</div>
            <div className="metric-value flex items-center gap-1.5"><Clock size={15} /> {formatNumber(order.estimated_duration_min)} min</div>
          </div>
        </div>

        <div className="price-row">
          <div>
            <div className="metric-label">Цена пассажира</div>
            <div className="price-value">{formatNumber(order.passenger_price)}<span className="price-currency">{currency}</span></div>
          </div>
          {actionLabel ? (
            <button type="button" onClick={onAction} disabled={disabled} className="button primary min-w-[132px]">
              {disabled ? "Выполняем..." : actionLabel}
            </button>
          ) : null}
        </div>

        {onCounterOffer ? (
          <div className="bid-panel">
            <div>
              <h3 className="bid-title">Встречное предложение</h3>
              <p className="bid-subtitle">Крупные кнопки для быстрого выбора цены</p>
            </div>

            <div className="bid-grid">
              {percentOffers.map((offer) => (
                <button key={offer.percent} type="button" disabled={disabled || !basePrice} onClick={() => sendCounterOffer(offer.value)} className="bid-button">
                  +{offer.percent}%
                  <span>{formatMoney(offer.value, currency)}</span>
                </button>
              ))}
            </div>

            <div className="bid-grid">
              {steps.map((step) => (
                <button key={step} type="button" disabled={disabled || !basePrice} onClick={() => sendCounterOffer(basePrice + step)} className="bid-button">
                  +{formatNumber(step)}
                  <span>{currency}</span>
                </button>
              ))}
            </div>

            <div className="manual-bid">
              <input
                type="number"
                min="0"
                inputMode="numeric"
                value={value}
                onChange={(event) => setValue(event.target.value)}
                className="it-input"
                placeholder="Своя цена"
              />
              <button type="button" disabled={disabled || !value} onClick={() => sendCounterOffer(Number(value))} className="send-bid" aria-label="Отправить цену">
                <Check size={24} />
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </article>
  );
}
