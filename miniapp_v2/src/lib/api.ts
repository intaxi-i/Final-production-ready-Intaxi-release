import { getTelegramInitData } from './telegram';
import type {
  CityOrder,
  CityTrip,
  CommissionRule,
  DonationPaymentSetting,
  DriverOnlineState,
  DriverPaymentMethod,
  PendingDriverProfile,
  PendingPayment,
  RideMode,
  UserMe,
  UserRole,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_INTAXI_API_BASE_URL || 'http://localhost:8000';
const DEV_USER_TOKEN = process.env.NEXT_PUBLIC_INTAXI_DEV_USER_TOKEN || 'dev:1';

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

async function request<T>(path: string, init: RequestInit = {}, authenticated = true): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');
  if (authenticated) {
    const initData = getTelegramInitData();
    if (initData) {
      headers.set('X-Telegram-Init-Data', initData);
    } else if (process.env.NODE_ENV !== 'production') {
      const devUserId = DEV_USER_TOKEN.replace('dev:', '');
      headers.set('Authorization', `Bearer ${DEV_USER_TOKEN}`);
      headers.set('X-Dev-User-Id', devUserId);
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    cache: 'no-store',
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const err = data?.error || {};
    throw new ApiError(err.message || 'Request failed', err.code || 'api_error', err.details || {});
  }
  return data as T;
}

export type CreateCityOrderInput = {
  mode: RideMode;
  country_code: string;
  city_id?: number | null;
  pickup_address: string;
  pickup_lat?: number | null;
  pickup_lng?: number | null;
  destination_address: string;
  destination_lat?: number | null;
  destination_lng?: number | null;
  seats: number;
  passenger_price: number;
  comment?: string | null;
};

export type DonationPaymentSettingInput = {
  method_type: string;
  title: string;
  country_code?: string | null;
  currency?: string | null;
  card_number?: string | null;
  card_holder_name?: string | null;
  bank_name?: string | null;
  digital_asset_network?: string | null;
  digital_asset_address?: string | null;
  instructions?: string | null;
  sort_order?: number;
  is_active?: boolean;
};

export type UserProfileInput = {
  full_name?: string;
  language?: string;
  country_code?: string | null;
  city_id?: number | null;
  profile_gender?: 'woman' | 'man' | 'unspecified';
  is_adult_confirmed?: boolean;
};

export async function getMe(): Promise<UserMe> {
  return request<UserMe>('/api/v2/user/me');
}

export async function updateMe(input: UserProfileInput): Promise<UserMe> {
  return request<UserMe>('/api/v2/user/me', { method: 'PATCH', body: JSON.stringify(input) });
}

export async function updateRole(activeRole: UserRole): Promise<UserMe> {
  return request<UserMe>('/api/v2/user/role', { method: 'PATCH', body: JSON.stringify({ active_role: activeRole }) });
}

export async function getDriverOnline(): Promise<DriverOnlineState> {
  return request<DriverOnlineState>('/api/v2/driver/online');
}

export async function setDriverOnline(input: { is_online: boolean; country_code?: string | null; city_id?: number | null }): Promise<DriverOnlineState> {
  return request<DriverOnlineState>('/api/v2/driver/online', { method: 'POST', body: JSON.stringify(input) });
}

export type DriverPaymentMethodInput = {
  country_code: string;
  method_type?: string;
  card_number?: string | null;
  card_holder_name?: string | null;
  bank_name?: string | null;
};

export async function listMyDriverPaymentMethods(): Promise<DriverPaymentMethod[]> {
  return request<DriverPaymentMethod[]>('/api/v2/driver/payment-methods');
}

export async function createDriverPaymentMethod(input: DriverPaymentMethodInput): Promise<DriverPaymentMethod> {
  return request<DriverPaymentMethod>('/api/v2/driver/payment-methods', { method: 'POST', body: JSON.stringify(input) });
}

export async function createCityOrder(input: CreateCityOrderInput): Promise<CityOrder> {
  const data = await request<{ order: CityOrder }>('/api/v2/city/orders', { method: 'POST', body: JSON.stringify(input) });
  return data.order;
}

export async function listMyCityOrders(): Promise<CityOrder[]> {
  return request<CityOrder[]>('/api/v2/city/orders/my');
}

export async function raiseCityOrderPrice(orderId: number, price: number): Promise<CityOrder> {
  return request<CityOrder>(`/api/v2/city/orders/${orderId}/raise-price`, { method: 'POST', body: JSON.stringify({ price }) });
}

export async function cancelCityOrder(orderId: number, reason?: string): Promise<CityOrder> {
  return request<CityOrder>(`/api/v2/city/orders/${orderId}/cancel`, { method: 'POST', body: JSON.stringify({ reason: reason || null }) });
}

export async function listAvailableCityOrders(): Promise<CityOrder[]> {
  return request<CityOrder[]>('/api/v2/city/orders/available');
}

export async function acceptCityOrder(orderId: number): Promise<CityTrip> {
  return request<CityTrip>(`/api/v2/city/orders/${orderId}/accept`, { method: 'POST' });
}

export async function getCurrentCityTrip(): Promise<CityTrip | null> {
  const data = await request<{ item: CityTrip | null }>('/api/v2/city/trips/current');
  return data.item;
}

export async function updateCityTripStatus(tripId: number, status: string): Promise<CityTrip> {
  return request<CityTrip>(`/api/v2/city/trips/${tripId}/status`, { method: 'POST', body: JSON.stringify({ status }) });
}

export async function getDriverPaymentMethodsForTrip(tripId: number): Promise<DriverPaymentMethod[]> {
  return request<DriverPaymentMethod[]>(`/api/v2/city/trips/${tripId}/driver-payment-methods`);
}

export async function listDonationPaymentSettings(countryCode?: string, currency?: string): Promise<DonationPaymentSetting[]> {
  const params = new URLSearchParams();
  if (countryCode) params.set('country_code', countryCode);
  if (currency) params.set('currency', currency);
  const query = params.toString();
  return request<DonationPaymentSetting[]>(`/api/v2/public/donation-payment-settings${query ? `?${query}` : ''}`, {}, false);
}

export async function listAdminDonationPaymentSettings(): Promise<DonationPaymentSetting[]> {
  return request<DonationPaymentSetting[]>('/api/v2/admin/donation-payment-settings');
}

export async function createAdminDonationPaymentSetting(input: DonationPaymentSettingInput): Promise<DonationPaymentSetting> {
  return request<DonationPaymentSetting>('/api/v2/admin/donation-payment-settings', { method: 'POST', body: JSON.stringify(input) });
}

export async function updateAdminDonationPaymentSetting(id: number, input: Partial<DonationPaymentSettingInput>): Promise<DonationPaymentSetting> {
  return request<DonationPaymentSetting>(`/api/v2/admin/donation-payment-settings/${id}`, { method: 'PATCH', body: JSON.stringify(input) });
}

export async function listPendingDrivers(): Promise<PendingDriverProfile[]> {
  return request<PendingDriverProfile[]>('/api/v2/admin/drivers/pending');
}

export async function approveDriverProfile(id: number): Promise<{ id: number; status: string }> {
  return request<{ id: number; status: string }>(`/api/v2/admin/drivers/${id}/approve`, { method: 'POST' });
}

export async function rejectDriverProfile(id: number, reason?: string): Promise<{ id: number; status: string }> {
  const query = reason ? `?reason=${encodeURIComponent(reason)}` : '';
  return request<{ id: number; status: string }>(`/api/v2/admin/drivers/${id}/reject${query}`, { method: 'POST' });
}

export async function approveWomanDriverProfile(id: number): Promise<{ id: number; woman_driver_status: string }> {
  return request<{ id: number; woman_driver_status: string }>(`/api/v2/admin/drivers/${id}/approve-woman-mode`, { method: 'POST' });
}

export async function listCommissionRules(): Promise<CommissionRule[]> {
  return request<CommissionRule[]>('/api/v2/admin/commission-rules');
}

export async function createCommissionRule(input: { scope_type: string; scope_id: string; commission_percent: number; free_first_rides: number }): Promise<CommissionRule> {
  const params = new URLSearchParams({
    scope_type: input.scope_type,
    scope_id: input.scope_id,
    commission_percent: String(input.commission_percent),
    free_first_rides: String(input.free_first_rides),
  });
  return request<CommissionRule>(`/api/v2/admin/commission-rules?${params.toString()}`, { method: 'POST' });
}

export async function listPendingPayments(): Promise<PendingPayment[]> {
  return request<PendingPayment[]>('/api/v2/admin/payments/pending');
}

export async function approvePayment(id: number): Promise<{ id: number; status: string }> {
  return request<{ id: number; status: string }>(`/api/v2/admin/payments/${id}/approve`, { method: 'POST' });
}

export async function rejectPayment(id: number, reason?: string): Promise<{ id: number; status: string }> {
  const query = reason ? `?reason=${encodeURIComponent(reason)}` : '';
  return request<{ id: number; status: string }>(`/api/v2/admin/payments/${id}/reject${query}`, { method: 'POST' });
}
