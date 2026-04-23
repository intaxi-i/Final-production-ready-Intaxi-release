"use client";

import { useEffect, useMemo, useState } from "react";
import BottomNav from "@/components/BottomNav";
import LocationFields from "@/components/LocationFields";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { VEHICLE_CAPACITY_OPTIONS, VEHICLE_CATALOG, currencyForCountry } from "@/lib/constants";
import { formatUzLocation, guessUzRegionFromCity } from "@/lib/locations";
import { api, HistoryResponse } from "@/lib/api";
import { t } from "@/lib/i18n";

const DONATION_WALLETS = {
  fiat: [
    { label: "UZCARD / HUMO", value: process.env.NEXT_PUBLIC_DONATE_FIAT_UZ || "8600310416548592" },
    { label: "VISA / MASTER", value: process.env.NEXT_PUBLIC_DONATE_FIAT_GLOBAL || "4195250052390109" },
  ],
  crypto: [
    { label: "Bitcoin", value: process.env.NEXT_PUBLIC_DONATE_BTC || "" },
    { label: "Ethereum", value: process.env.NEXT_PUBLIC_DONATE_ETH || "" },
    { label: "Solana", value: process.env.NEXT_PUBLIC_DONATE_SOL || "" },
  ],
};

function selectLabel(lang: string) {
  const map: Record<string, string> = { ru: "Выберите", uz: "Tanlang", en: "Select", kz: "Таңдаңыз", ar: "اختر" };
  return map[lang] || map.ru;
}

function copyLabel(lang: string) {
  const map: Record<string, string> = { ru: "Копировать", uz: "Nusxa", en: "Copy", kz: "Көшіру", ar: "نسخ" };
  return map[lang] || map.ru;
}

function settingsLabel(lang: string) {
  const map: Record<string, string> = { ru: "Настройки", uz: "Sozlamalar", en: "Settings", kz: "Баптаулар", ar: "الإعدادات" };
  return map[lang] || map.ru;
}

function donateTitle(lang: string) {
  const map: Record<string, string> = { ru: "Поддержать проект", uz: "Loyihani qo‘llab-quvvatlash", en: "Support the project", kz: "Жобаны қолдау", ar: "دعم المشروع" };
  return map[lang] || map.ru;
}

function donateText(lang: string) {
  const map: Record<string, string> = {
    ru: "Добровольная помощь на развитие продукта и покрытие расходов сервиса.",
    uz: "Mahsulot rivoji va servis xarajatlari uchun ixtiyoriy yordam.",
    en: "Voluntary support for product development and service costs.",
    kz: "Өнімді дамыту мен сервистік шығындарға ерікті қолдау.",
    ar: "دعم طوعي لتطوير المنتج وتغطية نفقات الخدمة.",
  };
  return map[lang] || map.ru;
}

