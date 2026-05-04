import type { CityTrip } from '@/lib/types';

type Props = {
  trip: CityTrip;
  onStatus?: (status: string) => void;
  disabled?: boolean;
};

const NEXT_STATUSES: Record<string, string[]> = {
  accepted: ['driver_on_way', 'driver_arrived', 'cancelled'],
  driver_on_way: ['driver_arrived', 'cancelled'],
  driver_arrived: ['in_progress', 'cancelled'],
  in_progress: ['completed', 'cancelled'],
};

const LABELS: Record<string, string> = {
  driver_on_way: 'Выехал',
  driver_arrived: 'Прибыл',
  in_progress: 'Начать поездку',
  completed: 'Завершить',
  cancelled: 'Отменить',
};

export function TripCard({ trip, onStatus, disabled }: Props) {
  const next = NEXT_STATUSES[trip.status] || [];

  return (
    <article className="card stack">
      <div className="row">
        <span className="badge">Trip #{trip.id} · {trip.mode}</span>
        <span className="badge">{trip.status}</span>
      </div>
      <div>
        <h3 className="title" style={{ fontSize: 20 }}>Текущая поездка</h3>
        <p className="subtitle">A: {trip.pickup_address}</p>
        <p className="subtitle">B: {trip.destination_address}</p>
      </div>
      <div className="card-soft">
        <strong>{trip.final_price} {trip.currency}</strong>
        <p className="subtitle">Итоговая цена</p>
      </div>
      {onStatus ? (
        <div className="actions">
          {next.map((status) => (
            <button
              className={`button ${status === 'cancelled' ? 'danger' : ''}`}
              key={status}
              type="button"
              disabled={disabled}
              onClick={() => onStatus(status)}
            >
              {LABELS[status] || status}
            </button>
          ))}
        </div>
      ) : null}
    </article>
  );
}
