'use client';

import { useEffect, useState } from 'react';
import { listAdminDonationPaymentSettings, updateAdminDonationPaymentSetting } from '@/lib/api';
import type { DonationPaymentSetting } from '@/lib/types';

export default function AdminSupportSettingsPage() {
  const [items, setItems] = useState<DonationPaymentSetting[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      setItems(await listAdminDonationPaymentSettings());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить настройки');
    } finally {
      setLoading(false);
    }
  }

  async function toggle(item: DonationPaymentSetting) {
    setSaving(true);
    setError(null);
    try {
      await updateAdminDonationPaymentSetting(item.id, { is_active: !item.is_active });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось изменить статус');
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
          <h1 className="title">Donation settings</h1>
          <p className="subtitle">Админ видит и включает только настройки, которые хранятся в Backend V2.</p>
        </div>
        {error ? <p className="error">{error}</p> : null}
      </section>

      <section className="grid grid-2">
        {loading ? <p className="subtitle">Загрузка...</p> : null}
        {items.map((item) => (
          <article className="card stack" key={item.id}>
            <div className="row">
              <span className="badge">{item.method_type}</span>
              <span className="badge">{item.is_active ? 'active' : 'disabled'}</span>
            </div>
            <div>
              <h2 className="title" style={{ fontSize: 22 }}>{item.title}</h2>
              <p className="subtitle">{item.country_code || 'global'} · {item.currency || 'any currency'}</p>
            </div>
            <div className="card-soft">
              <p className="subtitle">Card: {item.card_number_masked || '—'}</p>
              <p className="subtitle">Address: {item.digital_asset_address_preview || '—'}</p>
              <p className="subtitle">Network: {item.digital_asset_network || '—'}</p>
            </div>
            <button className="button secondary" type="button" disabled={saving} onClick={() => toggle(item)}>
              {item.is_active ? 'Отключить' : 'Включить'}
            </button>
          </article>
        ))}
      </section>
    </main>
  );
}
