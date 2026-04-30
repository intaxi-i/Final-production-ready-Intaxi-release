'use client';

import { FormEvent, useEffect, useState } from 'react';
import { createDriverPaymentMethod, listMyDriverPaymentMethods } from '@/lib/api';
import type { DriverPaymentMethod } from '@/lib/types';

export default function DriverPaymentMethodsPage() {
  const [items, setItems] = useState<DriverPaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      setItems(await listMyDriverPaymentMethods());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить реквизиты');
    } finally {
      setLoading(false);
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSaving(true);
    setError(null);
    try {
      await createDriverPaymentMethod({
        country_code: String(form.get('country_code') || 'uz'),
        method_type: 'card',
        card_number: String(form.get('card_number') || '') || null,
        card_holder_name: String(form.get('card_holder_name') || '') || null,
        bank_name: String(form.get('bank_name') || '') || null,
      });
      event.currentTarget.reset();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить реквизиты');
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <main className="shell stack">
      <section className="card stack">
        <div>
          <h1 className="title">Реквизиты водителя</h1>
          <p className="subtitle">
            Эти данные видит только пассажир назначенной поездки через защищённый trip endpoint.
          </p>
        </div>
        {error ? <p className="error">{error}</p> : null}
      </section>

      <section className="card stack">
        <h2 className="title" style={{ fontSize: 22 }}>Добавить карту</h2>
        <form className="stack" onSubmit={submit}>
          <div className="grid grid-2">
            <label className="label">Страна<input className="input" name="country_code" defaultValue="uz" /></label>
            <label className="label">Номер карты<input className="input" name="card_number" required /></label>
            <label className="label">Владелец<input className="input" name="card_holder_name" /></label>
            <label className="label">Банк<input className="input" name="bank_name" /></label>
          </div>
          <button className="button" type="submit" disabled={saving}>{saving ? 'Сохраняем...' : 'Сохранить'}</button>
        </form>
      </section>

      <section className="grid grid-2">
        {loading ? <p className="subtitle">Загрузка...</p> : null}
        {items.map((item) => (
          <article className="card stack" key={item.id}>
            <span className="badge">{item.method_type}</span>
            <div>
              <h2 className="title" style={{ fontSize: 22 }}>{item.card_number_masked || 'Карта'}</h2>
              <p className="subtitle">{item.bank_name || 'Банк не указан'} · {item.card_holder_name || 'Владелец не указан'}</p>
            </div>
            <span className="badge">{item.is_active ? 'active' : 'disabled'}</span>
          </article>
        ))}
      </section>
    </main>
  );
}