export default function ProfilePage() {
  const { lang, user, setUser, sessionToken, isReady } = useApp();
  const [country, setCountry] = useState("uz");
  const [regionKey, setRegionKey] = useState("");
  const [city, setCity] = useState("");
  const [brand, setBrand] = useState("");
  const [model, setModel] = useState("");
  const [plate, setPlate] = useState("");
  const [color, setColor] = useState("");
  const [capacity, setCapacity] = useState("");
  const [saving, setSaving] = useState("");
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showVehicleEditor, setShowVehicleEditor] = useState(false);
  const role = user?.active_role || "passenger";
  const selectText = selectLabel(lang);
  const currency = currencyForCountry(user?.country);
  const visibleCryptoWallets = DONATION_WALLETS.crypto.filter((item) => item.value && !item.value.includes("ADD_YOUR"));

  useEffect(() => {
    if (!user) return;
    setCountry(user.country || "uz");
    setBrand(user.vehicle?.brand || "");
    setModel(user.vehicle?.model || "");
    setPlate(user.vehicle?.plate || "");
    setColor(user.vehicle?.color || "");
    setCapacity(user.vehicle?.capacity || "");
    const guessedRegion = guessUzRegionFromCity(user.city || "");
    if (user.country === "uz" && guessedRegion) setRegionKey(guessedRegion);
    setCity(user.city || "");
  }, [user]);

  useEffect(() => {
    let cancelled = false;
    async function loadHistory() {
      if (!sessionToken || !isReady) return;
      try {
        const data = await api.historyAll(sessionToken);
        if (!cancelled) setHistory(data);
      } catch {
        if (!cancelled) setHistory(null);
      }
    }
    void loadHistory();
    return () => { cancelled = true; };
  }, [sessionToken, isReady]);

  const cityValue = useMemo(() => {
    if (country === "uz" && regionKey && city) return formatUzLocation(regionKey, city, lang);
    return city;
  }, [country, regionKey, city, lang]);

  const brandOptions = useMemo(() => Object.keys(VEHICLE_CATALOG[country] || {}), [country]);
  const modelOptions = useMemo(() => (brand ? VEHICLE_CATALOG[country]?.[brand] || [] : []), [country, brand]);

  async function saveProfile() {
    if (!sessionToken) return;
    try {
      setSaving("profile");
      const data = await api.updateProfile(sessionToken, { country, city: cityValue });
      setUser(data.user);
    } finally {
      setSaving("");
    }
  }

  async function saveVehicle() {
    if (!sessionToken) return;
    try {
      setSaving("vehicle");
      const data = await api.updateVehicle(sessionToken, { brand, model, plate, color, capacity });
      setUser(data.user);
      setShowVehicleEditor(false);
    } finally {
      setSaving("");
    }
  }

  async function toggleRole() {
    if (!sessionToken) return;
    try {
      setSaving("role");
      const nextRole = role === "driver" ? "passenger" : "driver";
      const data = await api.updateRole(sessionToken, nextRole);
      setUser(data.user);
    } finally {
      setSaving("");
    }
  }

  async function copy(value: string) {
    if (!value || typeof navigator === "undefined" || !navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(value);
    } catch {}
  }

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title={t(lang, "profile")} subtitle={t(lang, "profileDescription")} />

        <div className="card stack">
          <div className="list-row">
            <div>
              <div className="card-title">{user?.full_name || t(lang, "loading")}</div>
              <div className="muted">@{user?.username || "—"}</div>
            </div>
            <button className="button-secondary" type="button" onClick={() => setShowSettings((prev) => !prev)}>{settingsLabel(lang)}</button>
          </div>
          <div className="info-grid">
            <div className="info-block"><div className="info-label">{t(lang, "verified")}</div><div className="info-value">{user?.is_verified ? t(lang, "verifyYes") : t(lang, "verifyNo")}</div></div>
            <div className="info-block"><div className="info-label">{t(lang, "currentRole")}</div><div className="info-value">{role}</div></div>
            <div className="info-block"><div className="info-label">{t(lang, "balance")}</div><div className="info-value">{user?.balance ?? 0} {currency}</div></div>
            <div className="info-block"><div className="info-label">{t(lang, "commission")}</div><div className="info-value">0%</div></div>
          </div>
          {role === "driver" && user?.vehicle ? (
            <div className="info-grid">
              <div className="info-block"><div className="info-label">{t(lang, "car")}</div><div className="info-value">{user.vehicle.brand || ""} {user.vehicle.model || ""}</div></div>
              <div className="info-block"><div className="info-label">{t(lang, "vehiclePlate")}</div><div className="info-value">{user.vehicle.plate || "—"}</div></div>
              <div className="info-block"><div className="info-label">{t(lang, "vehicleColor")}</div><div className="info-value">{user.vehicle.color || "—"}</div></div>
              <div className="info-block"><div className="info-label">{t(lang, "capacity")}</div><div className="info-value">{user.vehicle.capacity || "—"}</div></div>
            </div>
          ) : null}
          <button className="button-secondary full" onClick={toggleRole}>{saving === "role" ? t(lang, "loading") : role === "driver" ? t(lang, "switchToPassenger") : t(lang, "switchToDriver")}</button>
        </div>

        {showSettings ? (
          <>
            <div className="card stack">
              <div className="card-title">{t(lang, "sectionLocation")}</div>
              <LocationFields lang={lang} country={country} setCountry={setCountry} regionKey={regionKey} setRegionKey={setRegionKey} city={city} setCity={setCity} />
              <button className="button-main full" onClick={saveProfile}>{saving === "profile" ? t(lang, "loading") : t(lang, "updateProfile")}</button>
            </div>

            {role === "driver" ? (
              <div className="card stack">
                <div className="list-row">
                  <div className="card-title">{t(lang, "sectionVehicle")}</div>
                  <button className="button-secondary" type="button" onClick={() => setShowVehicleEditor((prev) => !prev)}>{showVehicleEditor ? t(lang, "close") : settingsLabel(lang)}</button>
                </div>
                {showVehicleEditor ? (
                  <>
                    <div>
                      <label className="field-label">{t(lang, "vehicleBrand")}</label>
                      <select className="field" value={brand} onChange={(e) => { setBrand(e.target.value); setModel(""); }}>
                        <option value="">{selectText}</option>
                        {brandOptions.map((item) => <option key={item} value={item}>{item}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="field-label">{t(lang, "vehicleModel")}</label>
                      <select className="field" value={model} onChange={(e) => setModel(e.target.value)}>
                        <option value="">{selectText}</option>
                        {modelOptions.map((item) => <option key={item} value={item}>{item}</option>)}
                      </select>
                    </div>
                    <div className="grid-2">
                      <div><label className="field-label">{t(lang, "vehiclePlate")}</label><input className="field" value={plate} onChange={(e) => setPlate(e.target.value)} /></div>
                      <div><label className="field-label">{t(lang, "vehicleColor")}</label><input className="field" value={color} onChange={(e) => setColor(e.target.value)} /></div>
                    </div>
                    <div>
                      <label className="field-label">{t(lang, "capacity")}</label>
                      <select className="field" value={capacity} onChange={(e) => setCapacity(e.target.value)}>
                        <option value="">{selectText}</option>
                        {VEHICLE_CAPACITY_OPTIONS.map((item) => <option key={item} value={item}>{item}</option>)}
                      </select>
                    </div>
                    <button className="button-main full" onClick={saveVehicle}>{saving === "vehicle" ? t(lang, "loading") : (lang === "ru" ? "Сохранить и отправить на проверку" : t(lang, "updateVehicle"))}</button>
                  </>
                ) : (
                  <div className="muted">{lang === "ru" ? "Изменение данных машины доступно через настройки этого блока." : t(lang, "sectionVehicle")}</div>
                )}
              </div>
            ) : null}
          </>
        ) : null}

        <div className="card stack">
          <div className="card-title">{donateTitle(lang)}</div>
          <div className="muted">{donateText(lang)}</div>
          <div className="info-grid">
            {DONATION_WALLETS.fiat.map((item) => (
              <div key={item.label} className="info-block">
                <div className="info-label">{item.label}</div>
                <div className="info-value" style={{ wordBreak: "break-all" }}>{item.value}</div>
                <button type="button" className="button-secondary full" style={{ marginTop: 8 }} onClick={() => copy(item.value)}>{copyLabel(lang)}</button>
              </div>
            ))}
            {visibleCryptoWallets.map((item) => (
              <div key={item.label} className="info-block">
                <div className="info-label">{item.label}</div>
                <div className="info-value" style={{ wordBreak: "break-all" }}>{item.value}</div>
                <button type="button" className="button-secondary full" style={{ marginTop: 8 }} onClick={() => copy(item.value)}>{copyLabel(lang)}</button>
              </div>
            ))}
          </div>
        </div>

        <div className="card stack">
          <div className="card-title">History</div>
          {!history ? <div className="muted">{t(lang, "noData")}</div> : (
            <>
              {history.city_orders.map((item) => (
                <details key={`co-${item.id}`} className="info-block">
                  <summary>{item.from_address} → {item.to_address || "—"}</summary>
                  <div className="muted">{item.status} · {item.price}</div>
                </details>
              ))}
              {history.city_trips.map((item) => (
                <details key={`ct-${item.id}`} className="info-block">
                  <summary>{item.from_address} → {item.to_address || "—"}</summary>
                  <div className="muted">{item.status} · {item.price}</div>
                </details>
              ))}
              {history.intercity_routes.map((item) => (
                <details key={`ir-${item.id}`} className="info-block">
                  <summary>{item.from_city} → {item.to_city}</summary>
                  <div className="muted">{item.status} · {item.price}</div>
                </details>
              ))}
              {history.intercity_requests.map((item) => (
                <details key={`iq-${item.id}`} className="info-block">
                  <summary>{item.from_city} → {item.to_city}</summary>
                  <div className="muted">{item.status} · {item.price_offer}</div>
                </details>
              ))}
            </>
          )}
        </div>
      </div>
      <BottomNav />
    </main>
  );
}
