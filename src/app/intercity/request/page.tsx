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

export default function IntercityRequestPage() {
  const { lang, sessionToken } = useApp();
  const [country, setCountry] = useState("uz");
  const [fromRegion, setFromRegion] = useState("");
  const [toRegion, setToRegion] = useState("");
  const [fromCity, setFromCity] = useState("");
  const [toCity, setToCity] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [seatsNeeded, setSeatsNeeded] = useState("1");
  const [priceOffer, setPriceOffer] = useState("");
  const [comment, setComment] = useState("");
  const [message, setMessage] = useState("");

  const fromLabel = useMemo(() => country === "uz" && fromRegion && fromCity ? formatUzLocation(fromRegion, fromCity, lang) : fromCity, [country, fromRegion, fromCity, lang]);
  const toLabel = useMemo(() => country === "uz" && toRegion && toCity ? formatUzLocation(toRegion, toCity, lang) : toCity, [country, toRegion, toCity, lang]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!sessionToken) return;
    try {
      await api.createIntercityRequest(sessionToken, {
        country,
        from_city: fromLabel,
        to_city: toLabel,
        date,
        time,
        seats_needed: Number(seatsNeeded || 1),
        price_offer: Number(priceOffer || 0),
        comment,
      });
      setMessage(t(lang, "postedSuccessfully"));
    } catch {
      setMessage(t(lang, "operationFailed"));
    }
  }

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title={t(lang, "createRequest")} subtitle={t(lang, "passengerMode")} />
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
              <label className="field-label">{t(lang, "people")}</label>
              <input className="field" type="number" min="1" value={seatsNeeded} onChange={(e) => setSeatsNeeded(e.target.value)} />
            </div>
            <div>
              <label className="field-label">{t(lang, "yourPrice")}</label>
              <input className="field" type="number" min="0" value={priceOffer} onChange={(e) => setPriceOffer(e.target.value)} />
            </div>
          </div>
          <div>
            <label className="field-label">{t(lang, "comment")}</label>
            <textarea className="field" value={comment} onChange={(e) => setComment(e.target.value)} />
          </div>
          <button type="submit" className="button-main full">{t(lang, "createRequest")}</button>
        </form>
      </div>
      <BottomNav />
    </main>
  );
}