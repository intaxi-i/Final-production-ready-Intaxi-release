'use client';

import { useCallback, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { APP_ROUTES } from '@/lib/constants';
import { getTelegramWebApp } from '@/lib/telegram';

export function AppBackButton() {
  const pathname = usePathname();
  const router = useRouter();
  const isHome = !pathname || pathname === APP_ROUTES.home;

  const goBack = useCallback(() => {
    if (typeof window !== 'undefined' && window.history.length > 1) {
      router.back();
      return;
    }
    router.push(APP_ROUTES.home);
  }, [router]);

  useEffect(() => {
    const backButton = getTelegramWebApp()?.BackButton;
    if (!backButton) return;

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
  }, [goBack, isHome]);

  return null;
}
