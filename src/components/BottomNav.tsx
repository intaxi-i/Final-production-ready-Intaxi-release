"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { APP_ROUTES } from "@/lib/constants";
import { useApp } from "@/context/AppContext";
import { t } from "@/lib/i18n";

const links = [
  { href: APP_ROUTES.home, labelKey: "home" },
  { href: APP_ROUTES.city, labelKey: "city" },
  { href: APP_ROUTES.intercity, labelKey: "intercity" },
  { href: APP_ROUTES.profile, labelKey: "profile" },
  { href: APP_ROUTES.wallet, labelKey: "wallet" },
];

export default function BottomNav() {
  const pathname = usePathname();
  const { lang } = useApp();

  return (
    <div className="bottom-nav-wrap">
      <nav className="bottom-nav">
        {links.map((link) => {
          const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
          return (
            <Link key={link.href} href={link.href} className={`bottom-link${active ? " active" : ""}`}>
              <span>{t(lang, link.labelKey)}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
