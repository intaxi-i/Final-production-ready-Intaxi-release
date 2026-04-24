"use client";

import supportData from "../../shared/support-data.json";
import { useMemo, useState } from "react";

function buttonLabel(lang: string, open: boolean) {
  const map = {
    ru: open ? "Скрыть реквизиты" : "Поддержать наш проект",
    uz: open ? "Ma’lumotlarni yashirish" : "Loyihamizni qo‘llab-quvvatlash",
    en: open ? "Hide details" : "Support our project",
    kz: open ? "Деректерді жасыру" : "Біздің жобаны қолдау",
    ar: open ? "إخفاء التفاصيل" : "ادعم مشروعنا",
  } as const;
  return map[lang as keyof typeof map] || map.ru;
}

function hint(lang: string) {
  const map = {
    ru: "После нажатия откроются карты и адреса криптовалют для добровольной поддержки проекта.",
    uz: "Bosilgandan keyin loyiha uchun ixtiyoriy yordam rekvizitlari ochiladi.",
    en: "Tap to show cards and crypto addresses for voluntary project support.",
    kz: "Басқаннан кейін жобаға ерікті қолдау деректері ашылады.",
    ar: "بعد الضغط ستظهر البطاقات وعناوين العملات المشفرة للدعم الطوعي للمشروع.",
  } as const;
  return map[lang as keyof typeof map] || map.ru;
}

function copyLabel(lang: string) {
  const map = { ru: "Копировать", uz: "Nusxa", en: "Copy", kz: "Көшіру", ar: "نسخ" } as const;
  return map[lang as keyof typeof map] || map.ru;
}

export default function SupportToggle({ lang }: { lang: string }) {
  const [open, setOpen] = useState(false);
  const items = useMemo(() => {
    const fiat = Array.isArray((supportData as any).fiat) ? (supportData as any).fiat.filter((item: any) => item?.value) : [];
    const crypto = Array.isArray((supportData as any).crypto) ? (supportData as any).crypto.filter((item: any) => item?.value) : [];
    return [...fiat, ...crypto];
  }, []);

  async function copy(value: string) {
    if (!value || typeof navigator === "undefined" || !navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(value);
    } catch {}
  }

  return (
    <div className="card stack">
      <button type="button" className="button-secondary full" onClick={() => setOpen((prev) => !prev)}>
        {buttonLabel(lang, open)}
      </button>
      <div className="muted">{hint(lang)}</div>
      {open ? (
        <div className="info-grid">
          {items.length ? items.map((item: any) => (
            <div key={item.label} className="info-block">
              <div className="info-label">{item.label}</div>
              <div className="info-value" style={{ wordBreak: "break-all" }}>{item.value}</div>
              <button type="button" className="button-secondary full" style={{ marginTop: 8 }} onClick={() => copy(item.value)}>{copyLabel(lang)}</button>
            </div>
          )) : <div className="muted">—</div>}
        </div>
      ) : null}
    </div>
  );
}
