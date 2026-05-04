export interface RegionInfo {
  ru: string;
  uz: string;
  en: string;
  kz: string;
  localities: readonly string[];
}

export type RegionRecord = Record<string, RegionInfo>;

export interface LocationOption {
  key: string;
  value: string;
  label: string;
}

export const KAZAKHSTAN_REGIONS = {
  astana: { ru: 'Астана', uz: 'Astana', en: 'Astana', kz: 'Астана', localities: ['Astana'] },
  almaty: { ru: 'Алматы', uz: 'Almaty', en: 'Almaty', kz: 'Алматы', localities: ['Almaty'] },
  shymkent: { ru: 'Шымкент', uz: 'Shymkent', en: 'Shymkent', kz: 'Шымкент', localities: ['Shymkent'] },
} as const;

export const UZBEKISTAN_REGIONS = {
  tashkent: { ru: 'Ташкент', uz: 'Toshkent', en: 'Toshkent', kz: 'Ташкент', localities: ['Tashkent'] },
  samarkand: { ru: 'Самарканд', uz: 'Samarqand', en: 'Samarkand', kz: 'Самарқанд', localities: ['Samarqand'] },
} as const;

export function getRegions(country: string): RegionRecord {
  if (country === 'kz') return KAZAKHSTAN_REGIONS as unknown as RegionRecord;
  if (country === 'uz') return UZBEKISTAN_REGIONS as unknown as RegionRecord;
  return {};
}

export function getAllLocalities(country: string): string[] {
  const regions = getRegions(country);
  return Object.values(regions).flatMap((region) => [...region.localities]);
}

export function getLocalityOptionsForCountry(country: string, regionKey?: string | null): LocationOption[] {
  const regions = getRegions(country);
  const mapper = (locality: string) => ({ key: locality, value: locality, label: locality });

  if (regionKey && regions[regionKey]) {
    return regions[regionKey].localities.map(mapper);
  }
  return Object.values(regions).flatMap((region) => region.localities.map(mapper));
}

function resolveRegionLabel(region: RegionInfo, lang: string): string {
  if (lang === 'uz') return region.uz;
  if (lang === 'en') return region.en;
  if (lang === 'kz') return region.kz;
  return region.ru;
}

export function getRegionOptionsForCountry(country: string, lang: string = 'ru'): LocationOption[] {
  const regions = getRegions(country);
  return Object.entries(regions).map(([key, region]) => ({
    key,
    value: key,
    label: resolveRegionLabel(region, lang),
  }));
}

export function guessRegionFromCity(city: string | null, country: string): string | null {
  if (!city) return null;
  const regions = getRegions(country);
  for (const [regionKey, regionInfo] of Object.entries(regions)) {
    if (regionInfo.localities.includes(city)) return regionKey;
  }
  return null;
}