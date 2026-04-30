export type RideMode = 'regular' | 'women';
export type UserRole = 'passenger' | 'driver' | 'admin';
export type ProfileGender = 'woman' | 'man' | 'unspecified';

export type UserMe = {
  id: number;
  tg_id: number | null;
  phone: string | null;
  full_name: string;
  username: string | null;
  language: string;
  country_code: string | null;
  city_id: number | null;
  active_role: UserRole | null;
  is_blocked: boolean;
  profile_gender: ProfileGender;
  is_adult_confirmed: boolean;
  rating: number;
  rating_count: number;
};

export type DriverOnlineState = {
  is_online: boolean;
  is_busy: boolean;
  country_code: string | null;
  city_id: number | null;
  lat: number | null;
  lng: number | null;
};

export type PendingDriverProfile = {
  id: number;
  user_id: number;
  country_code: string;
  city_id: number | null;
  woman_driver_status: string;
};

export type PendingPayment = {
  id: number;
  driver_user_id: number;
  amount: number;
  currency: string;
  status: string;
};

export type CommissionRule = {
  id: number;
  scope_type: string;
  scope_id: string;
  commission_percent: number;
  free_first_rides: number;
  is_active: boolean;
};

export type CityOrder = {
  id: number;
  mode: RideMode;
  passenger_user_id: number;
  country_code: string;
  city_id: number | null;
  pickup_address: string;
  destination_address: string;
  seats: number;
  passenger_price: number;
  recommended_price: number | null;
  minimum_recommended_price: number | null;
  currency: string;
  estimated_distance_km: number | null;
  estimated_duration_min: number | null;
  status: string;
  seen_by_drivers: number;
  accepted_trip_id: number | null;
};

export type CityTrip = {
  id: number;
  mode: RideMode;
  order_id: number;
  passenger_user_id: number;
  driver_user_id: number;
  vehicle_id: number | null;
  final_price: number;
  currency: string;
  status: string;
  pickup_address: string;
  destination_address: string;
  driver_lat: number | null;
  driver_lng: number | null;
};

export type DriverPaymentMethod = {
  id: number;
  method_type: string;
  card_number_masked: string | null;
  card_holder_name: string | null;
  bank_name: string | null;
  is_active: boolean;
};

export type DonationPaymentSetting = {
  id: number;
  method_type: string;
  title: string;
  country_code: string | null;
  currency: string | null;
  card_number_masked: string | null;
  card_holder_name: string | null;
  bank_name: string | null;
  digital_asset_network: string | null;
  digital_asset_address_preview: string | null;
  instructions: string | null;
  extra_json: Record<string, unknown> | null;
  sort_order: number;
  is_active: boolean;
};

export type ApiErrorPayload = {
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, unknown>;
  };
};
