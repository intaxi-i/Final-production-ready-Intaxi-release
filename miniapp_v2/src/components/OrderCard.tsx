import { useState } from 'react';
import type { CityOrder } from '@/lib/types';

type Props = {
  order: CityOrder;
  actionLabel?: string;
  onAction?: () => void;
  onCounterOffer?: (price: number) => void;
  disabled?: boolean;
};

export function OrderCard({ order, actionLabel, onAction, onCounterOffer, disabled }: Props) {
  const [customPrice, setCustomPrice] = useState(String(order.passenger_price));

  return (
    <article className="card stack relative overflow-hidden">
      <div className="row">
        <span className="badge bg-blue-100 text-blue-800">#{order.id} · {order.mode}</span>
        <span className="badge">{order.status}</span>
      </div>
      <div>
        <p className="subtitle text-sm">📍 <b className="text-gray-900 dark:text-white">А:</b> {order.pickup_address}</p>
        <p className="subtitle text-sm mt-1">🏁 <b className="text-gray-900 dark:text-white">Б:</b> {order.destination_address}</p>
        {order.estimated_distance_km ? (
          <p className="subtitle mt-3 font-medium text-blue-600 dark:text-blue-400">
            🛣 {order.estimated_distance_km} км 
            {order.estimated_duration_min ? ` · ⏳ ~${order.estimated_duration_min} мин` : ''}
          </p>
        ) : null}
      </div>
      <div className="grid grid-2 mt-2 gap-2">
        <div className="card-soft bg-green-50 dark:bg-green-900/20">
          <strong className="text-green-700 dark:text-green-400">{order.passenger_price} {order.currency}</strong>
          <p className="subtitle text-xs">Цена пассажира</p>
        </div>
        <div className="card-soft">
          <strong>{order.seen_by_drivers}</strong>
          <p className="subtitle text-xs">Конкурентов видят</p>
        </div>
      </div>
      
      {actionLabel && onAction ? (
        <button className="button w-full mt-2 font-bold py-3" type="button" disabled={disabled} onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}

      {onCounterOffer ? (
        <div className="stack mt-4 p-4 border rounded-xl bg-gray-50 dark:bg-[#1b2638]">
          <p className="text-center text-sm font-semibold text-gray-700 dark:text-gray-300">Предложить свою цену</p>
          <div className="flex gap-2">
            {[10, 20, 30].map(pct => {
              const val = Math.round(order.passenger_price * (1 + pct / 100));
              return (
                <button key={pct} type="button" className="button secondary flex-1 py-2 text-sm font-medium" disabled={disabled} onClick={() => onCounterOffer(val)}>
                  +{pct}%
                </button>
              );
            })}
          </div>
          <div className="flex gap-2 mt-2">
            <input 
              type="number" 
              className="input flex-1 bg-white dark:bg-[#162033]" 
              value={customPrice} 
              onChange={e => setCustomPrice(e.target.value)} 
              placeholder="Своя цена..."
            />
            <button 
              type="button" 
              className="button whitespace-nowrap bg-blue-600 text-white" 
              disabled={disabled || !customPrice} 
              onClick={() => onCounterOffer(Number(customPrice))}
            >
              Отправить
            </button>
          </div>
        </div>
      ) : null}
    </article>
  );
}
