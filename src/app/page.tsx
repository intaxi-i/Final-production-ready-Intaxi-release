"use client";

import Link from "next/link";
import BottomNav from "@/components/BottomNav";
import LanguageSwitcher from "@/components/LanguageSwitcher";
import { useApp } from "@/context/AppContext";
import { APP_ROUTES, currencyForCountry } from "@/lib/constants";
import { t } from "@/lib/i18n";

function BrandWordmark() {
  return (
    <div className="brand-wordmark" aria-label="Intaxi">
      <span className="brand-in">In</span><span className="brand-taxi">taxi</span>
    </div>
  );
}

export default function HomePage() {
  const { lang, user, isReady } = useApp();

  return (
    <main className="page-center">
      <div className="container stack">
        <section className="home-hero">
          <div className="home-hero-glow" />
          <div className="page-top-row">
            <div className="home-hero-copy">
              <div className="eyebrow">Premium taxi marketplace</div>
              <BrandWordmark />
              <p className="subtitle">
                {isReady ? `${user?.full_name || "-"} · ${user?.username || "-"}` : t(lang, "loading")}
              </p>
            </div>
            <LanguageSwitcher />
          </div>
          <div className="home-stats">
            <div className="home-stat"><div className="info-label">{t(lang, "username")}</div><div className="info-value">{user?.username || "-"}</div></div>
            <div className="home-stat"><div className="info-label">{t(lang, "balance")}</div><div className="info-value">{user?.balance ?? 0} {currencyForCountry(user?.country)}</div></div>
          </div>
        </section>
        <section className="home-actions">
          <Link href={APP_ROUTES.city} className="home-action-card"><div><div className="home-action-title">{t(lang, "city")}</div><div className="home-action-text">Fast city orders, smart pricing and driver bidding</div></div><div className="home-action-icon yellow">→</div></Link>
          <Link href={APP_ROUTES.intercity} className="home-action-card"><div><div className="home-action-title">{t(lang, "intercity")}</div><div className="home-action-text">Routes, passenger requests and available seats</div></div><div className="home-action-icon dark">→</div></Link>
        </section>
      </div>
      <BottomNav />
    </main>
  );
}
