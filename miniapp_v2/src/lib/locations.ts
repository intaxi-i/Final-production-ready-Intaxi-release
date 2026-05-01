import { DEFAULT_CITIES_EXTENDED } from './country-config';

export const UZBEKISTAN_REGIONS = {
  tashkent_city: { ru: 'Город Ташкент', uz: 'Toshkent shahri', en: 'Tashkent City', kz: 'Ташкент қаласы', localities: ['Bektemir', 'Mirobod', "Mirzo Ulug'bek", 'Sergeli', 'Chilonzor', 'Yunusobod', 'Yashnobod', 'Yakkasaroy', 'Shayxontohur', 'Uchtepa', 'Olmazor', 'Yangi Hayot'] },
  tashkent_region: { ru: 'Ташкентская область', uz: 'Toshkent viloyati', en: 'Tashkent Region', kz: 'Ташкент облысы', localities: ['Nurafshon', 'Angren', 'Bekobod', 'Chirchiq', 'Olmaliq', 'Ohangaron', 'Qibray', 'Parkent', 'Yangiyo‘l'] },
  samarkand: { ru: 'Самаркандская область', uz: 'Samarqand viloyati', en: 'Samarkand Region', kz: 'Самарқанд облысы', localities: ['Samarqand', "Kattaqo'rg'on", 'Urgut', 'Toyloq', 'Jomboy'] },
  bukhara: { ru: 'Бухарская область', uz: 'Buxoro viloyati', en: 'Bukhara Region', kz: 'Бұхара облысы', localities: ['Buxoro', 'Kogon', "G'ijduvon", 'Romitan'] },
  fergana: { ru: 'Ферганская область', uz: 'Farg‘ona viloyati', en: 'Fergana Region', kz: 'Ферғана облысы', localities: ["Farg'ona", "Qo'qon", "Marg'ilon", 'Rishton'] },
} as const;

export const KAZAKHSTAN_REGIONS = {
  astana: { ru: 'Астана', uz: 'Astana', en: 'Astana', kz: 'Астана', localities: ['Astana'] },
  almaty: { ru: 'Алматы', uz: 'Almaty', en: 'Almaty', kz: 'Алматы', localities: ['Almaty'] },
  shymkent: { ru: 'Шымкент', uz: 'Shymkent', en: 'Shymkent', kz: 'Шымкент', localities: ['Shymkent'] },
} as const;

type RegionRecord = Record<string, { ru: string; uz: string; en: string; kz: string; localities: string[] }>;

function getRegions(country: string): RegionRecord {
  if (country === 'kz') return KAZAKHSTAN_REGIONS;
  if (country === 'uz') return UZBEKISTAN_REGIONS;
  return {};
}

export function getRegionOptionsForCountry(country: string, lang: string) {
  const regions = getRegions(country);
  return Object.entries(regions).map(([key, value]) => ({ key, label: value[lang as keyof typeof value] || value.ru }));
}

export function getLocalityOptionsForCountry(country: string, regionKey: string) {
  const regions = getRegions(country);
  const region = regions[regionKey];
  if (region) return region.localities;
  return DEFAULT_CITIES_EXTENDED[country] || [];
}

export function guessRegionFromCity(country: string, city: string) {
  if (!city) return '';
  const normalized = city.toLowerCase();
  const regions = getRegions(country);
  for (const [key, region] of Object.entries(regions)) {
    if ([region.ru, region.uz, region.en, region.kz].some((item) => item.toLowerCase() === normalized)) return key;
    if (region.localities.some((item) => item.toLowerCase() === normalized)) return key;
  }
  return '';
}
