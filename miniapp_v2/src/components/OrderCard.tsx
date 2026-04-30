import type { CityOrder } from '@/lib/types';

type Props = {
  order: CityOrder;
  actionLabel?: string;
  onAction?: () => void;
  disabled?: boolean;
};

export function OrderCard({ order, actionLabel, onAction, disabled }: Props) {
  return (
    <article className="card stack">
      <div className="row">
        <span className="badge">#{order.id} · {order.mode}</span>
        <span className="badge">{order.status}</span>
      </div>
      <div>
        <h3 className="title" style={{ fontSize: 20 }}>Заказ по городу</h3>
        <p className="subtitle">A: {order.pickup_address}</p>
        <p className="subtitle">B: {order.destination_address}</p>
      </div>
      <div className="grid grid-2">
        <div className="card-soft">
          <strong>{order.passenger_price} {order.currency}</strong>
          <p className="subtitle">Цена пассажира</p>
        </div>
        <div className="card-soft">
          <strong>{order.seen_by_drivers}</strong>
          <p className="subtitle">Подходящих водителей</p>
        </div>
      </div>
      {actionLabel && onAction ? (
        <button className="button" type="button" disabled={disabled} onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}
    </article>
  );
}
