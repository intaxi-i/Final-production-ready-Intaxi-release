"use client";

import { useCallback, useEffect, useState } from "react";
import BottomNav from "@/components/BottomNav";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { api, TariffItem, WalletTopupItem } from "@/lib/api";
import { t } from "@/lib/i18n";

export default function AdminPage() {
  const { lang, sessionToken, refreshUser, isReady } = useApp();
  const [items, setItems] = useState<WalletTopupItem[]>([]);
  const [tariffs, setTariffs] = useState<TariffItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [message, setMessage] = useState("");

  const loadPending = useCallback(async () => {
    if (!sessionToken) return;
    setLoading(true);
    try {
      const [payments, tariffData] = await Promise.all([
        api.adminPendingPayments(sessionToken).catch(() => ({ items: [] })),
        api.adminTariffs(sessionToken).catch(() => ({ items: [] })),
      ]);
      setItems(payments.items || []);
      setTariffs(tariffData.items || []);
    } catch (error) {
      setItems([]);
      setTariffs([]);
      setMessage(error instanceof Error ? error.message : "Xatolik yuz berdi");
    } finally {
      setLoading(false);
    }
  }, [sessionToken]);

  useEffect(() => {
    if (!isReady || !sessionToken) { setLoading(false); return; }
    void loadPending();
  }, [isReady, sessionToken, loadPending]);

  async function approve(id: number) {
    if (!sessionToken) return;
    try {
      setBusyId(id); setMessage("");
      await api.adminApprovePayment(sessionToken, id);
      await Promise.all([loadPending(), refreshUser()]);
      setMessage("Tolov tasdiqlandi");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Xatolik yuz berdi");
    } finally { setBusyId(null); }
  }

  async function reject(id: number) {
    if (!sessionToken) return;
    try {
      setBusyId(id); setMessage("");
      await api.adminRejectPayment(sessionToken, id);
      await Promise.all([loadPending(), refreshUser()]);
      setMessage("Tolov rad etildi");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Xatolik yuz berdi");
    } finally { setBusyId(null); }
  }

  async function updateTariff(item: TariffItem, value: string) {
    if (!sessionToken) return;
    try {
      await api.updateTariff(sessionToken, { country: item.country, price_per_km: Number(value), currency: item.currency });
      await loadPending();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Xatolik yuz berdi");
    }
  }

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title="Admin" subtitle="Payment moderation" />
        {message ? <div className="notice">{message}</div> : null}

        <div className="card stack">
          <div className="list-row"><div className="card-title">Tariffs</div><button className="button-secondary" onClick={() => void loadPending()}>Refresh</button></div>
          {tariffs.map((item) => (
            <div key={item.country} className="info-block">
              <div className="info-value">{item.country.toUpperCase()} — {item.currency}</div>
              <input className="field" defaultValue={String(item.price_per_km)} onBlur={(e) => void updateTariff(item, e.target.value)} />
            </div>
          ))}
        </div>

        <div className="card stack">
          <div className="list-row"><div className="card-title">Kutilayotgan tolovlar</div><button className="button-secondary" onClick={() => void loadPending()}>Yangilash</button></div>
          {loading ? <div className="info-value">{t(lang, "loading")}</div> : !items.length ? <div className="muted">{t(lang, "noData")}</div> : items.map((item) => (
            <div key={item.id} className="info-block">
              <div className="info-value">#{item.id} - {item.amount}</div>
              {item.driver_tg_id ? <div className="muted">Foydalanuvchi: {item.driver_tg_id}</div> : null}
              <div className="muted">Status: {item.status}</div>
              <div className="actions-row" style={{ marginTop: 12 }}>
                <button className="button-main" disabled={busyId === item.id} onClick={() => void approve(item.id)}>{busyId === item.id ? t(lang, "loading") : "Approve"}</button>
                <button className="button-secondary" disabled={busyId === item.id} onClick={() => void reject(item.id)}>{busyId === item.id ? t(lang, "loading") : "Reject"}</button>
              </div>
            </div>
          ))}
        </div>
      </div>
      <BottomNav />
    </main>
  );
}
