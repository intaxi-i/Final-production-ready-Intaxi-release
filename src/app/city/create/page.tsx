"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import AddressField from "@/components/AddressField";
import BottomNav from "@/components/BottomNav";
import LocationFields from "@/components/LocationFields";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { api, TariffItem } from "@/lib/api";
import { haversineKm } from "@/lib/geo";
import { formatCountryLocation, guessRegionFromCity } from "@/lib/locations";
import { t } from "@/lib/i18n";

const FALLBACK_TARIFFS: Record<string, TariffItem> = {
  uz: { country: "uz", currency: "UZS", price_per_km: 2500 },
  tr: { country: "tr", currency: "TRY", price_per_km: 45 },
  kz: { country: "kz", currency: "KZT", price_per_km: 120 },
  sa: { country: "sa", currency: "SAR", price_per_km: 2.5 },
};

function swapLabel(lang: string) {
  if (lang === "ru") return "Поменять точки";
  if (lang === "uz") return "Nuqtalarni almashtirish";
  if (lang === "ar") return "تبديل النقطتين";
  if (lang === "kz") return "Нүктелерді ауыстыру";
  return "Swap points";
}

function extraLabel(lang: string, open: boolean) {
  if (lang === "ru") return open ? "Скрыть дополнительные настройки" : "Дополнительные настройки";
  if (lang === "uz") return open ? "Qo‘shimcha sozlamalarni yashirish" : "Qo‘shimcha sozlamalar";
  if (lang === "ar") return open ? "إخفاء الإعدادات الإضافية" : "إعدادات إضافية";
  if (lang === "kz") return open ? "Қосымша баптауды жасыру" : "Қосымша баптаулар";
  return open ? "Hide extra settings" : "Extra settings";
}

function manualAreaLabel(lang: string, open: boolean) {
  if (lang === "ru") return open ? "Скрыть город и район" : "Указать город вручную";
  if (lang === "uz") return open ? "Shahar va hududni yashirish" : "Shaharni qo‘lda ko‘rsatish";
  if (lang === "ar") return open ? "إخفاء المدينة والمنطقة" : "تحديد المدينة يدويًا";
  if (lang === "kz") return open ? "Қала мен аймақты жасыру" : "Қаланы қолмен көрсету";
  return open ? "Hide city and area" : "Set city manually";
}

function searchingTitle(lang: string) {
  if (lang === "ru") return "Ищем водителя";
  if (lang === "uz") return "Haydovchini qidirmoqdamiz";
  if (lang === "ar") return "جاري البحث عن سائق";
  if (lang === "kz") return "Жүргізуші ізделіп жатыр";
  return "Searching for driver";
}

function searchingSubtitle(lang: string) {
  if (lang === "ru") return "Заказ создан. Сейчас система показывает ваш заказ ближайшим водителям.";
  if (lang === "uz") return "Buyurtma yaratildi. Tizim hozir uni yaqin haydovchilarga ko‘rsatmoqda.";
  if (lang === "ar") return "تم إنشاء الطلب. يعرض النظام طلبك الآن على السائقين القريبين.";
  if (lang === "kz") return "Тапсырыс құрылды. Жүйе қазір оны жақын жүргізушілерге көрсетіп жатыр.";
  return "Order created. The system is now showing it to nearby drivers.";
}

