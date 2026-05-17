import { getTelegramInitData, getTelegramUser } from './telegram';
import type {
  CityOrder,
  CityTrip,
  CommissionRule,
  DonationPaymentSetting,
  DriverOnlineState,
  DriverPaymentMethod,
  IntercityOffer,
  IntercityRequestInput,
  IntercityRouteInput,
  IntercityTrip,
  PendingDriverProfile,
  PendingPayment,
  RideMode,
  UserMe,
  UserRole,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_INTAXI_API_BASE_URL || 'https://api.intaxi.best';
const DEV_USER_TOKEN = process.env.NEXT_PUBLIC_INTAXI_DEV_USER_TOKEN || 'dev:1';
const SESSION_STORAGE_KEY = 'intaxi_api_session_token';
const LIVE_CITY_TRIP_STATUSES = new Set(['accepted', 'driver_on_way', 'driver_arrived', 'in_progress']);
const LIVE_INTERCITY_TRIP_STATUSES = new Set(['accepted', 'driver_on_way', 'driver_arrived', 'in_progress']);
const LIVE_ORDER_STATUSES = new Set(['active', 'search', 'accepted']);

export class ApiError extends Error {
  code: string;
  details: Record<string, unknown>;

  constructor(message: string, code = 'api_error', details: Record<string, unknown> = {}) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.details = details;
  }
}

type BackendUser = { id?: number | null; tg_id?: number | null; full_name?: string | null; username?: string | null; language?: string | null; country?: string | null; country_code?: string | null; active_role?: UserRole | null; is_verified?: boolean | null; is_blocked?: boolean | null; rating?: number | null; rating_count?: number | null; photo_url?: string | null };
type BackendCityOrder = { id?: number; creator_tg_id?: number | null; country?: string | null; country_code?: string | null; from_address?: string | null; pickup_address?: string | null; to_address?: string | null; destination_address?: string | null; seats?: number | null; price?: number | null; passenger_price?: number | null; recommended_price?: number | null; minimum_recommended_price?: number | null; currency?: string | null; estimated_distance_km?: number | null; estimated_trip_min?: number | null; estimated_duration_min?: number | null; status?: string | null; seen_by_drivers?: number | null; active_trip_id?: number | null; accepted_trip_id?: number | null };
type BackendIntercityOffer = { kind?: string; id?: number; country?: string | null; country_code?: string | null; from_city?: string | null; from_text?: string | null; to_city?: string | null; to_text?: string | null; date?: string | null; time?: string | null; seats?: number | null; seats_needed?: number | null; price?: number | null; price_offer?: number | null; currency?: string | null; status?: string | null };

function storageAvailable() { return typeof window !== 'undefined' && typeof window.sessionStorage !== 'undefined'; }
function getStoredSessionToken() { return storageAvailable() ? window.sessionStorage.getItem(SESSION_STORAGE_KEY) : null; }
function setStoredSessionToken(token: string | null) { if (!storageAvailable()) return; if (token) window.sessionStorage.setItem(SESSION_STORAGE_KEY, token); else window.sessionStorage.removeItem(SESSION_STORAGE_KEY); }
function parseDevTgId() { const parsed = Number(DEV_USER_TOKEN.replace('dev:', '').trim()); return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined; }
function sleep(ms: number) { return new Promise((resolve) => setTimeout(resolve, ms)); }

async function waitForTelegramInitData() {
  for (let attempt = 0; attempt < 20; attempt += 1) {
    const initData = getTelegramInitData();
    if (initData) return initData;
    await sleep(100);
  }
  return getTelegramInitData();
}

async function parseResponse(response: Response) {
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : null;
    const err = data?.error || {};
    throw new ApiError(err.message || detail || 'Request failed', err.code || 'api_error', err.details || {});
  }
  if (data === null) throw new ApiError('API вернул не JSON. Проверьте, что api.intaxi.best указывает на FastAPI, а не nginx placeholder.', 'invalid_json');
  return data;
}

async function createSession(): Promise<string | null> {
  const headers = new Headers();
  headers.set('Content-Type', 'application/json');
  const initData = await waitForTelegramInitData();

  if (initData) {
    const response = await fetch(`${API_BASE_URL}/auth/telegram`, { method: 'POST', headers, body: JSON.stringify({ init_data: initData }), cache: 'no-store' });
    const data = await parseResponse(response);
    const token = typeof data?.session_token === 'string' ? data.session_token : null;
    setStoredSessionToken(token);
    return token;
  }

  if (process.env.NODE_ENV !== 'production') {
    const response = await fetch(`${API_BASE_URL}/dev/session`, { method: 'POST', headers, body: JSON.stringify({ tg_id: parseDevTgId() }), cache: 'no-store' });
    const data = await parseResponse(response);
    const token = typeof data?.session_token === 'string' ? data.session_token : null;
    setStoredSessionToken(token);
    return token;
  }

  throw new ApiError('Откройте Mini App внутри Telegram, чтобы авторизоваться.', 'telegram_auth_missing');
}

