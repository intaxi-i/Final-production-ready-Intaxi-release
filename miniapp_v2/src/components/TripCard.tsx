import { Banknote, Clock3, MapPin, Navigation } from 'lucide-react';
import type { CityTrip } from '@/lib/types';

type Props = {
  trip: CityTrip;
  onStatus?: (status: string) => void;
  disabled?: boolean;
  canControl?: boolean;
};

const NEXT_STATUSES: Record<string, string[]> = {
  accepted: ['driver_on_way', 'driver_arrived', 'cancelled'],
  driver_on_way: ['driver_arrived', 'cancelled'],
  driver_arrived: ['in_progress', 'cancelled'],
  in_progress: ['completed', 'cancelled'],
};

const ACTION_LABELS: Record<string, string> = {
  driver_on_way: 'Выехал к пассажиру',
  driver_arrived: 'Я на месте',
  in_progress: 'Начать поездку',
  completed: 'Завершить поездку',
  cancelled: 'Отменить поездку',
};

const STATUS_LABELS: Record<string, string> = {
  accepted: 'Принято',
  driver_on_way: 'Водитель едет',
  driver_arrived: 'Водитель прибыл',
  in_progress: 'В пути',
  completed: 'Завершено',
  cancelled: 'Отменено',
};

const MODE_LABELS: Record<string, string> = {
  regular: 'Обычный режим',
  women: 'Женский режим',
};

function statusLabel(value?: string | null) {
  return value ? STATUS_LABELS[value] || 'Неизвестный статус' : 'Неизвестный статус';
}

function modeLabel(value?: string | null) {
  return value ? MODE_LABELS[value] || 'Неизвестный режим' : 'Неизвестный режим';
}

function actionLabel(value?: string | null) {
  return value ? ACTION_LABELS[value] || 'Неизвестное действие' : 'Неизвестное действие';
}

function formatMoney(value: number, currency: string) {
  return `${Math.round(value).toLocaleString('ru-RU')} ${currency}`;
}

export function TripCard({ trip, onStatus, disabled, canControl = true }: Props) {
  const next = canControl ? NEXT_STATUSES[trip.status] || [] : [];

  return (
    <article className="order-card">
      <div className="order-card-inner stack">
        <div className="order-topline">
          <span className="order-badge">Город · №{trip.id}</span>
          <span className="order-badge bg-brand-yellow text-brand-dark">{statusLabel(trip.status)}</span>
        </div>

        <div className="route-panel">
          <div className="route-line" />
          <div className="route-point">
            <div className="route-dot" />
            <div>
              <div className="route-kicker">Откуда</div>
              <div className="route-address">{trip.pickup_address}</div>
            </div>
          </div>
          <div className="route-point">
            <div className="route-dot end" />
            <div>
              <div className="route-kicker">Куда</div>
              <div className="route-address muted">{trip.destination_address}</div>
            </div>
          </div>
        </div>

        <section className="metric-grid">
          <div className="metric-card">
            <div className="metric-label">Цена</div>
            <div className="metric-value">{formatMoney(trip.final_price, trip.currency)}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Режим</div>
            <div className="metric-value">{modeLabel(trip.mode)}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Водитель</div>
            <div className="metric-value">#{trip.driver_user_id}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Пассажир</div>
            <div className="metric-value">#{trip.passenger_user_id}</div>
          </div>
        </section>

        <div className="row rounded-3xl bg-slate-50 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-brand-yellow"><Navigation size={20} /></div>
            <div>
              <strong>{statusLabel(trip.status)}</strong>
              <p className="subtitle mt-1">Следуйте статусам поездки по порядку.</p>
            </div>
          </div>
          <Clock3 className="text-slate-300" />
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
                {actionLabel(status)}
              </button>
            ))}
          </div>
        ) : null}
      </div>
    </article>
  );
}
