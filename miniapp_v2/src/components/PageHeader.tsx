'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { MouseEvent } from 'react';
import { APP_ROUTES } from '@/lib/constants';
import { t } from '@/lib/i18n';

export function PageHeader({
  title,
  subtitle,
  backHref = APP_ROUTES.home,
  highlightText,
  lang = 'ru',
}: {
  title: string;
  subtitle?: string;
  backHref?: string;
  highlightText?: string;
  lang?: string;
}) {
  const router = useRouter();

  function handleBack(event: MouseEvent<HTMLAnchorElement>) {
    event.preventDefault();
    if (typeof window !== 'undefined' && window.history.length > 1) {
      router.back();
      return;
    }
    router.push(backHref);
  }

  return (
    <header className="page-header">
      <Link href={backHref} className="back-link" onClick={handleBack}>← {t(lang, 'back')}</Link>
      <h1 className="title">{title}</h1>
      {subtitle ? <p className="subtitle">{subtitle}</p> : null}
      {highlightText ? <div className="section-highlight">{highlightText}</div> : null}
    </header>
  );
}
