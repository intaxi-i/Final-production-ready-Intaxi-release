"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import AddressField from "@/components/AddressField";
import BottomNav from "@/components/BottomNav";
import LocationFields from "@/components/LocationFields";
import MapPointPicker from "@/components/MapPointPicker";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { api, TariffItem } from "@/lib/api";
import { haversineKm } from "@/lib/geo";
import { formatCountryLocation, guessRegionFromCity } from "@/lib/locations";
import { APP_ROUTES } from "@/lib/constants";
import { t } from "@/lib/i18n";

const FALLBACK_TARIFFS: Record<string, TariffItem> = {
  uz: { country: "uz", currency: "UZS", price_per_km: 2500 },
  tr: { country: "tr", currency: "TRY", price_per_km: 45 },
  kz: { country: "kz", currency: "KZT", price_per_km: 120 },
  sa: { country: "sa", currency: "SAR", price_per_km: 2.5 },
};

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
  if (lang === "ru") return "Заказ создан. Система показывает его ближайшим активным водителям и постепенно расширяет круг поиска.";
  if (lang === "uz") return "Buyurtma yaratildi. Tizim uni yaqin faol haydovchilarga ko‘rsatib, qidiruv doirasini kengaytiradi.";
  if (lang === "ar") return "تم إنشاء الطلب. يعرضه النظام على أقرب السائقين النشطين ثم يوسّع دائرة البحث.";
  if (lang === "kz") return "Тапсырыс құрылды. Жүйе оны жақын белсенді жүргізушілерге көрсетіп, іздеу аясын кеңейтеді.";
  return "Order created. The system is showing it to nearby active drivers and expanding the search radius.";
}

function destinationHint(lang: string) {
  if (lang === "ru") return "Укажите конечный адрес текстом или выберите точку на карте. Текущая геолокация для точки B не используется.";
  if (lang === "uz") return "Yakuniy manzilni yozing yoki xaritada nuqta tanlang. B nuqta uchun joriy geolokatsiya ishlatilmaydi.";
  if (lang === "ar") return "أدخل عنوان الوصول أو اختر النقطة على الخريطة. لا يتم استخدام الموقع الحالي للنقطة B.";
  if (lang === "kz") return "Соңғы мекенжайды жазыңыз немесе картадан нүкте таңдаңыз. B нүктесі үшін ағымдағы геолокация қолданылмайды.";
  return "Enter destination or choose a point on the map. Current geolocation is not used for point B.";
}

function mapPickerText(lang: string) {
  if (lang === "ru") return "Указать точку B на карте";
  if (lang === "uz") return "B nuqtani xaritada tanlash";
  if (lang === "ar") return "تحديد النقطة B على الخريطة";
  if (lang === "kz") return "B нүктесін картадан таңдау";
  return "Pick point B on map";
}

function mapPickerTitle(lang: string) {
  if (lang === "ru") return "Конечная точка на карте";
  if (lang === "uz") return "Xaritadagi manzil nuqtasi";
  if (lang === "ar") return "نقطة الوصول على الخريطة";
  if (lang === "kz") return "Картадағы соңғы нүкте";
  return "Destination point on map";
}

function confirmPointText(lang: string) {
  if (lang === "ru") return "Принять точку";
  if (lang === "uz") return "Nuqtani qabul qilish";
  if (lang === "ar") return "تأكيد النقطة";
  if (lang === "kz") return "Нүктені қабылдау";
  return "Confirm point";
}

function cancelPointText(lang: string) {
  if (lang === "ru") return "Закрыть карту";
  if (lang === "uz") return "Xaritani yopish";
  if (lang === "ar") return "إغلاق الخريطة";
  if (lang === "kz") return "Картаны жабу";
  return "Close map";
}

function driverGuideTitle(lang: string) {
  if (lang === "ru") return "Городской заказ создаёт только пассажир";
  if (lang === "uz") return "Shahar buyurtmasini faqat yo‘lovchi yaratadi";
  if (lang === "ar") return "طلب المدينة ينشئه الراكب فقط";
  if (lang === "kz") return "Қалалық тапсырысты тек жолаушы жасайды";
  return "Only a passenger creates a city order";
}

function driverGuideText(lang: string) {
  if (lang === "ru") return "Если водитель хочет заказать такси для себя, нужно открыть профиль и переключить роль на пассажира.";
  if (lang === "uz") return "Haydovchi o‘zi uchun taksi chaqirmoqchi bo‘lsa, profilga kirib rolni yo‘lovchiga almashtirishi kerak.";
  if (lang === "ar") return "إذا أراد السائق طلب سيارة لنفسه، فعليه فتح الملف الشخصي وتبديل الدور إلى راكب.";
  if (lang === "kz") return "Егер жүргізуші өзі үшін такси шақырғысы келсе, профильге кіріп рөлін жолаушыға ауыстыруы керек.";
  return "If a driver wants to order a taxi, they need to switch the role to passenger in the profile.";
}

function openProfileText(lang: string) {
  if (lang === "ru") return "Открыть профиль";
  if (lang === "uz") return "Profilni ochish";
  if (lang === "ar") return "فتح الملف الشخصي";
  if (lang === "kz") return "Профильді ашу";
  return "Open profile";
}

