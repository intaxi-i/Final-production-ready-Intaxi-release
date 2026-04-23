"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import AddressField from "@/components/AddressField";
import BottomNav from "@/components/BottomNav";
import LocationFields from "@/components/LocationFields";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { api, TariffItem } from "@/lib/api";
import { haversineKm } from "@/lib/geo";
import { formatUzLocation, guessUzRegionFromCity } from "@/lib/locations";
import { t } from "@/lib/i18n";

function swapLabel(lang: string) {
  if (lang === "ru") return "Поменять точки";
  if (lang === "uz") return "Nuqtalarni almashtirish";
  if (lang === "ar") return "تبديل النقطتين";
  if (lang === "kz") return "Нүктелерді ауыстыру";
  return "Swap points";
}

function formatMoney(value: number | null, currency: string) {
  if (value == null || Number.isNaN(value)) return "—";
  return `${Number(value.toFixed(2))} ${currency}`;
}

export default function CityCreatePage() {
  const { lang, sessionToken, user } = useApp();
  const [forcedRole, setForcedRole] = useState<"passenger" | "driver" | "">("");
  const role = forcedRole || (user?.active_role as "passenger" | "driver") || "passenger";
  const [country, setCountry] = useState(user?.country || "uz");
  const [regionKey, setRegionKey] = useState(guessUzRegionFromCity(user?.city || ""));
  const [city, setCity] = useState(user?.city || "");
  const [fromAddress, setFromAddress] = useState("");
  const [toAddress, setToAddress] = useState("");
  const [fromLat, setFromLat] = useState("");
  const [fromLng, setFromLng] = useState("");
  const [toLat, setToLat] = useState("");
  const [toLng, setToLng] = useState("");
  const [seats, setSeats] = useState("1");
  const [price, setPrice] = useState("");
  const [recommendedPrice, setRecommendedPrice] = useState<number | null>(null);
  const [currency, setCurrency] = useState("UZS");
  const [tariffHint, setTariffHint] = useState("");
  const [distanceKm, setDistanceKm] = useState<number | null>(null);
  const [comment, setComment] = useState("");
  const [message, setMessage] = useState("");
  const [createdOrderId, setCreatedOrderId] = useState<number | null>(null);
  const [driversSeen, setDriversSeen] = useState(0);
  const [secondsPassed, setSecondsPassed] = useState(0);
  const [tariffs, setTariffs] = useState<Record<string, TariffItem>>({});

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const nextRole = params.get("role");
    if (nextRole === "driver" || nextRole === "passenger") setForcedRole(nextRole);
    const from = params.get("from");
    const to = params.get("to");
    if (from) setFromAddress(from);
    if (to) setToAddress(to);
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadTariffs() {
      if (!sessionToken) return;
      try {
        const data = await api.tariffs(sessionToken);
        if (cancelled) return;
        const next: Record<string, TariffItem> = {};
        data.items.forEach((item) => {
          next[item.country] = item;
        });
        setTariffs(next);
      } catch {}
    }
    void loadTariffs();
    return () => {
      cancelled = true;
    };
  }, [sessionToken]);

  useEffect(() => {
    const tariff = tariffs[country];
    if (!tariff) return;
    setCurrency(tariff.currency);
    setTariffHint(`~${tariff.price_per_km} ${tariff.currency}/km`);
  }, [country, tariffs]);

  useEffect(() => {
    const tariff = tariffs[country];
    const ready = fromLat && fromLng && toLat && toLng && tariff;
    if (!ready) {
      setRecommendedPrice(null);
      setDistanceKm(null);
      return;
    }
    const km = haversineKm(Number(fromLat), Number(fromLng), Number(toLat), Number(toLng));
    setDistanceKm(Number(km.toFixed(2)));
    setRecommendedPrice(Number((km * tariff.price_per_km).toFixed(2)));
  }, [fromLat, fromLng, toLat, toLng, country, tariffs]);

  useEffect(() => {
    if (!createdOrderId) return;
    const timer = window.setInterval(() => setSecondsPassed((prev) => prev + 1), 1000);
    return () => window.clearInterval(timer);
  }, [createdOrderId]);

  const cityValue = useMemo(() => {
    if (country === "uz" && regionKey && city) return formatUzLocation(regionKey, city, lang);
    return city;
  }, [country, regionKey, city, lang]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!sessionToken) return;
    if (!cityValue || !fromAddress.trim()) {
      setMessage(lang === "ru" ? "Заполните город и точку отправления" : t(lang, "operationFailed"));
      return;
    }
    if (role === "passenger" && !toAddress.trim()) {
      setMessage(lang === "ru" ? "Укажите пункт назначения" : t(lang, "operationFailed"));
      return;
    }
    try {
      const result = await api.createCityOrder(sessionToken, {
        role,
        country,
        city: cityValue,
        from_address: fromAddress.trim(),
        to_address: toAddress.trim(),
        seats: Number(seats || 1),
        price: price ? Number(price) : null,
        comment,
        recommended_price: recommendedPrice ?? undefined,
        from_lat: fromLat ? Number(fromLat) : null,
        from_lng: fromLng ? Number(fromLng) : null,
        to_lat: toLat ? Number(toLat) : null,
        to_lng: toLng ? Number(toLng) : null,
      });
      setCreatedOrderId(result.id);
      setDriversSeen(result.seen_by_drivers || 0);
      setSecondsPassed(0);
      if (!price && result.recommended_price != null) setPrice(String(result.recommended_price));
      if (result.currency) setCurrency(result.currency);
      if (result.tariff_hint) setTariffHint(result.tariff_hint);
      setMessage(lang === "ru" ? "Заказ/предложение создано" : t(lang, "postedSuccessfully"));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : t(lang, "operationFailed"));
    }
  }

  async function raisePrice() {
    if (!createdOrderId || !sessionToken) return;
    const nextPrice = Number(price || recommendedPrice || 0) + 5000;
    try {
      await api.raiseCityOrderPrice(sessionToken, createdOrderId, nextPrice);
      setPrice(String(nextPrice));
      setMessage(t(lang, "updatedSuccessfully"));
    } catch {
      setMessage(t(lang, "operationFailed"));
    }
  }

  function swapPoints() {
    setFromAddress(toAddress);
    setToAddress(fromAddress);
    setFromLat(toLat);
    setFromLng(toLng);
    setToLat(fromLat);
    setToLng(fromLng);
  }

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title={role === "driver" ? t(lang, "createOffer") : t(lang, "createOrder")} subtitle={role === "driver" ? t(lang, "driverMode") : t(lang, "passengerMode")} />
        {message ? <div className="notice">{message}</div> : null}

        <form className="card stack" onSubmit={handleSubmit}>
          <LocationFields lang={lang} country={country} setCountry={setCountry} regionKey={regionKey} setRegionKey={setRegionKey} city={city} setCity={setCity} />

          <AddressField
            lang={lang}
            label={t(lang, "fromAddress")}
            address={fromAddress}
            setAddress={setFromAddress}
            lat={fromLat}
            setLat={setFromLat}
            lng={fromLng}
            setLng={setFromLng}
            onResolved={({ countryCode, city: resolvedCity }) => {
              if (countryCode === "uz" || countryCode === "tr" || countryCode === "sa") setCountry(countryCode);
              if (resolvedCity) {
                if ((countryCode || country) === "uz") {
                  const guessed = guessUzRegionFromCity(resolvedCity);
                  if (guessed) setRegionKey(guessed);
                }
                setCity(resolvedCity);
              }
            }}
          />

          <AddressField
            lang={lang}
            label={t(lang, "toAddress")}
            address={toAddress}
            setAddress={setToAddress}
            lat={toLat}
            setLat={setToLat}
            lng={toLng}
            setLng={setToLng}
          />

          <button type="button" className="button-secondary full" onClick={swapPoints}>{swapLabel(lang)}</button>

          <div className="info-grid">
            <div className="info-block">
              <div className="info-label">{t(lang, "tripDistance")}</div>
              <div className="info-value">{distanceKm != null ? `${distanceKm} km` : "—"}</div>
            </div>
            <div className="info-block">
              <div className="info-label">{t(lang, "recommendedPrice")}</div>
              <div className="info-value">{recommendedPrice != null ? formatMoney(recommendedPrice, currency) : tariffHint || "—"}</div>
            </div>
          </div>

          <div className="grid-2">
            <div>
              <label className="field-label">{t(lang, "seats")}</label>
              <input className="field" type="number" min="1" value={seats} onChange={(e) => setSeats(e.target.value)} />
            </div>
            <div>
              <label className="field-label">{t(lang, "yourPrice")}</label>
              <input className="field" type="number" min="0" value={price} onChange={(e) => setPrice(e.target.value)} />
            </div>
          </div>

          <button type="button" className="button-secondary full" onClick={() => recommendedPrice != null ? setPrice(String(recommendedPrice)) : null}>
            {t(lang, "useRecommendedPrice")}
          </button>

          <div>
            <label className="field-label">{t(lang, "comment")}</label>
            <textarea className="field" value={comment} onChange={(e) => setComment(e.target.value)} placeholder={t(lang, "writeComment")} />
          </div>

          <button type="submit" className="button-main full" style={{ padding: "16px 14px", fontSize: "18px" }}>
            {role === "driver" ? t(lang, "createOffer") : t(lang, "createOrder")}
          </button>
        </form>

        {role === "passenger" && createdOrderId ? (
          <div className="card stack">
            <div className="card-title">{t(lang, "searchStarted")}</div>
            <div className="info-grid">
              <div className="info-block"><div className="info-label">{t(lang, "driversSeen")}</div><div className="info-value">{driversSeen}</div></div>
              <div className="info-block"><div className="info-label">{t(lang, "recommendedPrice")}</div><div className="info-value">{price ? `${price} ${currency}` : formatMoney(recommendedPrice, currency)}</div></div>
            </div>
            {secondsPassed >= 30 ? <div className="stack"><div className="notice">{t(lang, "raisePriceHint")}</div><button className="button-main full" onClick={raisePrice}>{t(lang, "raisePrice")}</button></div> : null}
          </div>
        ) : null}
      </div>
      <BottomNav />
    </main>
  );
}
