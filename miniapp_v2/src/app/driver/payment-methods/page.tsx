'use client';

import { FormEvent, useEffect, useState } from 'react';
import { CreditCard, RefreshCw, ShieldCheck, WalletCards } from 'lucide-react';
import { BottomNav } from '@/components/BottomNav';
import { createDriverPaymentMethod, listMyDriverPaymentMethods } from '@/lib/api';
import { COUNTRY_OPTIONS } from '@/lib/constants';
import type { DriverPaymentMethod } from '@/lib/types';

function methodLabel(value: string) {
  if (value === 'bank_transfer') return 'Банковский перевод';
  if (value === 'cash') return 'Наличные';
  if (value === 'crypto') return 'Криптовалюта';
  return 'Карта';
}

function activityLabel(active: boolean) {
  return active ? 'Активно' : 'Отключено';
}

export default function DriverPaymentMethodsPage() {
  const [items, setItems] = useState<DriverPaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

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
    setMessage(null);
    try {
      await createDriverPaymentMethod({
        country_code: String(form.get('country_code') || 'uz'),
        method_type: String(form.get('method_type') || 'card'),
        card_number: String(form.get('card_number') || '') || null,
        card_holder_name: String(form.get('card_holder_name') || '') || null,
        bank_name: String(form.get('bank_name') || '') || null,
      });
      event.currentTarget.reset();
      setMessage('Реквизиты сохранены. Пассажир увидит их только после назначения поездки.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить реквизиты');
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">Водитель</p>
            <h1 className="title">Реквизиты</h1>
            <p className="subtitle mt-2">Добавьте способ получения оплаты. Реквизиты показываются только пассажиру вашей назначенной поездки.</p>
          </div>
          <WalletCards className="text-brand-yellow" size={34} />
        </div>
      </section>

      {error ? <p className="error">{error}</p> : null}
      {message ? <p className="success">{message}</p> : null}

      <section className="metric-grid">
        <div className="metric-card"><div className="metric-label">Всего</div><div className="metric-value">{items.length}</div></div>
        <div className="metric-card"><div className="metric-label">Активных</div><div className="metric-value">{items.filter((item) => item.is_active).length}</div></div>
      </section>

      <form className="card stack" onSubmit={submit}>
        <div className="row">
          <div>
            <p className="metric-label">Новый способ</p>
            <h2 className="title" style={{ fontSize: 22 }}>Добавить оплату</h2>
          </div>
          <CreditCard className="text-brand-yellow" />
        </div>
        <div className="grid grid-2">
          <label className="label">Страна
            <select className="select" name="country_code" defaultValue="uz">
              {COUNTRY_OPTIONS.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}
            </select>
          </label>
          <label className="label">Тип
            <select className="select" name="method_type" defaultValue="card">
              <option value="card">Карта</option>
              <option value="bank_transfer">Банковский перевод</option>
              <option value="cash">Наличные</option>
              <option value="crypto">Криптовалюта</option>
            </select>
          </label>
        </div>
        <div className="grid grid-2">
          <label className="label">Номер карты / счёта
            <input className="input" name="card_number" inputMode="numeric" placeholder="8600••••••••1234" required />
          </label>
          <label className="label">Владелец
            <input className="input" name="card_holder_name" placeholder="Имя на карте" />
          </label>
          <label className="label">Банк
            <input className="input" name="bank_name" placeholder="Название банка" />
          </label>
        </div>
        <button className="button primary full-submit" type="submit" disabled={saving}>{saving ? 'Сохраняем...' : 'Сохранить реквизиты'}</button>
      </form>

      <section className="card stack">
        <div className="row">
          <div>
            <p className="metric-label">Сохранённые</p>
            <h2 className="title" style={{ fontSize: 22 }}>Способы оплаты</h2>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={load} disabled={loading} aria-label="Обновить">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {loading ? <p className="subtitle">Загрузка...</p> : null}
        {!loading && items.length === 0 ? <p className="subtitle">Реквизиты ещё не добавлены.</p> : null}
        <div className="stack">
          {items.map((item) => (
            <article className="card-soft" key={item.id}>
              <div className="row">
                <span className="order-badge">{methodLabel(item.method_type)}</span>
                <span className={`order-badge ${item.is_active ? 'bg-brand-yellow text-brand-dark' : ''}`}>{activityLabel(item.is_active)}</span>
              </div>
              <div className="mt-4">
                <h3 className="title" style={{ fontSize: 22 }}>{item.card_number_masked || 'Реквизиты'}</h3>
                <p className="subtitle mt-1">{item.bank_name || 'Банк не указан'} · {item.card_holder_name || 'Владелец не указан'}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="card-soft row">
        <div>
          <strong>Безопасность</strong>
          <p className="subtitle mt-1">Пассажир получает реквизиты только после назначения поездки.</p>
        </div>
        <ShieldCheck className="text-brand-yellow" />
      </section>
      <BottomNav />
    </main>
  );
}