function formatMoney(value: number | null, currency: string) {
  if (value == null || Number.isNaN(value)) return "—";
  return `${Number(value.toFixed(2))} ${currency}`;
}

export default function CityCreatePage() {
  const { lang, sessionToken, user } = useApp();
  const role = (user?.active_role as "passenger" | "driver") || "passenger";
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
  const [searchStatus, setSearchStatus] = useState("");
  const [tariffs, setTariffs] = useState<Record<string, TariffItem>>(FALLBACK_TARIFFS);
  const [showExtras, setShowExtras] = useState(false);
  const [showManualArea, setShowManualArea] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const from = params.get("from");
    const to = params.get("to");
    const nextCountry = params.get("country");
    const nextCity = params.get("city");
    const nextSeats = params.get("seats");
    const nextPrice = params.get("price");
    const nextComment = params.get("comment");
    if (from) setFromAddress(from);
    if (to) setToAddress(to);
    if (nextCountry && ["uz", "tr", "kz", "sa"].includes(nextCountry)) setCountry(nextCountry);
    if (nextCity) {
      setCity(nextCity);
      const guessedRegion = guessRegionFromCity(nextCountry || user?.country || "uz", nextCity);
      if (guessedRegion) setRegionKey(guessedRegion);
    }
    if (nextSeats) setSeats(nextSeats);
    if (nextPrice) setPrice(nextPrice);
    if (nextComment) {
      setComment(nextComment);
      setShowExtras(true);
    }
  }, [user?.country]);

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

  useEffect(() => {
    if (!createdOrderId || !sessionToken) return;
    let cancelled = false;

    async function pollOrder() {
      try {
        const data = await api.myCityOrders(sessionToken);
        if (cancelled) return;
        const current = (data.items || []).find((item) => item.id === createdOrderId);
        if (!current) return;
        setDriversSeen(current.seen_by_drivers ?? 0);
        setSearchStatus(current.status || "");
        if (current.price) setPrice(String(current.price));
        if (current.active_trip_id) {
          window.location.href = `${APP_ROUTES.currentTrip}?tripType=city_trip&tripId=${current.active_trip_id}`;
        }
      } catch {}
    }

    void pollOrder();
    const timer = window.setInterval(() => void pollOrder(), 6000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [createdOrderId, sessionToken]);

  const cityValue = useMemo(() => {
    if ((country === "uz" || country === "kz") && regionKey && city) return formatCountryLocation(country, regionKey, city, lang);
    return city;
  }, [country, regionKey, city, lang]);

  const searchDots = ".".repeat((secondsPassed % 3) + 1);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!sessionToken || role !== "passenger") return;
    if (!cityValue && !fromAddress.trim()) {
      setMessage(lang === "ru" ? "Укажите точку A или разрешите локацию" : t(lang, "operationFailed"));
      return;
    }
    if (!toAddress.trim()) {
      setMessage(lang === "ru" ? "Укажите пункт назначения" : t(lang, "operationFailed"));
      return;
    }
    try {
      const result = await api.createCityOrder(sessionToken, {
        role: "passenger",
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
      setSearchStatus(result.status || "active");
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

  if (role === "driver") {
    return (
      <main className="page">
        <div className="container stack">
          <PageHeader title={driverGuideTitle(lang)} subtitle={driverGuideText(lang)} />
          <div className="card stack">
            <div className="card-title">{driverGuideTitle(lang)}</div>
            <div className="muted">{driverGuideText(lang)}</div>
            <a href={APP_ROUTES.profile} className="button-main full">{openProfileText(lang)}</a>
          </div>
        </div>
        <BottomNav />
      </main>
    );
  }

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title={t(lang, "createOrder")} subtitle={t(lang, "passengerMode")} />
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

          <MapPointPicker
            lang={lang}
            triggerLabel={mapPickerText(lang)}
            title={mapPickerTitle(lang)}
            confirmLabel={confirmPointText(lang)}
            cancelLabel={cancelPointText(lang)}
            initialLat={toLat ? Number(toLat) : null}
            initialLng={toLng ? Number(toLng) : null}
            onConfirm={({ address, lat, lng, city: resolvedCity, region, countryCode }) => {
              setToAddress(address);
              setToLat(lat);
              setToLng(lng);
              if (countryCode === "uz" || countryCode === "tr" || countryCode === "sa" || countryCode === "kz") setCountry(countryCode);
              if (resolvedCity) {
                if ((countryCode || country) === "uz" || (countryCode || country) === "kz") {
                  const guessed = guessRegionFromCity(countryCode || country, resolvedCity || region || "");
                  if (guessed) setRegionKey(guessed);
                }
                setCity(resolvedCity);
              }
            }}
          />

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
            {t(lang, "createOrder")}
          </button>
        </form>

        {createdOrderId ? (
          <div className="card stack">
            <div className="card-title">{searchingTitle(lang)}{searchDots}</div>
            <div className="muted">{searchingSubtitle(lang)}</div>
            <div className="info-grid">
              <div className="info-block"><div className="info-label">{t(lang, "driversSeen")}</div><div className="info-value">{driversSeen}</div></div>
              <div className="info-block"><div className="info-label">{t(lang, "status")}</div><div className="info-value">{searchStatus || "active"}</div></div>
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
