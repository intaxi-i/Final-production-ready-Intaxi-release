export type WorldCountryOption = {
  code: string;
  label: string;
};

const FALLBACK_COUNTRIES: WorldCountryOption[] = [
  { code: 'uz', label: 'Uzbekistan' },
  { code: 'kz', label: 'Kazakhstan' },
  { code: 'tr', label: 'Turkey' },
  { code: 'sa', label: 'Saudi Arabia' },
  { code: 'ae', label: 'United Arab Emirates' },
  { code: 'ru', label: 'Russia' },
  { code: 'us', label: 'United States' },
  { code: 'de', label: 'Germany' },
  { code: 'fr', label: 'France' },
  { code: 'gb', label: 'United Kingdom' },
];

export function getWorldCountryOptions(locale = 'ru'): WorldCountryOption[] {
  try {
    const intlWithRegions = Intl as typeof Intl & { supportedValuesOf?: (key: 'region') => string[] };
    const regions = intlWithRegions.supportedValuesOf?.('region') || [];
    const names = new Intl.DisplayNames([locale, 'en'], { type: 'region' });
    return regions
      .map((region) => ({ code: region.toLowerCase(), label: names.of(region) || region }))
      .filter((item) => item.label && item.code.length === 2)
      .sort((a, b) => a.label.localeCompare(b.label, locale));
  } catch {
    return FALLBACK_COUNTRIES;
  }
}
