'use client';

import { useEffect } from 'react';
import { initTelegramUi } from '@/lib/telegram';

function loadTelegramScript() {
  if (typeof window === 'undefined') return Promise.resolve();
  if (window.Telegram?.WebApp) return Promise.resolve();
  if (document.querySelector('script[data-intaxi-telegram-sdk="true"]')) {
    return new Promise<void>((resolve) => setTimeout(resolve, 150));
  }

  return new Promise<void>((resolve) => {
    const script = document.createElement('script');
    script.dataset.intaxiTelegramSdk = 'true';
    script.src = 'https:' + '//telegram.org/js/telegram-web-app.js';
    script.onload = () => resolve();
    script.onerror = () => resolve();
    document.head.appendChild(script);
  });
}

export function TelegramBootstrap() {
  useEffect(() => {
    let cancelled = false;

    async function boot() {
      await loadTelegramScript();
      if (!cancelled) initTelegramUi();
    }

    void boot();

    return () => {
      cancelled = true;
    };
  }, []);

  return null;
}
