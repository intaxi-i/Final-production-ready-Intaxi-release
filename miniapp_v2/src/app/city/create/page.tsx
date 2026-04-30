'use client';

import { FormEvent, useState } from 'react';
import { createCityOrder } from '@/lib/api';
import type { CityOrder, RideMode } from '@/lib/types';
import { ModeToggle } from '@/components/ModeToggle';
import { OrderCard } from '@/components/OrderCard';

export default function CityCreatePage() {
  const [mode, setMode] = useState<RideMode>('regular');
  const [pickup, setPickup] = useState('');
  const [destination, setDestination] = useState('');
  const [price, setPrice] = useState('30000');
  const [seats, setSeats] = useState('1');
  const [created, setCreated] = useState<CityOrder | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const order = await createCityOrder({
        mode,
        country_code: 'uz',
        city_id: null,
        pickup_address: pickup,
        destination_address: destination,
        seats: Number(seats),
        passenger_price: Number(price),
      });
      setCreated(order);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать заказ');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className={`shell stack ${mode === 'women' ? 'women-mode' : ''}`}>
      <section className="card stack">
        <div>
          <h1 className="title">Создать city-заказ</h1>
          <p className="subtitle">Пассажир предлагает цену. Backend V2 проверяет роль, режим и создаёт заказ.</p>
        </div>
        <ModeToggle value={mode} onChange={setMode} />
        <form className="stack" onSubmit={submit}>
          <label className="label">
            Откуда
            <input className="input" value={pickup} onChange={(event) => setPickup(event.target.value)} required />
          </label>
          <label className="label">
            Куда
            <input className="input" value={destination} onChange={(event) => setDestination(event.target.value)} required />
          </label>
          <div className="grid grid-2">
            <label className="label">
              Цена
              <input className="input" inputMode="numeric" value={price} onChange={(event) => setPrice(event.target.value)} required />
            </label>
            <label className="label">
              Мест
              <input className="input" inputMode="numeric" value={seats} onChange={(event) => setSeats(event.target.value)} required />
            </label>
          </div>
          {error ? <p className="error">{error}</p> : null}
          <button className="button" type="submit" disabled={loading}>
            {loading ? 'Создаём...' : 'Создать заказ'}
          </button>
        </form>
      </section>

      {created ? <OrderCard order={created} /> : null}
    </main>
  );
}