function destinationHint(lang: string) {
  if (lang === "ru") return "Укажите конечный адрес текстом. Текущая геолокация для точки B не используется.";
  if (lang === "uz") return "Yakuniy manzilni matn bilan kiriting. B nuqta uchun joriy geolokatsiya ishlatilmaydi.";
  if (lang === "ar") return "أدخل عنوان الوصول نصيًا. لا يتم استخدام الموقع الحالي للنقطة B.";
  if (lang === "kz") return "Соңғы мекенжайды мәтінмен енгізіңіз. B нүктесі үшін ағымдағы геолокация қолданылмайды.";
  return "Enter destination as text. Current geolocation is not used for point B.";
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
  const [regionKey, setRegionKey] = useState(guessRegionFromCity(user?.country || "uz", user?.city || ""));
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
  const [tariffs, setTariffs] = useState<Record<string, TariffItem>>(FALLBACK_TARIFFS);
  const [showExtras, setShowExtras] = useState(false);
  const [showManualArea, setShowManualArea] = useState(false);

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
        const next: Record<string, TariffItem> = { ...FALLBACK_TARIFFS };
        data.items.forEach((item) => {
          next[item.country] = item;
        });
        setTariffs(next);
      } catch {
        if (!cancelled) setTariffs(FALLBACK_TARIFFS);
      }
    }
    void loadTariffs();
    return () => {
      cancelled = true;
    };
  }, [sessionToken]);

  useEffect(() => {
    const tariff = tariffs[country] || FALLBACK_TARIFFS[country] || FALLBACK_TARIFFS.uz;
    setCurrency(tariff.currency);
    setTariffHint(`~${tariff.price_per_km} ${tariff.currency}/km`);
  }, [country, tariffs]);

  useEffect(() => {
    const tariff = tariffs[country] || FALLBACK_TARIFFS[country] || FALLBACK_TARIFFS.uz;
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
    if ((country === "uz" || country === "kz") && regionKey && city) return formatCountryLocation(country, regionKey, city, lang);
    return city;
  }, [country, regionKey, city, lang]);

  const searchDots = ".".repeat((secondsPassed % 3) + 1);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!sessionToken) return;
    if (!cityValue && !fromAddress.trim()) {
      setMessage(lang === "ru" ? "Укажите точку A или разрешите локацию" : t(lang, "operationFailed"));
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
        city: cityValue || city || user?.city || "",
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
      setMessage("");
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
              if (countryCode === "uz" || countryCode === "tr" || countryCode === "sa" || countryCode === "kz") setCountry(countryCode);
              if (resolvedCity) {
                if ((countryCode || country) === "uz" || (countryCode || country) === "kz") {
                  const guessed = guessRegionFromCity(countryCode || country, resolvedCity);
                  if (guessed) setRegionKey(guessed);
                }
                setCity(resolvedCity);
                setShowManualArea(false);
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
            allowCurrentLocation={false}
            manualHint={destinationHint(lang)}
          />

          <button type="button" className="button-secondary full" onClick={swapPoints}>{swapLabel(lang)}</button>

          <button type="button" className="button-secondary full" onClick={() => setShowManualArea((prev) => !prev)}>
            {manualAreaLabel(lang, showManualArea)}
          </button>

          {showManualArea ? (
            <LocationFields lang={lang} country={country} setCountry={setCountry} regionKey={regionKey} setRegionKey={setRegionKey} city={city} setCity={setCity} collapsible />
          ) : cityValue ? (
            <div className="info-block">
              <div className="info-label">{t(lang, "cityField")}</div>
              <div className="info-value">{cityValue}</div>
            </div>
          ) : null}

          <button type="button" className="button-secondary full" onClick={() => setShowExtras((prev) => !prev)}>
            {extraLabel(lang, showExtras)}
          </button>

          {showExtras ? (
            <>
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
            </>
          ) : null}

          <button type="submit" className="button-main full" style={{ padding: "16px 14px", fontSize: "18px" }}>
            {role === "driver" ? t(lang, "createOffer") : t(lang, "createOrder")}
          </button>
        </form>

        {role === "passenger" && createdOrderId ? (
          <div className="card stack">
            <div className="card-title">{searchingTitle(lang)}{searchDots}</div>
            <div className="muted">{searchingSubtitle(lang)}</div>
            <div className="info-grid">
              <div className="info-block"><div className="info-label">{t(lang, "driversSeen")}</div><div className="info-value">{driversSeen}</div></div>
              <div className="info-block"><div className="info-label">{t(lang, "recommendedPrice")}</div><div className="info-value">{price ? `${price} ${currency}` : formatMoney(recommendedPrice, currency)}</div></div>
            </div>
            <div className="muted">{secondsPassed < 30 ? `${secondsPassed}s` : t(lang, "raisePriceHint")}</div>
            {secondsPassed >= 30 ? <button className="button-main full" onClick={raisePrice}>{t(lang, "raisePrice")}</button> : null}
          </div>
        ) : null}
      </div>
      <BottomNav />
    </main>
  );
}
