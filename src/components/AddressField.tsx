"use client";

import { useMemo, useState } from "react";
import { resolveCurrentLocation } from "@/lib/geo";

type Props = {
  lang: string;
  label: string;
  address: string;
  setAddress: (value: string) => void;
  lat: string;
  setLat: (value: string) => void;
  lng: string;
  setLng: (value: string) => void;
  onResolved?: (payload: { address: string; lat: string; lng: string; countryCode?: string; city?: string; region?: string }) => void;
  allowCurrentLocation?: boolean;
  manualHint?: string;
};

function texts(lang: string) {
  if (lang === "uz") return { current: "Joylashuvim bo‘yicha", manual: "Aniq nuqtani qo‘lda kiritish", hideManual: "Aniq nuqtani yashirish", address: "Manzil", coords: "Koordinatalar", loading: "Aniqlanmoqda...", detected: "Joylashuv topildi" };
  if (lang === "ar") return { current: "حسب موقعي الحالي", manual: "إدخال نقطة دقيقة يدويًا", hideManual: "إخفاء النقطة الدقيقة", address: "العنوان", coords: "الإحداثيات", loading: "جارٍ التحديد...", detected: "تم تحديد الموقع" };
  if (lang === "kz") return { current: "Менің орным бойынша", manual: "Нақты нүктені қолмен енгізу", hideManual: "Нақты нүктені жасыру", address: "Мекенжай", coords: "Координаттар", loading: "Анықталуда...", detected: "Орналасу табылды" };
  if (lang === "en") return { current: "Use my location", manual: "Enter precise point manually", hideManual: "Hide precise point", address: "Address", coords: "Coordinates", loading: "Resolving...", detected: "Location detected" };
  return { current: "По моей локации", manual: "Указать точку вручную", hideManual: "Скрыть точную точку", address: "Адрес", coords: "Координаты", loading: "Определяем...", detected: "Локация определена" };
}

export default function AddressField({
  lang,
  label,
  address,
  setAddress,
  lat,
  setLat,
  lng,
  setLng,
  onResolved,
  allowCurrentLocation = true,
  manualHint,
}: Props) {
  const ui = useMemo(() => texts(lang), [lang]);
  const [busy, setBusy] = useState(false);
  const [hint, setHint] = useState("");
  const [manualOpen, setManualOpen] = useState(false);

  async function useCurrentLocation() {
    try {
      setBusy(true);
      setHint("");
      const data = await resolveCurrentLocation();
      const latValue = String(data.lat);
      const lngValue = String(data.lng);
      setAddress(data.address);
      setLat(latValue);
      setLng(lngValue);
      setHint(ui.detected);
      onResolved?.({ address: data.address, lat: latValue, lng: lngValue, countryCode: data.countryCode, city: data.city, region: data.region });
    } catch (error) {
      setHint(error instanceof Error ? error.message : "Location error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <div>
        <label className="field-label">{label}</label>
        <input
          className="field"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder={manualHint || label}
        />
      </div>

      {allowCurrentLocation ? (
        <button type="button" className="button-secondary full" onClick={useCurrentLocation} disabled={busy}>
          {busy ? ui.loading : ui.current}
        </button>
      ) : null}

      <button type="button" className="button-secondary full" onClick={() => setManualOpen((prev) => !prev)}>
        {manualOpen ? ui.hideManual : ui.manual}
      </button>

      {manualOpen ? (
        <div className="grid-2">
          <div>
            <label className="field-label">Lat</label>
            <input className="field" value={lat} onChange={(e) => setLat(e.target.value)} placeholder="41.2995" />
          </div>
          <div>
            <label className="field-label">Lng</label>
            <input className="field" value={lng} onChange={(e) => setLng(e.target.value)} placeholder="69.2401" />
          </div>
        </div>
      ) : null}

      {hint ? <div className="muted">{hint}</div> : null}
      {!allowCurrentLocation && manualHint ? <div className="muted">{manualHint}</div> : null}
    </div>
  );
}
