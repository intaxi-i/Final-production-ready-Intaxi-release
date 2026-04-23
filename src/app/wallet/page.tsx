"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import BottomNav from "@/components/BottomNav";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { api, WalletResponse, WalletTopupItem } from "@/lib/api";
import { t } from "@/lib/i18n";
import { currencyForCountry } from "@/lib/constants";

function walletUi(lang: string, currency: string) {
  const map: Record<string, Record<string, string>> = {
    ru: {
      enterValidAmount: "Введите корректную сумму",
      requestSent: "Заявка отправлена",
      genericError: "Произошла ошибка",
      amountLabel: `Сумма (${currency})`,
      cardCountry: "Страна карты",
      receiptLabel: "Чек / file ID",
      receiptPlaceholder: "Telegram file_id или комментарий",
      submitRequest: "Отправить заявку",
      adminCard: "Карта администратора",
      topupHistory: "История пополнений",
      refresh: "Обновить",
      card: "Карта",
      country: "Страна",
      receipt: "Чек",
    },
    uz: {
      enterValidAmount: "Miqdorni to'g'ri kiriting",
      requestSent: "So'rov yuborildi",
      genericError: "Xatolik yuz berdi",
      amountLabel: `Miqdor (${currency})`,
      cardCountry: "Karta davlati",
      receiptLabel: "To'lov cheki / fayl ID",
      receiptPlaceholder: "Telegram file_id yoki izoh",
      submitRequest: "So'rov yuborish",
      adminCard: "Admin karta raqami",
      topupHistory: "Top-up tarixi",
      refresh: "Yangilash",
      card: "Karta",
      country: "Davlat",
      receipt: "Chek",
    },
    en: {
      enterValidAmount: "Enter a valid amount",
      requestSent: "Request sent",
      genericError: "Something went wrong",
      amountLabel: `Amount (${currency})`,
      cardCountry: "Card country",
      receiptLabel: "Receipt / file ID",
      receiptPlaceholder: "Telegram file_id or note",
      submitRequest: "Send request",
      adminCard: "Admin card number",
      topupHistory: "Top-up history",
      refresh: "Refresh",
      card: "Card",
      country: "Country",
      receipt: "Receipt",
    },
    kz: {
      enterValidAmount: "Дұрыс соманы енгізіңіз",
      requestSent: "Сұраныс жіберілді",
      genericError: "Қате орын алды",
      amountLabel: `Сома (${currency})`,
      cardCountry: "Карта елі",
      receiptLabel: "Чек / file ID",
      receiptPlaceholder: "Telegram file_id немесе түсініктеме",
      submitRequest: "Сұраныс жіберу",
      adminCard: "Әкімші картасы",
      topupHistory: "Толықтыру тарихы",
      refresh: "Жаңарту",
      card: "Карта",
      country: "Ел",
      receipt: "Чек",
    },
    ar: {
      enterValidAmount: "أدخل مبلغًا صحيحًا",
      requestSent: "تم إرسال الطلب",
      genericError: "حدث خطأ",
      amountLabel: `المبلغ (${currency})`,
      cardCountry: "دولة البطاقة",
      receiptLabel: "الإيصال / file ID",
      receiptPlaceholder: "Telegram file_id أو ملاحظة",
      submitRequest: "إرسال الطلب",
      adminCard: "رقم بطاقة المشرف",
      topupHistory: "سجل الشحن",
      refresh: "تحديث",
      card: "البطاقة",
      country: "الدولة",
      receipt: "الإيصال",
    },
  };
  return map[lang] || map.ru;
}


