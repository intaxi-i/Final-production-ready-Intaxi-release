export type ReverseGeoResult = {
  address: string;
  lat: number;
  lng: number;
  countryCode?: string;
  city?: string;
  region?: string;
};

function extractCity(address: Record<string, string | undefined>) {
  return (
    address.city ||
    address.town ||
    address.village ||
    address.municipality ||
    address.county ||
    address.state_district ||
    ''
  );
}

export async function getCurrentPosition(): Promise<{ lat: number; lng: number }> {
  return new Promise((resolve, reject) => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      reject(new Error('Geolocation is not supported'));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: Number(position.coords.latitude.toFixed(6)),
          lng: Number(position.coords.longitude.toFixed(6)),
        });
      },
      (error) => reject(new Error(error.message || 'Unable to get location')),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 10000 },
    );
  });
}

export async function reverseGeocode(lat: number, lng: number): Promise<ReverseGeoResult> {
  const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${encodeURIComponent(String(lat))}&lon=${encodeURIComponent(String(lng))}`;
  const response = await fetch(url, {
    headers: { Accept: 'application/json', 'Accept-Language': 'ru,en,uz' },
    cache: 'no-store',
  });
  if (!response.ok) throw new Error('Reverse geocoding failed');
  const data = await response.json();
  const address = data?.address || {};
  return {
    address: data?.display_name || `${lat}, ${lng}`,
    lat: Number(lat.toFixed(6)),
    lng: Number(lng.toFixed(6)),
    countryCode: String(address.country_code || '').toLowerCase(),
    city: extractCity(address),
    region: address.state || address.region || address.province || '',
  };
}

export async function resolveCurrentLocation(): Promise<ReverseGeoResult> {
  const { lat, lng } = await getCurrentPosition();
  return reverseGeocode(lat, lng);
}

export function haversineKm(lat1: number, lng1: number, lat2: number, lng2: number) {
  const toRad = (value: number) => (value * Math.PI) / 180;
  const radiusKm = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return 2 * radiusKm * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}
