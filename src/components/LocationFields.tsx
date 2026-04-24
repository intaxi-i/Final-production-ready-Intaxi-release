"use client";

import { useMemo, useState } from "react";
import { COUNTRY_OPTIONS_EXTENDED } from "@/lib/country-config";
import { resolveCurrentLocation } from "@/lib/geo";
import { getLocalityOptionsForCountry, getRegionOptionsForCountry, guessRegionFromCity } from "@/lib/locations";
import { t } from "@/lib/i18n";

type Props = {
  lang: string;
  country: string;
  setCountry?: (value: string) => void;
  regionKey: string;
  setRegionKey: (value: string) => void;
  city: string;
  setCity: (value: string) => void;
  showCountry?: boolean;
};

function labels(lang: string) {
  if (lang === "uz") return { current: "Joylashuvni bir bosishda olish", address: "Aniqlangan manzil", coords: "Koordinatalar", copy: "Nusxa", loading: "Aniqlanmoqda..." };
  if (lang === "ar") return { current: "استخدام موقعي الحالي", address: "العنوان المحدد", coords: "الإحداثيات", copy: "نسخ", loading: "جارٍ التحديد..." };
  if (lang === "kz") return { current: "Орнымды бір басуда алу", address: "Анықталған мекенжай", coords: "Координаттар", copy: "Көшіру", loading: "Анықталуда..." };
  if (lang === "en") return { current: "Use current location", address: "Detected address", coords: "Coordinates", copy: "Copy", loading: "Resolving..." };
  return { current: "Определить по текущей локации", address: "Определённый адрес", coords: "Координаты", copy: "Копировать", loading: "Определяем..." };
}

export default function LocationFields({
  lang,
  country,
  setCountry,
  regionKey,
  setRegionKey,
  city,
  setCity,
  showCountry = true,
}: Props) {
  const ui = useMemo(() => labels(lang), [lang]);
  const regionOptions = getRegionOptionsForCountry(country, lang);
  const cityOptions = getLocalityOptionsForCountry(country, regionKey);
  const [busy, setBusy] = useState(false);
  const [detectedAddress, setDetectedAddress] = useState("");
  const [detectedCoords, setDetectedCoords] = useState("");

  async function useCurrentLocation() {
    try {
      setBusy(true);
      const data = await resolveCurrentLocation();
      setDetectedAddress(data.address);
      setDetectedCoords(`${data.lat}, ${data.lng}`);
      const nextCountry = data.countryCode === "uz" ? "uz" : data.countryCode === "tr" ? "tr" : data.countryCode === "sa" ? "sa" : data.countryCode === "kz" ? "kz" : country;
      setCountry?.(nextCountry);
      const guessedCity = data.city || city;
      if (nextCountry === "uz" || nextCountry === "kz") {
        const guessedRegion = guessRegionFromCity(nextCountry, guessedCity || data.region || "");
        if (guessedRegion) setRegionKey(guessedRegion);
      } else {
        setRegionKey("");
      }
      if (guessedCity) setCity(guessedCity);
    } catch {
      setDetectedAddress("");
      setDetectedCoords("");
    } finally {
      setBusy(false);
    }
  }

  async function copy(value: string) {
    if (!value || typeof navigator === "undefined" || !navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(value);
    } catch {}
  }

  return (
    <>
      <button type="button" className="button-secondary full" onClick={useCurrentLocation} disabled={busy}>
        {busy ? ui.loading : ui.current}
      </button>

      {showCountry ? (
        <div>
          <label className="field-label">{t(lang as any, "country")}</label>
          <select
            className="field"
            value={country}
            onChange={(e) => {
              setCountry?.(e.target.value);
              setRegionKey("");
              setCity("");
            }}
          >
            {COUNTRY_OPTIONS_EXTENDED.map((item) => (
              <option key={item.code} value={item.code}>
                {item.label}
              </option>
            ))}
          </select>
        </div>
      ) : null}

      {country === "uz" || country === "kz" ? (
        <div>
          <label className="field-label">{t(lang as any, "region")}</label>
          <select
            className="field"
            value={regionKey}
            onChange={(e) => {
              setRegionKey(e.target.value);
              setCity("");
            }}
          >
            <option value="">{t(lang as any, "chooseRegion")}</option>
            {regionOptions.map((item) => (
              <option key={item.key} value={item.key}>
                {item.label}
              </option>
            ))}
          </select>
        </div>
      ) : null}

      <div>
        <label className="field-label">{t(lang as any, "cityField")}</label>
        <select className="field" value={city} onChange={(e) => setCity(e.target.value)}>
          <option value="">{t(lang as any, "chooseCity")}</option>
          {cityOptions.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </div>

      {detectedAddress ? (
        <div className="info-grid">
          <div className="info-block">
            <div className="info-label">{ui.address}</div>
            <div className="info-value">{detectedAddress}</div>
            <button type="button" className="button-secondary full" style={{ marginTop: 8 }} onClick={() => copy(detectedAddress)}>{ui.copy}</button>
          </div>
          <div className="info-block">
            <div className="info-label">{ui.coords}</div>
            <div className="info-value">{detectedCoords || "—"}</div>
            {detectedCoords ? <button type="button" className="button-secondary full" style={{ marginTop: 8 }} onClick={() => copy(detectedCoords)}>{ui.copy}</button> : null}
          </div>
        </div>
      ) : null}
    </>
  );
}
