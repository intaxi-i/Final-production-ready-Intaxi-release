export type TelegramBackButton = {
  show?: () => void;
  hide?: () => void;
  onClick?: (callback: () => void) => void;
  offClick?: (callback: () => void) => void;
};

export type TelegramUser = {
  id?: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  photo_url?: string;
};

export type TelegramWebApp = {
  initData?: string;
  initDataUnsafe?: {
    user?: TelegramUser;
  };
  ready?: () => void;
  expand?: () => void;
  setHeaderColor?: (color: string) => void;
  setBackgroundColor?: (color: string) => void;
  BackButton?: TelegramBackButton;
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

export function getTelegramUser(): TelegramUser | null {
  const webapp = getTelegramWebApp();
  const unsafeUser = webapp?.initDataUnsafe?.user;
  if (unsafeUser) return unsafeUser;

  const initData = webapp?.initData;
  if (!initData) return null;

  try {
    const params = new URLSearchParams(initData);
    const rawUser = params.get('user');
    return rawUser ? JSON.parse(rawUser) as TelegramUser : null;
  } catch {
    return null;
  }
}

export function initTelegramUi() {
  const webapp = getTelegramWebApp();
  if (!webapp) return;
  webapp.ready?.();
  webapp.expand?.();
  webapp.setHeaderColor?.('#111827');
  webapp.setBackgroundColor?.('#f6f7fb');
}
