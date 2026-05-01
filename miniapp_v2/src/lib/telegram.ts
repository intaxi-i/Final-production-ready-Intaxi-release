export type TelegramWebApp = {
  initData?: string;
  ready?: () => void;
  expand?: () => void;
  setHeaderColor?: (color: string) => void;
  setBackgroundColor?: (color: string) => void;
};

declare global {
  interface Window {
    Telegram?: {
      WebApp?: TelegramWebApp;
    };
  }
}

export function getTelegramWebApp(): TelegramWebApp | null {
  if (typeof window === 'undefined') return null;
  return window.Telegram?.WebApp || null;
}

export function getTelegramInitData(): string | null {
  return getTelegramWebApp()?.initData || null;
}

export function initTelegramUi() {
  const webapp = getTelegramWebApp();
  if (!webapp) return;
  webapp.ready?.();
  webapp.expand?.();
  webapp.setHeaderColor?.('#111827');
  webapp.setBackgroundColor?.('#f6f7fb');
}
