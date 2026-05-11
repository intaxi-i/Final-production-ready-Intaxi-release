'use client';

import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { APP_ROUTES } from '@/lib/constants';
import { getTelegramWebApp } from '@/lib/telegram';

export function AppBackButton() {
  const pathname = usePathname();
  const router = useRouter();
  const isHome = !pathname || pathname === APP_ROUTES.home;

  useEffect(() => {
    const webapp = getTelegramWebApp();
    const backButton = webapp?.BackButton;
    if (!backButton) return;

    function goBack() {
      if (typeof window !== 'undefined' && window.history.length > 1) {
        router.back();
      } else {
        router.push(APP_ROUTES.home);
      }
    }

    if (isHome) {
      backButton.hide?.();
      return;
    }

    backButton.show?.();
    backButton.onClick?.(goBack);

    return () => {
      backButton.offClick?.(goBack);
      backButton.hide?.();
    };
  }, [isHome, router]);

  return null;
}
