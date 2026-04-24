export const APP_NAME = "Intaxi";

export const APP_ROUTES = {
  home: "/",
  city: "/city",
  cityCreate: "/city/create",
  cityOffers: "/city/offers",
  cityMyOrders: "/city/my-orders",
  intercity: "/intercity",
  intercityRequest: "/intercity/request",
  intercityRoute: "/intercity/route",
  intercityOffers: "/intercity/offers",
  myRequests: "/intercity/my-requests",
  myRoutes: "/intercity/my-routes",
  currentTrip: "/trip/current",
  profile: "/profile",
  wallet: "/wallet",
  admin: "/admin",
};

export const LANGUAGES = ["uz", "kz", "ru", "en", "ar"] as const;
export type AppLanguage = typeof LANGUAGES[number];

export type ThemeMode = "light" | "dark";

export const COUNTRY_OPTIONS = [
  { code: "uz", label: "Uzbekistan" },
  { code: "tr", label: "Turkey" },
  { code: "kz", label: "Kazakhstan" },
  { code: "sa", label: "Saudi Arabia" },
] as const;

export const DEFAULT_CITIES: Record<string, string[]> = {
  tr: ["Istanbul", "Ankara", "Izmir", "Antalya", "Bursa", "Adana", "Konya", "Gaziantep", "Mersin", "Kayseri", "Eskisehir", "Trabzon"],
  kz: ["Astana", "Almaty", "Shymkent", "Karaganda", "Aktobe", "Atyrau", "Aktau", "Pavlodar", "Taraz", "Oskemen", "Semey", "Kostanay"],
  sa: ["Riyadh", "Jeddah", "Mecca", "Medina", "Dammam", "Taif", "Tabuk", "Abha", "Hail", "Jizan", "Najran", "Al Khobar"],
};

export const LANGUAGE_OPTIONS: { code: AppLanguage; label: string }[] = [
  { code: "uz", label: "O'zbekcha" },
  { code: "kz", label: "Қазақша" },
  { code: "ru", label: "Русский" },
  { code: "en", label: "English" },
  { code: "ar", label: "العربية" },
];

export const THEME_PALETTE = {
  light: {
    bg: "#f5f7fb",
    surface: "#ffffff",
    surfaceSoft: "#f8fafc",
    border: "#dbe1ea",
    text: "#111827",
    muted: "#64748b",
    accent: "#f5c242",
    accentText: "#111827",
    dangerBg: "#fee2e2",
    dangerText: "#991b1b",
    header: "#f5c242",
    shadow: "0 4px 14px rgba(0, 0, 0, 0.04)",
  },
  dark: {
    bg: "#0f172a",
    surface: "#162033",
    surfaceSoft: "#1b2638",
    border: "#2b364b",
    text: "#f8fafc",
    muted: "#9fb0c8",
    accent: "#f5c242",
    accentText: "#111827",
    dangerBg: "#47212c",
    dangerText: "#fecaca",
    header: "#162033",
    shadow: "0 8px 20px rgba(0, 0, 0, 0.28)",
  },
} as const;

export function formatCountryLabel(code?: string) {
  const item = COUNTRY_OPTIONS.find((entry) => entry.code === code);
  return item?.label || "—";
}

export const VEHICLE_CAPACITY_OPTIONS = ["4", "6", "8+"];

export const VEHICLE_CATALOG: Record<string, Record<string, string[]>> = {
  uz: {
    Chevrolet: ["Cobalt", "Gentra", "Nexia", "Lacetti", "Malibu", "Tracker", "Damas"],
    Kia: ["K5", "K8", "Carnival", "Sonet", "Sportage"],
    Chery: ["Tiggo 7", "Tiggo 8"],
    Hyundai: ["Elantra", "Sonata", "Tucson", "Staria"],
    Toyota: ["Corolla", "Camry", "Land Cruiser", "Hiace"],
    BYD: ["Song Plus", "Han", "Chazor"],
  },
  tr: {
    Renault: ["Clio", "Megane", "Taliant"],
    Fiat: ["Egea", "Doblo", "Fiorino"],
    Toyota: ["Corolla", "Camry", "Proace City"],
    Volkswagen: ["Passat", "Caddy", "Transporter"],
    Ford: ["Focus", "Tourneo Courier", "Transit"],
    Hyundai: ["i20", "Elantra", "Tucson"],
  },
  kz: {
    Toyota: ["Camry", "Corolla", "Land Cruiser", "RAV4", "Hiace"],
    Hyundai: ["Elantra", "Sonata", "Tucson", "Santa Fe", "Staria"],
    Kia: ["K5", "Cerato", "Sportage", "Carnival"],
    Chevrolet: ["Cobalt", "Onix", "Malibu", "Tracker"],
    Lexus: ["ES", "RX", "GX", "LX"],
    Volkswagen: ["Polo", "Passat", "Tiguan", "Multivan"],
  },
  sa: {
    Toyota: ["Camry", "Corolla", "Innova", "Hiace"],
    Hyundai: ["Accent", "Sonata", "Staria", "H1"],
    Kia: ["K5", "Carnival", "Cerato"],
    Nissan: ["Sunny", "Altima", "Urvan"],
    GMC: ["Yukon", "Terrain"],
    Honda: ["Accord", "City", "CR-V"],
  },
};

export function currencyForCountry(code?: string | null) {
  const map: Record<string, string> = { uz: 'UZS', kz: 'KZT', tr: 'TRY', sa: 'SAR' };
  return map[(code || '').toLowerCase()] || 'USD';
}
