import { ApiError } from './api';
import type { DriverProfile, SupportTicket, Topup, Vehicle, Wallet } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_INTAXI_API_BASE_URL || 'http://localhost:8000';
const DEV_USER_TOKEN = process.env.NEXT_PUBLIC_INTAXI_DEV_USER_TOKEN || 'dev:1';

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');
  headers.set('Authorization', `Bearer ${DEV_USER_TOKEN}`);
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers, cache: 'no-store' });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const err = data?.error || {};
    throw new ApiError(err.message || 'Request failed', err.code || 'api_error', err.details || {});
  }
  return data as T;
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

export const getDriverProfile = () => request<DriverProfile | null>('/api/v2/driver/profile');
export const submitDriverProfile = (input: DriverProfileInput) => request<DriverProfile>('/api/v2/driver/profile', { method: 'POST', body: JSON.stringify(input) });
export const listVehicles = () => request<Vehicle[]>('/api/v2/driver/vehicles');
export const submitVehicle = (input: VehicleInput) => request<Vehicle>('/api/v2/driver/vehicles', { method: 'POST', body: JSON.stringify(input) });

export const getWallet = () => request<Wallet>('/api/v2/wallet');
export const listTopups = () => request<Topup[]>('/api/v2/wallet/topups');
export const createTopup = (input: { amount: number; currency: string; method: string; receipt_file_id?: string | null }) => request<Topup>('/api/v2/wallet/topups', { method: 'POST', body: JSON.stringify(input) });

export const createSupportTicket = (input: { ticket_type?: string; priority?: string; related_type?: string | null; related_id?: number | null; subject?: string | null; message: string }) => request<SupportTicket>('/api/v2/support/tickets', { method: 'POST', body: JSON.stringify(input) });
export const listMySupportTickets = () => request<SupportTicket[]>('/api/v2/support/tickets/my');
