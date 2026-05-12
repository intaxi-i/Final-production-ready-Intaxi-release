'use client';

import { FormEvent, useEffect, useState } from 'react';
import { Percent, RefreshCw, ShieldCheck } from 'lucide-react';
import { createCommissionRule, listCommissionRules } from '@/lib/api';
import type { CommissionRule } from '@/lib/types';

function scopeLabel(value: string) {
  if (value === 'country') return 'Страна';
  if (value === 'city') return 'Город';
  if (value === 'driver') return 'Водитель';
  return 'Весь сервис';
}

function statusLabel(active: boolean) {
  return active ? 'Активно' : 'Отключено';
}

export default function AdminCommissionPage() {
  const [items, setItems] = useState<CommissionRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      setItems(await listCommissionRules());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить правила комиссии');
    } finally {
      setLoading(false);
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const percent = Number(form.get('commission_percent') || 0);
    const freeFirstRides = Number(form.get('free_first_rides') || 0);

    if (!Number.isFinite(percent) || percent < 0 || percent > 5) {
      setError('Комиссия Intaxi не должна быть выше 5%.');
      return;
    }

    if (!Number.isFinite(freeFirstRides) || freeFirstRides < 0) {
      setError('Количество бесплатных первых поездок не может быть отрицательным.');
      return;
    }

    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await createCommissionRule({
        scope_type: String(form.get('scope_type') || 'global'),
        scope_id: String(form.get('scope_id') || 'global').trim() || 'global',
        commission_percent: percent,
        free_first_rides: freeFirstRides,
      });
      event.currentTarget.reset();
      setMessage('Правило комиссии создано.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать правило');
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => { load(); }, []);

  const activeRules = items.filter((item) => item.is_active).length;
  const averageCommission = items.length ? items.reduce((sum, item) => sum + item.commission_percent, 0) / items.length : 0;

  return (
    <main className="shell stack">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">Админ · комиссия</p>
            <h1 className="title">Правила комиссии</h1>
            <p className="subtitle mt-2">Настройте комиссию по сервису, стране, городу или отдельному водителю. Лимит Intaxi — до 5%.</p>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={load} disabled={loading} aria-label="Обновить">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {error ? <p className="error mt-4">{error}</p> : null}
        {message ? <p className="success mt-4">{message}</p> : null}
      </section>

      <section className="metric-grid">
        <div className="metric-card"><div className="metric-label">Правил</div><div className="metric-value">{items.length}</div></div>
        <div className="metric-card"><div className="metric-label">Активных</div><div className="metric-value">{activeRules}</div></div>
        <div className="metric-card"><div className="metric-label">Средняя</div><div className="metric-value">{averageCommission.toFixed(1)}%</div></div>
        <div className="metric-card"><div className="metric-label">Лимит</div><div className="metric-value">5%</div></div>
      </section>

      <section className="card stack">
        <div className="row">
          <div>
            <p className="metric-label">Новое правило</p>
            <h2 className="title" style={{ fontSize: 22 }}>Создать комиссию</h2>
          </div>
          <Percent className="text-brand-yellow" />
        </div>
        <form className="stack" onSubmit={submit}>
          <div className="grid grid-2">
            <label className="label">Уровень
              <select className="select" name="scope_type" defaultValue="global">
                <option value="global">Весь сервис</option>
                <option value="country">Страна</option>
                <option value="city">Город</option>
                <option value="driver">Водитель</option>
              </select>
            </label>
            <label className="label">Код/ID уровня
              <input className="input" name="scope_id" defaultValue="global" placeholder="global, uz, city_id или user_id" />
            </label>
            <label className="label">Комиссия, %
              <input className="input" name="commission_percent" defaultValue="0" inputMode="decimal" />
            </label>
            <label className="label">Бесплатных первых поездок
              <input className="input" name="free_first_rides" defaultValue="0" inputMode="numeric" />
            </label>
          </div>
          <button className="button primary full-submit" type="submit" disabled={saving}>{saving ? 'Сохраняем...' : 'Создать правило'}</button>
        </form>
      </section>

      {loading ? <section className="card"><p className="subtitle">Загрузка...</p></section> : null}
      {!loading && items.length === 0 ? <section className="card"><p className="subtitle">Правила комиссии ещё не созданы.</p></section> : null}

      <section className="grid grid-2">
        {items.map((item) => (
          <article className="card stack" key={item.id}>
            <div className="row">
              <span className="order-badge">{scopeLabel(item.scope_type)}</span>
              <span className={`order-badge ${item.is_active ? 'bg-brand-yellow text-brand-dark' : ''}`}>{statusLabel(item.is_active)}</span>
            </div>
            <div className="row rounded-3xl bg-slate-50 p-4">
              <div>
                <p className="metric-label">{item.scope_id}</p>
                <h2 className="title" style={{ fontSize: 28 }}>{item.commission_percent}%</h2>
                <p className="subtitle mt-1">Бесплатных первых поездок: {item.free_first_rides}</p>
              </div>
              <ShieldCheck className="text-brand-yellow" />
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
