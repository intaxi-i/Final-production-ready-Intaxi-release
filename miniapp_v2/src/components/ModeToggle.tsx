'use client';

import type { RideMode } from '@/lib/types';

type Props = {
  value: RideMode;
  onChange: (value: RideMode) => void;
};

export function ModeToggle({ value, onChange }: Props) {
  return (
    <div className="actions" role="group" aria-label="Ride mode">
      <button
        className={`button ${value === 'regular' ? '' : 'secondary'}`}
        type="button"
        onClick={() => onChange('regular')}
      >
        Обычный режим
      </button>
      <button
        className={`button ${value === 'women' ? '' : 'secondary'}`}
        type="button"
        onClick={() => onChange('women')}
      >
        Women mode
      </button>
    </div>
  );
}