export default function WalletPage() {
  const { lang, sessionToken, user, refreshUser, isReady } = useApp();
  const [wallet, setWallet] = useState<WalletResponse | null>(null);
  const [history, setHistory] = useState<WalletTopupItem[]>([]);
  const [amount, setAmount] = useState("50000");
  const [receiptFileId, setReceiptFileId] = useState("");
  const [cardCountry, setCardCountry] = useState("uz");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [lastCreated, setLastCreated] = useState<WalletTopupItem | null>(null);
  const mountedRef = useRef(true);
  const currency = currencyForCountry(user?.country);
  const ui = walletUi(lang, currency);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const loadWalletState = useCallback(async () => {
    if (!sessionToken || !mountedRef.current) return;

    if (mountedRef.current) {
      setLoading(true);
    }

    try {
      const [walletData, topupHistory] = await Promise.all([
        api.wallet(sessionToken),
        api.walletTopupHistory(sessionToken).catch(() => ({ items: [] })),
      ]);

      if (!mountedRef.current) return;

      setWallet(walletData);
      setHistory(topupHistory.items || []);
      await refreshUser();
    } catch {
      if (!mountedRef.current) return;
      setWallet(null);
      setHistory([]);
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [refreshUser, sessionToken]);

  useEffect(() => {
    if (!isReady || !sessionToken) {
      setLoading(false);
      return;
    }

    loadWalletState().catch(() => null);

    const timer = window.setInterval(() => {
      loadWalletState().catch(() => null);
    }, 15000);

    return () => {
      window.clearInterval(timer);
    };
  }, [isReady, sessionToken, loadWalletState]);

  async function submitTopup() {
    if (!sessionToken) return;

    const numericAmount = Number(amount || 0);
    if (!numericAmount || numericAmount <= 0) {
      setMessage(ui.enterValidAmount);
      return;
    }

    try {
      setBusy("topup");
      setMessage("");
      const created = await api.walletTopup(sessionToken, {
        amount: numericAmount,
        card_country: cardCountry || null,
        receipt_file_id: receiptFileId || null,
      });
      if (!mountedRef.current) return;
      setLastCreated(created);
      setReceiptFileId("");
      setMessage(ui.requestSent);
      await loadWalletState();
    } catch (error) {
      if (!mountedRef.current) return;
      setMessage(error instanceof Error ? error.message : ui.genericError);
    } finally {
      if (mountedRef.current) {
        setBusy("");
      }
    }
  }

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader
          title={t(lang, "wallet")}
          subtitle={user?.balance !== undefined ? `${user.balance} ${currency} · 0%` : t(lang, "loading")}
        />

        {message ? <div className="notice">{message}</div> : null}

        <div className="card stack">
          {loading ? (
            <div className="info-value">{t(lang, "loading")}</div>
          ) : !wallet ? (
            <div className="info-value">{t(lang, "operationFailed")}</div>
          ) : (
            <div className="info-grid">
              <div className="info-block">
                <div className="info-label">{t(lang, "balance")}</div>
                <div className="info-value">{wallet.balance} {currency}</div>
              </div>
              <div className="info-block">
                <div className="info-label">{t(lang, "commission")}</div>
                <div className="info-value">0%</div>
              </div>
              <div className="info-block">
                <div className="info-label">Service</div>
                <div className="info-value">0% commission</div>
              </div>
            </div>
          )}
        </div>

        <div className="card stack">
          <div className="card-title">{t(lang, "topup")}</div>

          <div>
            <label className="field-label">{ui.amountLabel}</label>
            <input
              className="field"
              type="number"
              min="0"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>

          <div>
            <label className="field-label">{ui.cardCountry}</label>
            <select
              className="field"
              value={cardCountry}
              onChange={(e) => setCardCountry(e.target.value)}
            >
              <option value="uz">Uzbekistan</option>
              <option value="tr">Turkey</option>
              <option value="sa">Saudi Arabia</option>
            </select>
          </div>

          <div>
            <label className="field-label">{ui.receiptLabel}</label>
            <input
              className="field"
              value={receiptFileId}
              onChange={(e) => setReceiptFileId(e.target.value)}
              placeholder={ui.receiptPlaceholder}
            />
          </div>

          <button
            className="button-main full"
            onClick={submitTopup}
            disabled={busy === "topup"}
          >
            {busy === "topup" ? t(lang, "loading") : ui.submitRequest}
          </button>

          {lastCreated?.admin_card_number ? (
            <div className="info-block">
              <div className="info-label">{ui.adminCard}</div>
              <div className="info-value">{lastCreated.admin_card_number}</div>
            </div>
          ) : null}
        </div>

        <div className="card stack">
          <div className="list-row">
            <div className="card-title">{ui.topupHistory}</div>
            <button className="button-secondary" onClick={() => loadWalletState().catch(() => null)}>
              {ui.refresh}
            </button>
          </div>

          {!history.length ? (
            <div className="muted">{t(lang, "noData")}</div>
          ) : (
            history.map((item) => (
              <div key={item.id} className="info-block">
                <div className="info-value">
                  #{item.id} {item.amount} {currency}
                </div>
                <div className="muted">{t(lang, "status")}: {item.status}</div>
                {item.admin_card_number ? (
                  <div className="muted">{ui.card}: {item.admin_card_number}</div>
                ) : null}
                {item.card_country ? (
                  <div className="muted">{ui.country}: {item.card_country}</div>
                ) : null}
                {item.receipt_file_id ? (
                  <div className="muted">{ui.receipt}: {item.receipt_file_id}</div>
                ) : null}
              </div>
            ))
          )}
        </div>
      </div>

      <BottomNav />
    </main>
  );
}
