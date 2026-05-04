"use client";

import type { MouseEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
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
  const router = useRouter();

  function handleBack(event: MouseEvent<HTMLAnchorElement>) {
    event.preventDefault();
    if (typeof window !== "undefined" && window.history.length > 1) {
      router.back();
      return;
    }
    router.push(backHref);
  }

  return (
    <div className="page-header">
      <Link href={backHref} className="back-link" onClick={handleBack}>
        ← {t(lang, "back")}
      </Link>
      <h1 className="section-title">{title}</h1>
      {subtitle ? <p className="section-subtitle">{subtitle}</p> : null}
      {highlightText ? <div className="section-highlight">{highlightText}</div> : null}
    </div>
  );
}
