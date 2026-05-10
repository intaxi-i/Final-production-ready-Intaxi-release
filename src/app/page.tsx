"use client";

import Link from "next/link";
import BottomNav from "@/components/BottomNav";
import LanguageSwitcher from "@/components/LanguageSwitcher";
import { useApp } from "@/context/AppContext";
import { APP_ROUTES, currencyForCountry } from "@/lib/constants";
import { t } from "@/lib/i18n";

function BrandWordmark() {
  return (
    <div aria-label="Intaxi" style={{ marginTop: 8, fontFamily: "var(--font-unbounded), var(--font-manrope), system-ui, sans-serif", fontSize: 36, fontWeight: 800, letterSpacing: "-0.06em", lineHeight: 1 }}>
      <span style={{ color: "var(--app-accent)" }}>In</span><span style={{ color: "var(--app-text)" }}>taxi</span>
    </div>
  );
}

export default function HomePage() {
  const { lang, user, isReady } = useApp();

  return (
    <main className="page-center">
      <div className="container stack">
        <section className="card stack" style={{ position: "relative", overflow: "hidden", borderRadius: 34, padding: 24 }}>
          <div style={{ position: "absolute", right: -48, top: -48, width: 144, height: 144, borderRadius: 999, background: "var(--app-accent)", opacity: 0.2, filter: "blur(30px)" }} />
          <div className="page-top-row">
            <div style={{ minWidth: 0 }}>
              <div style={{ color: "var(--app-muted)", fontSize: 11, fontWeight: 900, letterSpacing: "0.2em", textTransform: "uppercase" }}>Premium taxi marketplace</div>
              <BrandWordmark />
              <p className="subtitle">{isReady ? `${user?.full_name || "-"} · ${user?.username || "-"}` : t(lang, "loading")}</p>
            </div>
            <LanguageSwitcher />
          </div>
          <div className="info-grid" style={{ marginTop: 10 }}>
            <div className="info-block"><div className="info-label">{t(lang, "username")}</div><div className="info-value">{user?.username || "-"}</div></div>
            <div className="info-block"><div className="info-label">{t(lang, "balance")}</div><div className="info-value">{user?.balance ?? 0} {currencyForCountry(user?.country)}</div></div>
          </div>
        </section>

        <Link href={APP_ROUTES.city} className="card page-top-row" style={{ borderRadius: 30 }}>
          <div><div className="card-title" style={{ fontSize: 21 }}>{t(lang, "city")}</div><div className="muted" style={{ marginTop: 4, fontSize: 13, fontWeight: 700 }}>Fast city orders, smart pricing and driver bidding</div></div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 56, height: 56, borderRadius: 20, background: "var(--app-accent)", color: "var(--app-accent-text)", fontSize: 24, fontWeight: 900, flexShrink: 0 }}>→</div>
        </Link>

        <Link href={APP_ROUTES.intercity} className="card page-top-row" style={{ borderRadius: 30 }}>
          <div><div className="card-title" style={{ fontSize: 21 }}>{t(lang, "intercity")}</div><div className="muted" style={{ marginTop: 4, fontSize: 13, fontWeight: 700 }}>Routes, passenger requests and available seats</div></div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 56, height: 56, borderRadius: 20, background: "var(--app-text)", color: "var(--app-surface)", fontSize: 24, fontWeight: 900, flexShrink: 0 }}>→</div>
        </Link>
      </div>
      <BottomNav />
    </main>
  );
}
