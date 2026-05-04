'use client';

import { FormEvent, useEffect, useState } from 'react';
import { createCommissionRule, listCommissionRules } from '@/lib/api';
import type { CommissionRule } from '@/lib/types';

export default function AdminCommissionPage() {
  const [items, setItems] = useState<CommissionRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    setSaving(true);
    setError(null);
    try {
      await createCommissionRule({
        scope_type: String(form.get('scope_type') || 'global'),
        scope_id: String(form.get('scope_id') || 'global'),
        commission_percent: Number(form.get('commission_percent') || 0),
        free_first_rides: Number(form.get('free_first_rides') || 0),
      });
      event.currentTarget.reset();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать правило');
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
        <h1 className="title">Commission rules</h1>
        <p className="subtitle">Начальная комиссия может быть 0%, а дальше меняется по global/country/city/driver scope.</p>
        {error ? <p className="error">{error}</p> : null}
      </section>

      <section className="card stack">
        <h2 className="title" style={{ fontSize: 22 }}>Создать правило</h2>
        <form className="stack" onSubmit={submit}>
          <div className="grid grid-2">
            <label className="label">Scope<select className="select" name="scope_type" defaultValue="global"><option value="global">global</option><option value="country">country</option><option value="city">city</option><option value="driver">driver</option></select></label>
            <label className="label">Scope ID<input className="input" name="scope_id" defaultValue="global" /></label>
            <label className="label">Commission %<input className="input" name="commission_percent" defaultValue="0" inputMode="decimal" /></label>
            <label className="label">Free first rides<input className="input" name="free_first_rides" defaultValue="0" inputMode="numeric" /></label>
          </div>
          <button className="button" type="submit" disabled={saving}>{saving ? 'Сохраняем...' : 'Создать правило'}</button>
        </form>
      </section>

      <section className="grid grid-2">
        {loading ? <p className="subtitle">Загрузка...</p> : null}
        {items.map((item) => (
          <article className="card stack" key={item.id}>
            <div className="row"><span className="badge">{item.scope_type}:{item.scope_id}</span><span className="badge">{item.is_active ? 'active' : 'disabled'}</span></div>
            <h2 className="title" style={{ fontSize: 22 }}>{item.commission_percent}%</h2>
            <p className="subtitle">Free first rides: {item.free_first_rides}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
