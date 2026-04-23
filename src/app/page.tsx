"use client";

import Link from "next/link";
import BottomNav from "@/components/BottomNav";
import LanguageSwitcher from "@/components/LanguageSwitcher";
import { useApp } from "@/context/AppContext";
import { APP_ROUTES, currencyForCountry } from "@/lib/constants";
import { t } from "@/lib/i18n";

export default function HomePage() {
  const { lang, user, isReady } = useApp();

  return (
    <main className="page-center">
      <div className="container stack">
        <div className="card stack">
          <div className="page-top-row">
            <div>
              <h1 className="title">{t(lang, "appName")}</h1>
              <p className="subtitle">
                {isReady ? `${user?.full_name || "—"} · ${user?.username || "—"}` : t(lang, "loading")}
              </p>
            </div>
            <LanguageSwitcher />
          </div>

          <div className="info-grid">
            <div className="info-block">
              <div className="info-label">{t(lang, "username")}</div>
              <div className="info-value">{user?.username || "—"}</div>
            </div>
            <div className="info-block">
              <div className="info-label">{t(lang, "balance")}</div>
              <div className="info-value">{user?.balance ?? 0} {currencyForCountry(user?.country)}</div>
            </div>
          </div>
        </div>

        <Link
          href={APP_ROUTES.city}
          className="button-main full"
          style={{ textAlign: "center", padding: "20px 16px", fontSize: "18px" }}
        >
          {t(lang, "city")}
        </Link>

        <Link
          href={APP_ROUTES.intercity}
          className="button-main full"
          style={{ textAlign: "center", padding: "20px 16px", fontSize: "18px" }}
        >
          {t(lang, "intercity")}
        </Link>
      </div>

      <BottomNav />
    </main>
  );
}
