import { ApiError, getMe } from './api';
import type { DriverProfile, SupportTicket, Topup, Vehicle, Wallet } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_INTAXI_API_BASE_URL || 'https://api.intaxi.best';
const SESSION_STORAGE_KEY = 'intaxi_api_session_token';

async function parseResponse(response: Response) {
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : null;
    const err = data?.error || {};
    throw new ApiError(err.message || detail || 'Request failed', err.code || 'api_error', err.details || {});
  }
  if (data === null) throw new ApiError('API вернул не JSON', 'invalid_json');
  return data;
}

async function authenticatedRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  await getMe();
  const token = typeof window !== 'undefined' ? window.sessionStorage.getItem(SESSION_STORAGE_KEY) : null;
  const headers = new Headers(init.headers);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers, cache: 'no-store' });
  return parseResponse(response) as Promise<T>;
}

export type DriverProfileInput = {
  country_code: string;
  city_id?: number | null;
  license_number?: string | null;
  request_woman_mode?: boolean;
};

export type VehicleInput = {
  country_code: string;
  brand: string;
  model: string;
  year?: number | null;
  color?: string | null;
  plate: string;
  capacity: number;
  vehicle_class?: string;
};

type BackendMe = {
  id?: number | null;
  tg_id?: number | null;
  country?: string | null;
  city?: string | null;
  is_verified?: boolean | null;
  vehicle?: {
    brand?: string | null;
    model?: string | null;
    plate?: string | null;
    color?: string | null;
    capacity?: string | number | null;
    vehicle_class?: string | null;
  } | null;
};

function driverStatus(me: BackendMe) {
  return me.is_verified ? 'approved' : 'pending';
}

function toDriverProfile(me: BackendMe): DriverProfile | null {
  if (!me.is_verified && !me.vehicle) return null;
  const id = Number(me.id ?? me.tg_id ?? 0);
  return {
    id,
    user_id: id,
    status: driverStatus(me),
    country_code: me.country || 'uz',
    city_id: null,
    license_number: null,
    is_woman_driver_verified: false,
    woman_driver_status: 'unknown',
    rejection_reason: null,
  };
}

function toVehicle(me: BackendMe): Vehicle | null {
  if (!me.vehicle) return null;
  const id = Number(me.id ?? me.tg_id ?? 0);
  return {
    id,
    driver_user_id: id,
    country_code: me.country || 'uz',
    brand: me.vehicle.brand || '',
    model: me.vehicle.model || '',
    year: null,
    color: me.vehicle.color || null,
    plate: me.vehicle.plate || '',
    capacity: Number(me.vehicle.capacity || 4),
    vehicle_class: me.vehicle.vehicle_class || 'economy',
    status: me.is_verified ? 'approved' : 'pending',
    rejection_reason: null,
  };
}

export const getDriverProfile = async () => {
  const me = await authenticatedRequest<BackendMe>('/me');
  return toDriverProfile(me);
};

export const submitDriverProfile = async (input: DriverProfileInput) => {
  await authenticatedRequest('/me/profile', {
    method: 'POST',
    body: JSON.stringify({ country: input.country_code, city: input.city_id ? String(input.city_id) : '' }),
  });
  const me = await authenticatedRequest<BackendMe>('/me');
  return toDriverProfile({ ...me, vehicle: me.vehicle || {} }) as DriverProfile;
};

export const listVehicles = async () => {
  const me = await authenticatedRequest<BackendMe>('/me');
  const vehicle = toVehicle(me);
  return vehicle ? [vehicle] : [];
};

export const submitVehicle = async (input: VehicleInput) => {
  const data = await authenticatedRequest<{ user?: BackendMe }>('/me/vehicle', {
    method: 'POST',
    body: JSON.stringify({
      brand: input.brand,
      model: input.model,
      plate: input.plate,
      color: input.color || '',
      capacity: String(input.capacity || 4),
      vehicle_class: input.vehicle_class || 'economy',
    }),
  });
  const vehicle = toVehicle(data.user || { vehicle: input, country: input.country_code, is_verified: false });
  if (!vehicle) throw new ApiError('Не удалось сохранить автомобиль');
  return vehicle;
};

export const getWallet = async () => {
  const data = await authenticatedRequest<any>('/wallet');
  return {
    user_id: 0,
    balance: Number(data?.balance || 0),
    hold_balance: Number(data?.commission_due || 0),
    currency: null,
  } as Wallet;
};

export const listTopups = async () => {
  const data = await authenticatedRequest<{ items?: any[] }>('/wallet/topup/history');
  return (data.items || []).map((item) => ({
    id: Number(item.id),
    driver_user_id: Number(item.driver_tg_id || 0),
    amount: Number(item.amount || 0),
    currency: 'USD',
    method: item.card_country || 'manual',
    receipt_file_id: item.receipt_file_id || null,
    status: item.status || 'pending',
    rejection_reason: null,
  })) as Topup[];
};

export const createTopup = async (input: { amount: number; currency: string; method: string; receipt_file_id?: string | null }) => {
  const item = await authenticatedRequest<any>('/wallet/topup', {
    method: 'POST',
    body: JSON.stringify({ amount: input.amount, card_country: input.currency || input.method, receipt_file_id: input.receipt_file_id || null }),
  });
  return {
    id: Number(item.id),
    driver_user_id: Number(item.driver_tg_id || 0),
    amount: Number(item.amount || 0),
    currency: input.currency,
    method: item.card_country || input.method,
    receipt_file_id: item.receipt_file_id || null,
    status: item.status || 'pending',
    rejection_reason: null,
  } as Topup;
};

export const createSupportTicket = async (input: { ticket_type?: string; priority?: string; related_type?: string | null; related_id?: number | null; subject?: string | null; message: string }) => ({
  id: Date.now(),
  created_by_user_id: 0,
  assigned_admin_id: null,
  related_type: input.related_type || null,
  related_id: input.related_id || null,
  ticket_type: input.ticket_type || 'support',
  priority: input.priority || 'normal',
  status: 'new',
  subject: input.subject || null,
  message: input.message,
  admin_notes: null,
}) as SupportTicket;

export const listMySupportTickets = async () => [] as SupportTicket[];
