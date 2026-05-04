export interface RegionInfo {
  ru: string;
  uz: string;
  en: string;
  kz: string;
  localities: readonly string[]; // Добавлено readonly
}

export type RegionRecord = Record<string, RegionInfo>;

export const KAZAKHSTAN_REGIONS = {
  astana: {
    ru: 'Астана',
    uz: 'Astana',
    en: 'Astana',
    kz: 'Астана',
    localities: ['Astana'],
  },
  almaty: {
    ru: 'Алматы',
    uz: 'Almaty',
    en: 'Almaty',
    kz: 'Алматы',
    localities: ['Almaty'],
  },
  shymkent: {
    ru: 'Шымкент',
    uz: 'Shymkent',
    en: 'Shymkent',
    kz: 'Шымкент',
    localities: ['Shymkent'],
  },
} as const;

export const UZBEKISTAN_REGIONS = {
  tashkent: {
    ru: 'Ташкент',
    uz: 'Toshkent',
    en: 'Tashkent',
    kz: 'Ташкент',
    localities: ['Tashkent'],
  },
  samarkand: {
    ru: 'Самарканд',
    uz: 'Samarqand',
    en: 'Samarkand',
    kz: 'Самарқанд',
    localities: ['Samarqand'],
  },
} as const;

export function getRegions(country: string): RegionRecord {
  if (country === 'kz') return KAZAKHSTAN_REGIONS as unknown as RegionRecord;
  if (country === 'uz') return UZBEKISTAN_REGIONS as unknown as RegionRecord;
  return {};
}

export function getAllLocalities(country: string): string[] {
  const regions = getRegions(country);
  return Object.values(regions).flatMap((r) => [...r.localities]);
}