async function getSessionToken() { return getStoredSessionToken() || createSession(); }

async function request<T>(path: string, init: RequestInit = {}, authenticated = true, retryAuth = true): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  if (authenticated) {
    const token = await getSessionToken();
    headers.set('Authorization', `Bearer ${token}`);
  }
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers, cache: 'no-store' });
  if (authenticated && response.status === 401 && retryAuth) {
    setStoredSessionToken(null);
    const token = await createSession();
    const retryHeaders = new Headers(init.headers);
    if (init.body && !retryHeaders.has('Content-Type')) retryHeaders.set('Content-Type', 'application/json');
    retryHeaders.set('Authorization', `Bearer ${token}`);
    const retryResponse = await fetch(`${API_BASE_URL}${path}`, { ...init, headers: retryHeaders, cache: 'no-store' });
    return parseResponse(retryResponse) as Promise<T>;
  }
  return parseResponse(response) as Promise<T>;
}

async function requestFirst<T>(paths: string[], init: RequestInit = {}, authenticated = true): Promise<T> {
  let lastError: unknown = null;
  for (const path of paths) {
    try { return await request<T>(path, init, authenticated); }
    catch (err) { lastError = err; if (!(err instanceof ApiError) || err.message !== 'Not Found') throw err; }
  }
  throw lastError instanceof Error ? lastError : new ApiError('Request failed');
}

function countryCurrency(country?: string | null) { const map: Record<string, string> = { uz: 'UZS', kz: 'KZT', tr: 'TRY', sa: 'SAR' }; return map[(country || '').toLowerCase()] || 'USD'; }

function normalizeMe(raw: BackendUser): UserMe & { is_verified?: boolean } {
  const tgUser = getTelegramUser();
  const tgId = Number(raw?.tg_id ?? tgUser?.id ?? raw?.id ?? 0);
  return { id: Number(raw?.id ?? tgId), tg_id: tgId || null, phone: null, full_name: raw?.full_name || [tgUser?.first_name, tgUser?.last_name].filter(Boolean).join(' ') || 'Пользователь', username: raw?.username || tgUser?.username || null, language: raw?.language || tgUser?.language_code || 'ru', country_code: raw?.country_code || raw?.country || null, city_id: null, active_role: raw?.active_role || 'passenger', is_blocked: Boolean(raw?.is_blocked), profile_gender: 'unspecified', is_adult_confirmed: true, rating: Number(raw?.rating ?? 0), rating_count: Number(raw?.rating_count ?? 0), photo_url: raw?.photo_url || tgUser?.photo_url || null, is_verified: Boolean(raw?.is_verified) };
}

function normalizeCityOrder(raw: BackendCityOrder, fallback: Partial<CityOrder> = {}): CityOrder {
  const countryCode = raw?.country_code || raw?.country || fallback.country_code || 'uz';
  const price = Number(raw?.passenger_price ?? raw?.price ?? fallback.passenger_price ?? 0);
  return { id: Number(raw?.id ?? fallback.id ?? 0), mode: (fallback.mode || 'regular') as RideMode, passenger_user_id: Number(raw?.creator_tg_id ?? fallback.passenger_user_id ?? 0), country_code: countryCode, city_id: null, pickup_address: raw?.pickup_address || raw?.from_address || fallback.pickup_address || '', destination_address: raw?.destination_address || raw?.to_address || fallback.destination_address || '', seats: Number(raw?.seats ?? fallback.seats ?? 1), passenger_price: price, recommended_price: raw?.recommended_price ?? fallback.recommended_price ?? null, minimum_recommended_price: raw?.minimum_recommended_price ?? fallback.minimum_recommended_price ?? null, currency: raw?.currency || fallback.currency || countryCurrency(countryCode), estimated_distance_km: raw?.estimated_distance_km ?? fallback.estimated_distance_km ?? null, estimated_duration_min: raw?.estimated_duration_min ?? raw?.estimated_trip_min ?? fallback.estimated_duration_min ?? null, status: raw?.status || fallback.status || 'active', seen_by_drivers: Number(raw?.seen_by_drivers ?? fallback.seen_by_drivers ?? 0), accepted_trip_id: raw?.accepted_trip_id ?? raw?.active_trip_id ?? fallback.accepted_trip_id ?? null };
}

