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
};

function texts(lang: string) {
  if (lang === "uz") return { current: "Joylashuvni bir bosishda olish", address: "Aniq manzil", coords: "Koordinatalar", copy: "Nusxa", loading: "Aniqlanmoqda..." };
  if (lang === "ar") return { current: "استخدام موقعي الحالي", address: "العنوان الدقيق", coords: "الإحداثيات", copy: "نسخ", loading: "جارٍ التحديد..." };
  if (lang === "kz") return { current: "Орнымды бір басуда алу", address: "Нақты мекенжай", coords: "Координаттар", copy: "Көшіру", loading: "Анықталуда..." };
  if (lang === "en") return { current: "Use current location", address: "Exact address", coords: "Coordinates", copy: "Copy", loading: "Resolving..." };
  return { current: "Указать по моей локации", address: "Точный адрес", coords: "Координаты", copy: "Копировать", loading: "Определяем..." };
}

export default function AddressField({ lang, label, address, setAddress, lat, setLat, lng, setLng, onResolved }: Props) {
  const ui = useMemo(() => texts(lang), [lang]);
  const [busy, setBusy] = useState(false);
  const [hint, setHint] = useState("");

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
      onResolved?.({ address: data.address, lat: latValue, lng: lngValue, countryCode: data.countryCode, city: data.city, region: data.region });
    } catch (error) {
      setHint(error instanceof Error ? error.message : "Location error");
    } finally {
      setBusy(false);
    }
  }

  async function copy(value: string) {
    if (!value || typeof navigator === "undefined" || !navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(value);
      setHint("OK");
      window.setTimeout(() => setHint(""), 1200);
    } catch {}
  }

  return (
    <div className="stack">
      <div>
        <label className="field-label">{label}</label>
        <input className="field" value={address} onChange={(e) => setAddress(e.target.value)} />
      </div>
      <button type="button" className="button-secondary full" onClick={useCurrentLocation} disabled={busy}>
        {busy ? ui.loading : ui.current}
      </button>
      <div className="grid-2">
        <div>
          <label className="field-label">{ui.address}</label>
          <div className="field" style={{ minHeight: 52, display: "flex", alignItems: "center" }}>{address || "—"}</div>
          {address ? <button type="button" className="button-secondary full" style={{ marginTop: 8 }} onClick={() => copy(address)}>{ui.copy}</button> : null}
        </div>
        <div>
          <label className="field-label">{ui.coords}</label>
          <div className="field" style={{ minHeight: 52, display: "flex", alignItems: "center" }}>{lat && lng ? `${lat}, ${lng}` : "—"}</div>
          {lat && lng ? <button type="button" className="button-secondary full" style={{ marginTop: 8 }} onClick={() => copy(`${lat}, ${lng}`)}>{ui.copy}</button> : null}
        </div>
      </div>
      <div className="grid-2">
        <div>
          <label className="field-label">Lat</label>
          <input className="field" value={lat} onChange={(e) => setLat(e.target.value)} />
        </div>
        <div>
          <label className="field-label">Lng</label>
          <input className="field" value={lng} onChange={(e) => setLng(e.target.value)} />
        </div>
      </div>
      {hint ? <div className="muted">{hint}</div> : null}
    </div>
  );
}
