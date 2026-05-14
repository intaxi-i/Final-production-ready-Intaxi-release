import { Banknote, Clock3, MapPin, Navigation } from 'lucide-react';
import type { CityTrip } from '@/lib/types';
import { t } from '@/lib/i18n';

type ViewerRole = 'driver' | 'passenger' | 'unknown';

type Props = {
  trip: CityTrip;
  onStatus?: (status: string) => void;
  disabled?: boolean;
  canControl?: boolean;
  viewerRole?: ViewerRole;
  lang?: string | null;
};

const NEXT_DRIVER_STATUSES: Record<string, string[]> = {
  accepted: ['driver_on_way', 'driver_arrived', 'cancelled'],
  driver_on_way: ['driver_arrived', 'cancelled'],
  driver_arrived: ['in_progress', 'cancelled'],
  in_progress: ['completed', 'cancelled'],
};

function statusLabel(lang: string | undefined | null, value?: string | null, viewerRole: ViewerRole = 'unknown') {
  if (value === 'accepted') return t(lang, viewerRole === 'driver' ? 'driverFoundDriver' : 'driverFoundPassenger');
  if (value === 'driver_on_way') return t(lang, viewerRole === 'driver' ? 'driverOnWayDriver' : 'driverOnWayPassenger');
  if (value === 'driver_arrived') return t(lang, viewerRole === 'driver' ? 'driverArrivedDriver' : 'driverArrivedPassenger');
  if (value === 'in_progress') return t(lang, viewerRole === 'driver' ? 'tripInProgressDriver' : 'tripInProgressPassenger');
  if (value === 'completed') return t(lang, 'completedStatus');
  if (value === 'cancelled') return t(lang, 'cancelledStatus');
  return t(lang, 'unknownStatus');
}

function modeLabel(lang: string | undefined | null, value?: string | null) {
  if (value === 'regular') return t(lang, 'regularMode');
  if (value === 'women') return t(lang, 'womenMode');
  return t(lang, 'unknownMode');
}

function actionLabel(lang: string | undefined | null, value?: string | null) {
  if (value === 'driver_on_way') return t(lang, 'driverOnWayDriver');
  if (value === 'driver_arrived') return t(lang, 'driverArrivedDriver');
  if (value === 'in_progress') return t(lang, 'tripInProgressDriver');
  if (value === 'completed') return t(lang, 'completedStatus');
  if (value === 'cancelled') return t(lang, 'cancelledStatus');
  return t(lang, 'unknownStatus');
}

function formatMoney(value: number, currency: string) {
  return `${Math.round(value).toLocaleString('ru-RU')} ${currency}`;
}

export function TripCard({ trip, onStatus, disabled, canControl = true, viewerRole = 'unknown', lang }: Props) {
  const canDriverControl = canControl && viewerRole === 'driver';
  const next = canDriverControl ? NEXT_DRIVER_STATUSES[trip.status] || [] : [];

  return (
    <article className="order-card min-w-0 overflow-hidden">
      <div className="order-card-inner stack min-w-0">
        <div className="order-topline min-w-0 gap-2">
          <span className="order-badge min-w-0 max-w-full truncate">{t(lang, 'city')} · №{trip.id}</span>
          <span className="order-badge shrink-0 bg-brand-yellow text-brand-dark">{statusLabel(lang, trip.status, viewerRole)}</span>
        </div>

        <div className="route-panel min-w-0 overflow-hidden">
          <div className="route-line" />
          <div className="route-point min-w-0">
            <div className="route-dot shrink-0" />
            <div className="min-w-0">
              <div className="route-kicker">{t(lang, 'fromWhere')}</div>
              <div className="route-address break-words">{trip.pickup_address || t(lang, 'pickupAddressMissing')}</div>
            </div>
          </div>
          <div className="route-point min-w-0">
            <div className="route-dot end shrink-0" />
            <div className="min-w-0">
              <div className="route-kicker">{t(lang, 'toWhere')}</div>
              <div className="route-address muted break-words">{trip.destination_address || t(lang, 'destinationAddressMissing')}</div>
            </div>
          </div>
        </div>

        <section className="metric-grid">
          <div className="metric-card min-w-0 overflow-hidden"><div className="metric-label">{t(lang, 'price')}</div><div className="metric-value break-words">{formatMoney(trip.final_price, trip.currency)}</div></div>
          <div className="metric-card min-w-0 overflow-hidden"><div className="metric-label">{t(lang, 'status')}</div><div className="metric-value break-words">{modeLabel(lang, trip.mode)}</div></div>
          <div className="metric-card min-w-0 overflow-hidden"><div className="metric-label">{t(lang, 'driver')}</div><div className="metric-value break-words">#{trip.driver_user_id}</div></div>
          <div className="metric-card min-w-0 overflow-hidden"><div className="metric-label">{t(lang, 'passengerMode')}</div><div className="metric-value break-words">#{trip.passenger_user_id}</div></div>
        </section>

        <div className="row rounded-3xl bg-slate-50 p-4">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white text-brand-yellow"><Navigation size={20} /></div>
            <div className="min-w-0">
              <strong className="break-words">{statusLabel(lang, trip.status, viewerRole)}</strong>
              <p className="subtitle mt-1 break-words">{viewerRole === 'driver' ? t(lang, 'driverCheckHint') : t(lang, 'createdOrderHint')}</p>
            </div>
          </div>
          <Clock3 className="shrink-0 text-slate-300" />
        </div>

        {onStatus && next.length > 0 ? (
          <div className="actions">
            {next.map((status) => (
              <button
                className={`button ${status === 'cancelled' ? 'danger' : status === 'completed' || status === 'in_progress' ? 'primary' : 'secondary'}`}
                key={status}
                type="button"
                disabled={disabled}
                onClick={() => onStatus(status)}
              >
                {status === 'completed' ? <Banknote size={18} /> : <MapPin size={18} />}
                {actionLabel(lang, status)}
              </button>
            ))}
          </div>
        ) : null}
      </div>
    </article>
  );
}
