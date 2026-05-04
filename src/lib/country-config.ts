export const COUNTRY_OPTIONS_EXTENDED = [
  { code: "uz", label: "Uzbekistan" },
  { code: "tr", label: "Turkey" },
  { code: "kz", label: "Kazakhstan" },
  { code: "sa", label: "Saudi Arabia" },
] as const;

export const DEFAULT_CITIES_EXTENDED: Record<string, string[]> = {
  tr: ["Istanbul", "Ankara", "Izmir", "Antalya", "Bursa", "Adana", "Konya", "Gaziantep", "Mersin", "Kayseri", "Eskisehir", "Trabzon"],
  kz: ["Astana", "Almaty", "Shymkent", "Karaganda", "Aktobe", "Atyrau", "Aktau", "Pavlodar", "Taraz", "Oskemen", "Semey", "Kostanay"],
  sa: ["Riyadh", "Jeddah", "Mecca", "Medina", "Dammam", "Taif", "Tabuk", "Abha", "Hail", "Jizan", "Najran", "Al Khobar"],
};
