"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, MeResponse } from "@/lib/api";
import { AppLanguage, ThemeMode, THEME_PALETTE } from "@/lib/constants";
import { getTelegramWebApp, TelegramThemeParams } from "@/lib/telegram";

type AppState = {
  lang: AppLanguage;
  setLang: (lang: AppLanguage) => void;
  theme: ThemeMode;
  sessionToken: string;
  user: MeResponse | null;
  setUser: (user: MeResponse | null) => void;
  refreshUser: () => Promise<MeResponse | null>;
  isReady: boolean;
};

const AppContext = createContext<AppState | null>(null);

function normalizeLanguage(code?: string | null): AppLanguage {
  const value = (code || "").toLowerCase();
  if (value === "kk" || value === "kz") return "kz";
  if (value === "uz") return "uz";
  if (value === "ru") return "ru";
  if (value === "en") return "en";
  if (value === "ar") return "ar";
  if (typeof navigator !== "undefined") {
    const browserLang = navigator.language.toLowerCase();
    if (browserLang.startsWith("kk")) return "kz";
    if (browserLang.startsWith("uz")) return "uz";
    if (browserLang.startsWith("en")) return "en";
    if (browserLang.startsWith("ar")) return "ar";
  }
  return "ru";
}

function applyThemeToDom(theme: ThemeMode, themeParams?: TelegramThemeParams) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  root.dataset.theme = theme;
  root.lang = root.lang || "ru";
  const palette = THEME_PALETTE[theme];
  root.style.setProperty("--app-bg", themeParams?.bg_color || palette.bg);
  root.style.setProperty("--app-surface", themeParams?.secondary_bg_color || palette.surface);
  root.style.setProperty("--app-surface-soft", palette.surfaceSoft);
  root.style.setProperty("--app-border", palette.border);
  root.style.setProperty("--app-text", themeParams?.text_color || palette.text);
  root.style.setProperty("--app-muted", themeParams?.hint_color || palette.muted);
  root.style.setProperty("--app-accent", themeParams?.button_color || palette.accent);
  root.style.setProperty("--app-accent-text", themeParams?.button_text_color || palette.accentText);
  root.style.setProperty("--app-header", themeParams?.header_bg_color || palette.header);
  root.style.setProperty("--app-danger-bg", palette.dangerBg);
  root.style.setProperty("--app-danger-text", palette.dangerText);
  root.style.setProperty("--app-shadow", palette.shadow);
  if (theme === "dark") {
    root.style.colorScheme = "dark";
  } else {
    root.style.colorScheme = "light";
  }
  document.body.style.backgroundColor = themeParams?.bg_color || palette.bg;
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<AppLanguage>("ru");
  const [theme, setTheme] = useState<ThemeMode>("light");
  const [sessionToken, setSessionToken] = useState("");
  const [user, setUser] = useState<MeResponse | null>(null);
  const [isReady, setIsReady] = useState(false);

  const refreshUser = useCallback(async () => {
    if (!sessionToken) return null;
    try {
      const me = await api.me(sessionToken);
      setUser(me);
      if (me?.language) setLang(normalizeLanguage(me.language));
      return me;
    } catch {
      return null;
    }
  }, [sessionToken]);

  function setLang(langValue: AppLanguage) {
    setLangState(langValue);
    if (typeof window !== "undefined") {
      localStorage.setItem("intaxi_lang", langValue);
    }
    if (typeof document !== "undefined") {
      document.documentElement.lang = langValue;
      document.documentElement.dir = langValue === "ar" ? "rtl" : "ltr";
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function createFreshSession() {
      const webApp = getTelegramWebApp();
      const isLocalHost =
        typeof window !== "undefined" &&
        ["localhost", "127.0.0.1"].includes(window.location.hostname);
      const session = webApp?.initData
        ? await api.authTelegram({ init_data: webApp.initData })
        : isLocalHost
          ? await api.devSession()
          : (() => {
              throw new Error("Telegram WebApp auth is required");
            })();

      if (cancelled) return null;
      setSessionToken(session.session_token);

      if (typeof window !== "undefined") {
        localStorage.setItem("intaxi_session_token", session.session_token);
      }
      const me = await api.me(session.session_token);
      if (cancelled) return null;
      setUser(me);
      if (me?.language) setLang(normalizeLanguage(me.language));
      return me;
    }

    async function bootstrap() {
      const webApp = getTelegramWebApp();
      webApp?.ready();
      webApp?.expand();

      const savedLang = typeof window !== "undefined" ? localStorage.getItem("intaxi_lang") : null;
      const initialLang = normalizeLanguage(savedLang || webApp?.initDataUnsafe?.user?.language_code);
      const initialTheme: ThemeMode =
        webApp?.colorScheme === "dark" ||
        (typeof window !== "undefined" &&
          !localStorage.getItem("intaxi_theme") &&
          window.matchMedia &&
          window.matchMedia("(prefers-color-scheme: dark)").matches) ||
        localStorage.getItem("intaxi_theme") === "dark"
          ? "dark"
          : "light";

      if (!cancelled) {
        setLang(initialLang);
        setTheme(initialTheme);
        applyThemeToDom(initialTheme, webApp?.themeParams);
        webApp?.setHeaderColor?.(THEME_PALETTE[initialTheme].header);
        webApp?.setBackgroundColor?.(THEME_PALETTE[initialTheme].bg);
      }

      try {
        const savedToken =
          typeof window !== "undefined" ? localStorage.getItem("intaxi_session_token") : null;

        if (webApp?.initData) {
          if (typeof window !== "undefined") localStorage.removeItem("intaxi_session_token");
          await createFreshSession();
          return;
        }

        if (savedToken) {
          try {
            const me = await api.me(savedToken);
            if (cancelled) return;
            setSessionToken(savedToken);
            setUser(me);
            if (me?.language) setLang(normalizeLanguage(me.language));
            return;
          } catch {
            if (typeof window !== "undefined") localStorage.removeItem("intaxi_session_token");
          }
        }

        await createFreshSession();
      } catch {
        if (typeof window !== "undefined") localStorage.removeItem("intaxi_session_token");
        if (!cancelled) {
          setSessionToken("");
          setUser(null);
        }
      } finally {
        if (!cancelled) setIsReady(true);
      }
    }

    bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!isReady || !sessionToken || !user) return;
    const current = normalizeLanguage(user.language);
    if (current === lang) return;

    let cancelled = false;
    void api
      .updateProfile(sessionToken, { language: lang })
      .then((data) => {
        if (!cancelled) {
          setUser(data.user);
        }
      })
      .catch(() => null);

    return () => {
      cancelled = true;
    };
  }, [isReady, lang, sessionToken, user]);

  const value = useMemo(
    () => ({ lang, setLang, theme, sessionToken, user, setUser, refreshUser, isReady }),
    [lang, theme, sessionToken, user, refreshUser, isReady]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const value = useContext(AppContext);
  if (!value) throw new Error("useApp must be used within AppProvider");
  return value;
}
