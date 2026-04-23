"use client";

import { FormEvent, useMemo, useState } from "react";
import BottomNav from "@/components/BottomNav";
import LocationFields from "@/components/LocationFields";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { api } from "@/lib/api";
import { COUNTRY_OPTIONS } from "@/lib/constants";
import { formatUzLocation } from "@/lib/locations";
import { t } from "@/lib/i18n";

function pickupModeLabel(lang: string, mode: string) {
  const labels: Record<string, Record<string, string>> = {
    driver_location: {
      ru: "Локация водителя = место сбора",
      uz: "Haydovchi joyi = yig‘ilish nuqtasi",
      ar: "موقع السائق هو نقطة التجمع",
      kz: "Жүргізуші орны = жиналу нүктесі",
      en: "Driver location is the pickup point",
    },
    driver_pickup: {
      ru: "Водитель сам заберёт пассажира",
      uz: "Haydovchi yo‘lovchini o‘zi olib ketadi",
      ar: "السائق سيصطحب الراكب بنفسه",
      kz: "Жүргізуші жолаушыны өзі алып кетеді",
      en: "Driver will pick the passenger up",
    },
    ask_driver: {
      ru: "Уточнить у водителя",
      uz: "Haydovchi bilan aniqlash",
      ar: "التأكيد مع السائق",
      kz: "Жүргізушімен нақтылау",
      en: "Ask the driver later",
    },
  };
  return labels[mode]?.[lang] || labels[mode]?.en || mode;
}

export default function IntercityRoutePage() {
  const { lang, sessionToken } = useApp();
  const [country, setCountry] = useState("uz");
  const [fromRegion, setFromRegion] = useState("");
  const [toRegion, setToRegion] = useState("");
  const [fromCity, setFromCity] = useState("");
  const [toCity, setToCity] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [seats, setSeats] = useState("1");
  const [price, setPrice] = useState("");
  const [comment, setComment] = useState("");
  const [pickupMode, setPickupMode] = useState<"driver_location" | "driver_pickup" | "ask_driver">("ask_driver");
  const [message, setMessage] = useState("");

  const fromLabel = useMemo(() => country === "uz" && fromRegion && fromCity ? formatUzLocation(fromRegion, fromCity, lang) : fromCity, [country, fromRegion, fromCity, lang]);
  const toLabel = useMemo(() => country === "uz" && toRegion && toCity ? formatUzLocation(toRegion, toCity, lang) : toCity, [country, toRegion, toCity, lang]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!sessionToken) return;
    try {
      await api.createIntercityRoute(sessionToken, {
        country,
        from_city: fromLabel,
        to_city: toLabel,
        date,
        time,
        seats: Number(seats || 1),
        price: Number(price || 0),
        comment,
        pickup_mode: pickupMode,
      });
      setMessage(t(lang, "postedSuccessfully"));
    } catch {
      setMessage(t(lang, "operationFailed"));
    }
  }

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title={t(lang, "createRoute")} subtitle={t(lang, "driverMode")} />
        {message ? <div className="notice">{message}</div> : null}
        <form className="card stack" onSubmit={handleSubmit}>
          <div>
            <label className="field-label">{t(lang, "country")}</label>
            <select className="field" value={country} onChange={(e) => { setCountry(e.target.value); setFromRegion(""); setToRegion(""); setFromCity(""); setToCity(""); }}>
              {COUNTRY_OPTIONS.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}
            </select>
          </div>
          <div className="grid-2">
            <div className="stack">
              <div className="card-title">{t(lang, "from")}</div>
              <LocationFields lang={lang} country={country} regionKey={fromRegion} setRegionKey={setFromRegion} city={fromCity} setCity={setFromCity} showCountry={false} />
            </div>
            <div className="stack">
              <div className="card-title">{t(lang, "to")}</div>
              <LocationFields lang={lang} country={country} regionKey={toRegion} setRegionKey={setToRegion} city={toCity} setCity={setToCity} showCountry={false} />
            </div>
          </div>
          <div>
            <label className="field-label">Pickup mode</label>
            <select className="field" value={pickupMode} onChange={(e) => setPickupMode(e.target.value as any)}>
              <option value="driver_location">{pickupModeLabel(lang, "driver_location")}</option>
              <option value="driver_pickup">{pickupModeLabel(lang, "driver_pickup")}</option>
              <option value="ask_driver">{pickupModeLabel(lang, "ask_driver")}</option>
            </select>
          </div>
          <div className="grid-2">
            <div>
              <label className="field-label">{t(lang, "date")}</label>
              <input className="field" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </div>
            <div>
              <label className="field-label">{t(lang, "time")}</label>
              <input className="field" type="time" value={time} onChange={(e) => setTime(e.target.value)} />
            </div>
          </div>
          <div className="grid-2">
            <div>
              <label className="field-label">{t(lang, "seats")}</label>
              <input className="field" type="number" min="1" value={seats} onChange={(e) => setSeats(e.target.value)} />
            </div>
            <div>
              <label className="field-label">{t(lang, "price")}</label>
              <input className="field" type="number" min="0" value={price} onChange={(e) => setPrice(e.target.value)} />
            </div>
          </div>
          <div>
            <label className="field-label">{t(lang, "comment")}</label>
            <textarea className="field" value={comment} onChange={(e) => setComment(e.target.value)} />
          </div>
          <button type="submit" className="button-main full">{t(lang, "createRoute")}</button>
        </form>
      </div>
      <BottomNav />
    </main>
  );
}