function normalizeCityTrip(raw: any): CityTrip { return { id: Number(raw?.id ?? raw?.trip_id ?? 0), mode: (raw?.mode || 'regular') as RideMode, order_id: Number(raw?.order_id ?? 0), passenger_user_id: Number(raw?.passenger_user_id ?? raw?.passenger_tg_id ?? 0), driver_user_id: Number(raw?.driver_user_id ?? raw?.driver_tg_id ?? 0), vehicle_id: raw?.vehicle_id ?? null, final_price: Number(raw?.final_price ?? raw?.price ?? 0), currency: raw?.currency || countryCurrency(raw?.country), status: raw?.status || 'accepted', pickup_address: raw?.pickup_address || raw?.from_address || '', destination_address: raw?.destination_address || raw?.to_address || '', driver_lat: raw?.driver_lat ?? null, driver_lng: raw?.driver_lng ?? null }; }

function normalizeIntercityOffer(raw: BackendIntercityOffer): IntercityOffer { const countryCode = raw?.country_code || raw?.country || 'uz'; return { kind: raw?.kind || 'route', id: Number(raw?.id ?? 0), mode: 'regular', country_code: countryCode, from_text: raw?.from_text || raw?.from_city || '', to_text: raw?.to_text || raw?.to_city || '', date: raw?.date || null, time: raw?.time || null, seats: Number(raw?.seats ?? raw?.seats_needed ?? 1), price: Number(raw?.price ?? raw?.price_offer ?? 0), currency: raw?.currency || countryCurrency(countryCode), status: raw?.status || 'active' }; }
function normalizeIntercityTrip(raw: any): IntercityTrip { return { id: Number(raw?.id ?? raw?.trip_id ?? 0), mode: raw?.mode || 'regular', source_type: raw?.source_type || raw?.trip_type || raw?.kind || 'request', source_id: Number(raw?.source_id ?? raw?.id ?? 0), passenger_user_id: Number(raw?.passenger_user_id ?? raw?.passenger_tg_id ?? 0), driver_user_id: Number(raw?.driver_user_id ?? raw?.driver_tg_id ?? 0), vehicle_id: raw?.vehicle_id ?? null, final_price: Number(raw?.final_price ?? raw?.price ?? 0), currency: raw?.currency || countryCurrency(raw?.country), status: raw?.status || 'accepted' }; }

function unwrapItems<T>(data: T[] | { items?: T[] }): T[] { return Array.isArray(data) ? data : data?.items || []; }
function unwrapItem<T>(data: T | { item?: T } | { order?: T }): T { if (data && typeof data === 'object' && 'item' in data && data.item) return data.item; if (data && typeof data === 'object' && 'order' in data && data.order) return data.order; return data as T; }

export type CreateCityOrderInput = { mode: RideMode; country_code: string; city_id?: number | null; pickup_address: string; pickup_lat?: number | null; pickup_lng?: number | null; destination_address: string; destination_lat?: number | null; destination_lng?: number | null; seats: number; passenger_price: number; comment?: string | null };
export type DonationPaymentSettingInput = Record<string, unknown>;
export type UserProfileInput = { full_name?: string; language?: string; country_code?: string | null; city_id?: number | null; profile_gender?: 'woman' | 'man' | 'unspecified'; is_adult_confirmed?: boolean };

export async function getMe(): Promise<UserMe & { is_verified?: boolean }> { return normalizeMe(await request<BackendUser>('/me')); }
export async function updateMe(input: UserProfileInput): Promise<UserMe> { const data = await request<{ user: BackendUser }>('/me/profile', { method: 'POST', body: JSON.stringify({ language: input.language, country: input.country_code, city: input.city_id ? String(input.city_id) : undefined }) }); return normalizeMe(data.user); }
export async function updateRole(activeRole: UserRole): Promise<UserMe> { const data = await request<{ user: BackendUser }>('/me/role', { method: 'POST', body: JSON.stringify({ active_role: activeRole }) }); return normalizeMe(data.user); }
export async function getDriverOnline(): Promise<DriverOnlineState> { const data = await request<any>('/driver/online'); return { is_online: Boolean(data?.is_online), is_busy: Boolean(data?.is_busy), country_code: data?.country || data?.country_code || null, city_id: null, lat: data?.lat ?? null, lng: data?.lng ?? null }; }
export async function setDriverOnline(input: { is_online: boolean; country_code?: string | null; city_id?: number | null; lat?: number | null; lng?: number | null }): Promise<DriverOnlineState> {
  const data = await request<any>('/driver/online', { method: 'POST', body: JSON.stringify({ is_online: input.is_online, country: input.country_code || undefined, country_code: input.country_code || undefined, city_id: input.city_id ?? undefined, lat: input.lat ?? undefined, lng: input.lng ?? undefined }) });
  return { is_online: Boolean(data?.is_online), is_busy: Boolean(data?.is_busy), country_code: input.country_code || data?.country || data?.country_code || null, city_id: input.city_id ?? null, lat: data?.lat ?? input.lat ?? null, lng: data?.lng ?? input.lng ?? null };
}

