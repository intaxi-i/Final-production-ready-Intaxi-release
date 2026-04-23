"use client";

import Link from "next/link";
import { useApp } from "@/context/AppContext";
import { APP_ROUTES } from "@/lib/constants";
import { t } from "@/lib/i18n";

type Props = {
  title: string;
  subtitle?: string;
  backHref?: string;
  highlightText?: string;
};

export default function PageHeader({
  title,
  subtitle,
  backHref = APP_ROUTES.home,
  highlightText,
}: Props) {
  const { lang } = useApp();

  return (
    <div className="page-header">
      <Link href={backHref} className="back-link">
        ← {t(lang, "back")}
      </Link>
      <h1 className="section-title">{title}</h1>
      {subtitle ? <p className="section-subtitle">{subtitle}</p> : null}
      {highlightText ? <div className="section-highlight">{highlightText}</div> : null}
    </div>
  );
}