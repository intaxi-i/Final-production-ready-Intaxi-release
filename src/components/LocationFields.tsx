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
  collapsible?: boolean;
};

function labels(lang: string) {
  if (lang === "uz") return { current: "Joylashuvni bir bosishda olish", manual: "Joylashuvni qo‘lda ko‘rsatish", hideManual: "Qo‘lda ko‘rsatishni yashirish", detected: "Aniqlangan joy", loading: "Aniqlanmoqda..." };
  if (lang === "ar") return { current: "استخدام موقعي الحالي", manual: "تحديد الموقع يدويًا", hideManual: "إخفاء التحديد اليدوي", detected: "الموقع المحدد", loading: "جارٍ التحديد..." };
  if (lang === "kz") return { current: "Орнымды бір басуда алу", manual: "Орналасуды қолмен көрсету", hideManual: "Қолмен таңдауды жасыру", detected: "Анықталған орын", loading: "Анықталуда..." };
  if (lang === "en") return { current: "Use current location", manual: "Set location manually", hideManual: "Hide manual location", detected: "Detected place", loading: "Resolving..." };
  return { current: "Определить по текущей локации", manual: "Указать локацию вручную", hideManual: "Скрыть ручной выбор", detected: "Определённое место", loading: "Определяем..." };
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
  collapsible = false,
}: Props) {
  const ui = useMemo(() => labels(lang), [lang]);
  const regionOptions = getRegionOptionsForCountry(country, lang);
  const cityOptions = getLocalityOptionsForCountry(country, regionKey);
  const [busy, setBusy] = useState(false);
  const [manualOpen, setManualOpen] = useState(!collapsible);
  const [detectedAddress, setDetectedAddress] = useState("");

  async function useCurrentLocation() {
    try {
      setBusy(true);
      const data = await resolveCurrentLocation();
      setDetectedAddress(data.address);
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
      if (collapsible) setManualOpen(false);
    } catch {
      setDetectedAddress("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <button type="button" className="button-secondary full" onClick={useCurrentLocation} disabled={busy}>
        {busy ? ui.loading : ui.current}
      </button>

      {detectedAddress || city ? (
        <div className="info-block">
          <div className="info-label">{ui.detected}</div>
          <div className="info-value">{city || detectedAddress || "—"}</div>
        </div>
      ) : null}

      {collapsible ? (
        <button type="button" className="button-secondary full" onClick={() => setManualOpen((prev) => !prev)}>
          {manualOpen ? ui.hideManual : ui.manual}
        </button>
      ) : null}

      {manualOpen ? (
        <>
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
        </>
      ) : null}
    </div>
  );
}