export type DriverPaymentMethodInput = Record<string, unknown>;
export async function listMyDriverPaymentMethods(): Promise<DriverPaymentMethod[]> { return []; }
export async function createDriverPaymentMethod(input?: DriverPaymentMethodInput): Promise<DriverPaymentMethod> { void input; return { id: Date.now(), method_type: 'manual', card_number_masked: null, card_holder_name: null, bank_name: null, is_active: true }; }

export async function createCityOrder(input: CreateCityOrderInput): Promise<CityOrder> { const data = await request<any>('/city/orders', { method: 'POST', body: JSON.stringify({ role: 'passenger', country: input.country_code, city: '', from_address: input.pickup_address, to_address: input.destination_address, seats: input.seats, price: input.passenger_price, comment: input.comment || '', from_lat: input.pickup_lat ?? null, from_lng: input.pickup_lng ?? null, to_lat: input.destination_lat ?? null, to_lng: input.destination_lng ?? null }) }); return normalizeCityOrder(unwrapItem(data), { mode: input.mode, country_code: input.country_code, pickup_address: input.pickup_address, destination_address: input.destination_address, seats: input.seats, passenger_price: input.passenger_price, currency: countryCurrency(input.country_code) }); }
export async function listMyCityOrders(): Promise<CityOrder[]> { const data = await requestFirst<any>(['/city/my-orders', '/city/orders/my']); return unwrapItems<BackendCityOrder>(data).map((item) => normalizeCityOrder(item)).filter((item) => LIVE_ORDER_STATUSES.has(item.status)); }
export async function raiseCityOrderPrice(orderId: number, price: number): Promise<CityOrder> { const data = await request<any>(`/city/orders/${orderId}/raise-price`, { method: 'POST', body: JSON.stringify({ price }) }); return normalizeCityOrder(unwrapItem(data)); }
export async function cancelCityOrder(orderId: number, reason?: string): Promise<CityOrder> { void reason; const data = await request<any>(`/city/orders/${orderId}/close`, { method: 'POST' }); return normalizeCityOrder(unwrapItem(data), { id: orderId, status: data?.status || 'closed' }); }
export async function listAvailableCityOrders(): Promise<CityOrder[]> { const data = await request<any>('/city/orders/available'); return unwrapItems<BackendCityOrder>(data).map((item) => normalizeCityOrder(item)).filter((item) => LIVE_ORDER_STATUSES.has(item.status)); }
export async function acceptCityOrder(orderId: number): Promise<CityTrip> { const data = await request<any>(`/city/orders/${orderId}/accept`, { method: 'POST' }); const item = unwrapItem<any>(data); return normalizeCityTrip({ ...item, id: item?.id ?? item?.trip_id, order_id: item?.order_id ?? orderId }); }

async function getCurrentTrip() { const data = await requestFirst<any>(['/trip/current', '/trips/current', '/current-trip']); return data?.item || data || null; }
export async function getCurrentCityTrip(): Promise<CityTrip | null> { try { const item = await getCurrentTrip(); if (!item) return null; const type = String(item.trip_type || item.source_type || 'city_trip'); const trip = type.includes('city') || item.order_id ? normalizeCityTrip(item) : null; return trip && LIVE_CITY_TRIP_STATUSES.has(trip.status) ? trip : null; } catch { return null; } }
export async function updateCityTripStatus(tripId: number, status: string): Promise<CityTrip> { const data = await requestFirst<any>([`/city/trips/${tripId}/status`, `/trips/city/${tripId}/status`], { method: 'POST', body: JSON.stringify({ status }) }); return normalizeCityTrip(unwrapItem(data)); }
export async function getDriverPaymentMethodsForTrip(tripId?: number): Promise<DriverPaymentMethod[]> { void tripId; return []; }

