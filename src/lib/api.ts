export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "https://api.intaxi.best";

type RequestOptions = RequestInit & { token?: string };

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { token, headers, ...rest } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(headers || {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    let message = "Request failed";
    try {
      const data = await response.json();
      message = data?.detail || JSON.stringify(data);
    } catch {
      try {
        message = await response.text();
      } catch {
        message = "Request failed";
      }
    }
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export type SessionResponse = { session_token: string; user: { tg_id: number; full_name: string; username?: string | null; language?: string | null } };
export type VehicleInfo = { brand?: string | null; model?: string | null; plate?: string | null; color?: string | null; capacity?: string | null; vehicle_class?: string | null };
export type MeResponse = { tg_id: number; full_name: string; username?: string | null; language?: string | null; country?: string | null; city?: string | null; balance?: number; commission_due?: number; free_rides_left?: number; active_role?: string | null; is_verified?: boolean; vehicle?: VehicleInfo | null };
export type WalletResponse = { balance: number; commission_due: number; free_rides_left: number; commission_rate?: number };
export type WalletTopupRequest = { amount: number; card_country?: string | null; receipt_file_id?: string | null };
export type WalletTopupItem = { id: number; amount: number; status: string; card_country?: string | null; admin_card_number?: string | null; receipt_file_id?: string | null; reviewed_by?: number | null; created_at?: string | null; reviewed_at?: string | null; driver_tg_id?: number | null; driver_balance?: number | null };
export type WalletTopupHistoryResponse = { items: WalletTopupItem[] };
export type AdminPendingPaymentsResponse = { items: WalletTopupItem[] };
export type AdminPaymentReviewResult = { id: number; status: string; driver_tg_id?: number | null; amount?: number; reviewed_by?: number | null; reviewed_at?: string | null; driver_balance?: number | null };
export type TariffItem = { country: string; currency: string; price_per_km: number };
export type TariffListResponse = { items: TariffItem[] };
export type DriverOnlineState = { is_online: boolean; lat?: number | null; lng?: number | null; updated_at?: string | null };
export type IntercityMyRoute = { id: number; country?: string; from_city: string; to_city: string; date: string; time: string; seats: number; price: number; comment?: string; status?: string; created_at?: string; pickup_mode?: "driver_location" | "driver_pickup" | "ask_driver" };
export type IntercityMyRequest = { id: number; country?: string; from_city: string; to_city: string; date: string; time: string; seats_needed: number; price_offer: number; comment?: string; status?: string; created_at?: string };
export type IntercityOffer = { id: number; kind: "route" | "request"; creator_tg_id?: number; creator_name?: string | null; creator_rating?: number | null; country?: string | null; from_city: string; to_city: string; date: string; time: string; seats: number; price: number; comment?: string | null; pickup_mode?: "driver_location" | "driver_pickup" | "ask_driver" | null; status?: string | null; created_at?: string | null; is_mine?: boolean | null; active_trip_id?: number | null; accepted_by_tg_id?: number | null; can_accept?: boolean | null; map_provider?: string | null; map_embed_url?: string | null; map_action_url?: string | null };
export type CityOrder = { id: number; creator_tg_id?: number; creator_name?: string; creator_rating?: number; role: "driver" | "passenger"; country?: string; city: string; from_address: string; to_address?: string; seats: number; price: number; recommended_price?: number; seen_by_drivers?: number; can_raise_price_after?: number; estimated_distance_km?: number; estimated_trip_min?: number; driver_distance_km?: number; driver_eta_min?: number; comment?: string; status?: string; created_at?: string; is_mine?: boolean; active_trip_id?: number | null; vehicle?: VehicleInfo | null; currency?: string | null; tariff_hint?: string | null };
export type CityTrip = { id: number; order_id: number; status: string; price: number; country?: string; city?: string; from_address?: string; to_address?: string; seats?: number; comment?: string; passenger_tg_id: number; driver_tg_id: number; passenger_name?: string; passenger_username?: string | null; driver_name?: string; driver_username?: string | null; driver_rating?: number; vehicle?: VehicleInfo | null; trip_type?: string | null; pickup_lat?: number | null; pickup_lng?: number | null; destination_lat?: number | null; destination_lng?: number | null; driver_lat?: number | null; driver_lng?: number | null; passenger_lat?: number | null; passenger_lng?: number | null; map_provider?: string | null; map_embed_url?: string | null; map_action_url?: string | null; eta_min?: number | null; pickup_mode?: string | null; date?: string | null; time?: string | null; from_city?: string | null; to_city?: string | null };
export type ChatMessage = { id: number; sender_tg_id: number; text: string; created_at: string };
export type HistoryResponse = { city_orders: CityOrder[]; city_trips: CityTrip[]; intercity_routes: IntercityMyRoute[]; intercity_requests: IntercityMyRequest[] };

export const api = {
  authTelegram(payload: { init_data: string }) { return request<SessionResponse>("/auth/telegram", { method: "POST", body: JSON.stringify(payload) }); },
  devSession() { return request<SessionResponse>("/dev/session", { method: "POST" }); },
  me(token: string) { return request<MeResponse>("/me", { token }); },
  wallet(token: string) { return request<WalletResponse>("/wallet", { token }); },
  walletTopup(token: string, payload: WalletTopupRequest) { return request<WalletTopupItem>("/wallet/topup", { method: "POST", token, body: JSON.stringify(payload) }); },
  walletTopupHistory(token: string) { return request<WalletTopupHistoryResponse>("/wallet/topup/history", { token }); },
  adminPendingPayments(token: string) { return request<AdminPendingPaymentsResponse>("/admin/payments/pending", { token }); },
  adminApprovePayment(token: string, paymentId: number, amount?: number) { return request<AdminPaymentReviewResult>(`/admin/payments/${paymentId}/approve`, { method: "POST", token, body: JSON.stringify(amount === undefined ? {} : { amount }) }); },
  adminRejectPayment(token: string, paymentId: number) { return request<AdminPaymentReviewResult>(`/admin/payments/${paymentId}/reject`, { method: "POST", token }); },
  tariffs(token: string) { return request<TariffListResponse>("/city/tariffs", { token }); },
  adminTariffs(token: string) { return request<TariffListResponse>("/admin/tariffs", { token }); },
  updateTariff(token: string, payload: { country: string; price_per_km: number; currency?: string }) { return request<TariffItem>("/admin/tariffs", { method: "POST", token, body: JSON.stringify(payload) }); },
  driverOnline(token: string) { return request<DriverOnlineState>("/driver/online", { token }); },
  setDriverOnline(token: string, is_online: boolean) { return request<DriverOnlineState>("/driver/online", { method: "POST", token, body: JSON.stringify({ is_online }) }); },
  updateProfile(token: string, payload: { language?: string; country?: string; city?: string }) { return request<{ user: MeResponse }>("/me/profile", { method: "POST", token, body: JSON.stringify(payload) }); },
  updateRole(token: string, active_role: string) { return request<{ user: MeResponse }>("/me/role", { method: "POST", token, body: JSON.stringify({ active_role }) }); },
  updateVehicle(token: string, payload: VehicleInfo) { return request<{ user: MeResponse }>("/me/vehicle", { method: "POST", token, body: JSON.stringify(payload) }); },
  intercityOffers(token: string) { return request<{ items: IntercityOffer[] }>("/intercity/offers", { token }); },
  intercityOfferDetail(token: string, kind: string, id: number) { return request<{ item: IntercityOffer }>(`/intercity/offers/${kind}/${id}`, { token }); },
  acceptIntercityOffer(token: string, kind: string, id: number) { return request<{ trip_id: number; trip_type: string; status: string }>(`/intercity/offers/${kind}/${id}/accept`, { method: "POST", token }); },
  grantIntercityChatAccess(token: string, kind: string, id: number) { return request<{ status: string; trip_type: string; trip_id: number }>(`/intercity/chat-access/${kind}/${id}`, { method: "POST", token }); },
  createIntercityRoute(token: string, payload: { country: string; from_city: string; to_city: string; date: string; time: string; seats: number; price: number; comment: string; pickup_mode?: "driver_location" | "driver_pickup" | "ask_driver"; }) { return request<{ id: number; status: string }>("/intercity/routes", { method: "POST", token, body: JSON.stringify(payload) }); },
  createIntercityRequest(token: string, payload: { country: string; from_city: string; to_city: string; date: string; time: string; seats_needed: number; price_offer: number; comment: string; }) { return request<{ id: number; status: string }>("/intercity/requests", { method: "POST", token, body: JSON.stringify(payload) }); },
  myIntercityRoutes(token: string) { return request<{ items: IntercityMyRoute[] }>("/intercity/my-routes", { token }); },
  myIntercityRequests(token: string) { return request<{ items: IntercityMyRequest[] }>("/intercity/my-requests", { token }); },
  cityOffers(token: string, kind: "all" | "driver" | "passenger" = "all") { return request<{ items: CityOrder[] }>(`/city/offers?kind=${kind}`, { token }); },
  cityOfferDetail(token: string, id: number) { return request<{ item: CityOrder }>(`/city/offers/${id}`, { token }); },
  createCityOrder(token: string, payload: { role: "driver" | "passenger"; country: string; city: string; from_address: string; to_address: string; seats: number; price?: number | null; comment: string; recommended_price?: number; from_lat?: number | null; from_lng?: number | null; to_lat?: number | null; to_lng?: number | null; }) { return request<{ id: number; status: string; recommended_price: number | null; seen_by_drivers: number; currency?: string | null; tariff_hint?: string | null }>("/city/orders", { method: "POST", token, body: JSON.stringify(payload) }); },
  myCityOrders(token: string) { return request<{ items: CityOrder[] }>("/city/my-orders", { token }); },
  closeCityOrder(token: string, id: number) { return request<{ id: number; status: string }>(`/city/orders/${id}/close`, { method: "POST", token }); },
  raiseCityOrderPrice(token: string, id: number, price: number) { return request<{ id: number; status: string; price: number }>(`/city/orders/${id}/raise-price`, { method: "POST", token, body: JSON.stringify({ price }) }); },
  acceptCityOffer(token: string, id: number) { return request<{ trip_id: number; status: string }>(`/city/offers/${id}/accept`, { method: "POST", token }); },
  cityTripDetail(token: string, id: number) { return request<{ item: CityTrip }>(`/city/trips/${id}`, { token }); },
  updateCityTripStatus(token: string, id: number, status: string) { return request<{ item: CityTrip }>(`/city/trips/${id}/status`, { method: "POST", token, body: JSON.stringify({ status }) }); },
  currentTrip(token: string) { return request<{ item: CityTrip | Record<string, unknown> | null }>("/trip/current", { token }); },
  chatMessages(token: string, tripId: number, tripType = "generic") { return request<{ items: ChatMessage[] }>(`/chat/${tripId}/messages?trip_type=${encodeURIComponent(tripType)}`, { token }); },
  sendChatMessage(token: string, tripId: number, text: string, tripType = "generic") { return request<{ id: number; status: string }>(`/chat/${tripId}/messages?trip_type=${encodeURIComponent(tripType)}`, { method: "POST", token, body: JSON.stringify({ text }) }); },
  updateDriverLocation(token: string, payload: { trip_id?: number; lat: number; lng: number }) { return request<{ status: string; updated_at: string }>("/driver/location", { method: "POST", token, body: JSON.stringify(payload) }); },
  historyAll(token: string) { return request<HistoryResponse>("/history/all", { token }); },
  updateIntercityRouteStatus(token: string, id: number, status: string) { return request<{ id: number; status: string }>(`/intercity/routes/${id}/status`, { method: "POST", token, body: JSON.stringify({ status }) }); },
  updateIntercityRequestStatus(token: string, id: number, status: string) { return request<{ id: number; status: string }>(`/intercity/requests/${id}/status`, { method: "POST", token, body: JSON.stringify({ status }) }); },
};
