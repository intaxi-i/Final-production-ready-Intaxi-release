'use client';

import { usePathname, useRouter } from 'next/navigation';
import { APP_ROUTES } from '@/lib/constants';

export function AppBackButton() {
  const pathname = usePathname();
  const router = useRouter();
  if (!pathname || pathname === APP_ROUTES.home) return null;

  function goBack() {
    if (typeof window !== 'undefined' && window.history.length > 1) {
      router.back();
      return;
    }
    router.push(APP_ROUTES.home);
  }

  return (
    <button type="button" className="app-back-button" onClick={goBack} aria-label="Назад">
      ←
    </button>
  );
}