export async function createIntercityRequest(input: IntercityRequestInput): Promise<{ id: number; status: string }> { const data = await request<any>('/intercity/requests', { method: 'POST', body: JSON.stringify({ country: input.country_code, from_city: input.from_text, to_city: input.to_text, date: input.date || '', time: input.time || '', seats_needed: input.seats, price_offer: input.passenger_price, comment: input.comment || '' }) }); const item = unwrapItem<any>(data); return { id: Number(item?.id ?? 0), status: item?.status || 'active' }; }
export async function createIntercityRoute(input: IntercityRouteInput): Promise<{ id: number; status: string }> { const data = await request<any>('/intercity/routes', { method: 'POST', body: JSON.stringify({ country: input.country_code, from_city: input.from_text, to_city: input.to_text, date: input.date || '', time: input.time || '', seats: input.seats_available, price: input.price_per_seat, pickup_mode: input.pickup_mode, comment: input.comment || '' }) }); const item = unwrapItem<any>(data); return { id: Number(item?.id ?? 0), status: item?.status || 'active' }; }
export async function listIntercityOffers(): Promise<IntercityOffer[]> { const data = await request<any>('/intercity/offers/search'); return unwrapItems<BackendIntercityOffer>(data).map((item) => normalizeIntercityOffer(item)).filter((item) => item.status === 'active' || item.status === 'search'); }
export async function acceptIntercityOffer(kind: string, itemId: number): Promise<IntercityTrip> { const data = await request<any>(`/intercity/offers/${kind}/${itemId}/accept`, { method: 'POST' }); return normalizeIntercityTrip(unwrapItem(data)); }
export async function getCurrentIntercityTrip(): Promise<IntercityTrip | null> { try { const item = await getCurrentTrip(); if (!item) return null; const type = String(item.trip_type || item.source_type || ''); const trip = type.includes('intercity') || item.source_type ? normalizeIntercityTrip(item) : null; return trip && LIVE_INTERCITY_TRIP_STATUSES.has(trip.status) ? trip : null; } catch { return null; } }
export async function updateIntercityTripStatus(tripId: number, status: string): Promise<IntercityTrip> {
  const payload = { method: 'POST', body: JSON.stringify({ status }) };
  const data = await requestFirst<any>([`/intercity/routes/${tripId}/status`, `/intercity/requests/${tripId}/status`, `/intercity/trips/${tripId}/status`, `/trips/intercity/${tripId}/status`], payload);
  return normalizeIntercityTrip(unwrapItem(data));
}

export async function listDonationPaymentSettings(countryCode?: string, currency?: string): Promise<DonationPaymentSetting[]> { void countryCode; void currency; return []; }
export async function listAdminDonationPaymentSettings(): Promise<DonationPaymentSetting[]> { return []; }
export async function createAdminDonationPaymentSetting(input?: DonationPaymentSettingInput): Promise<DonationPaymentSetting> { void input; throw new ApiError('Not implemented in current API contract'); }
export async function updateAdminDonationPaymentSetting(id?: number, input?: Partial<DonationPaymentSettingInput>): Promise<DonationPaymentSetting> { void id; void input; throw new ApiError('Not implemented in current API contract'); }
export async function listPendingDrivers(): Promise<PendingDriverProfile[]> { return []; }
export async function approveDriverProfile(id: number): Promise<{ id: number; status: string }> { return { id, status: 'approved' }; }
export async function rejectDriverProfile(id: number, reason?: string): Promise<{ id: number; status: string }> { void reason; return { id, status: 'rejected' }; }
export async function approveWomanDriverProfile(id: number): Promise<{ id: number; woman_driver_status: string }> { return { id, woman_driver_status: 'approved' }; }
export async function listCommissionRules(): Promise<CommissionRule[]> { return []; }
export async function createCommissionRule(input: { scope_type: string; scope_id: string; commission_percent: number; free_first_rides: number }): Promise<CommissionRule> { return { id: Date.now(), scope_type: input.scope_type, scope_id: input.scope_id, commission_percent: input.commission_percent, free_first_rides: input.free_first_rides, is_active: true }; }
export async function listPendingPayments(): Promise<PendingPayment[]> { return []; }
export async function approvePayment(id: number): Promise<{ id: number; status: string }> { return { id, status: 'approved' }; }
export async function rejectPayment(id: number, reason?: string): Promise<{ id: number; status: string }> { void reason; return { id, status: 'rejected' }; }
export async function createCityCounteroffer(orderId: number, price: number): Promise<any> { return request<any>(`/city/orders/${orderId}/counteroffers`, { method: 'POST', body: JSON.stringify({ price }) }); }
