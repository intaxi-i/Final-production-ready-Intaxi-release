'use client';

import { useEffect, useState } from 'react';
import { listDonationPaymentSettings } from '@/lib/api';
import type { DonationPaymentSetting } from '@/lib/types';

export default function DonatePage() {
  const [items, setItems] = useState<DonationPaymentSetting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      setItems(await listDonationPaymentSettings('uz'));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить реквизиты');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <main className="shell stack">
      <section className="card stack">
        <div>
          <h1 className="title">Поддержать Intaxi</h1>
          <p className="subtitle">
            Карты и digital asset wallet реквизиты берутся из Backend V2 и управляются только админ-панелью.
          </p>
        </div>
        <button className="button secondary" type="button" onClick={load} disabled={loading}>
          Обновить
        </button>
        {error ? <p className="error">{error}</p> : null}
      </section>

      {loading ? <p className="subtitle">Загрузка...</p> : null}
      {!loading && items.length === 0 ? <p className="subtitle">Активные реквизиты пока не добавлены.</p> : null}

      <section className="grid grid-2">
        {items.map((item) => (
          <article className="card stack" key={item.id}>
            <div className="row">
              <span className="badge">{item.method_type}</span>
              {item.currency ? <span className="badge">{item.currency}</span> : null}
            </div>
            <div>
              <h2 className="title" style={{ fontSize: 22 }}>{item.title}</h2>
              {item.instructions ? <p className="subtitle">{item.instructions}</p> : null}
            </div>
            {item.card_number_masked ? (
              <div className="card-soft">
                <strong>{item.card_number_masked}</strong>
                <p className="subtitle">{item.bank_name || 'Банк не указан'} · {item.card_holder_name || 'Владелец не указан'}</p>
              </div>
            ) : null}
            {item.digital_asset_address_preview ? (
              <div className="card-soft">
                <strong>{item.digital_asset_address_preview}</strong>
                <p className="subtitle">{item.digital_asset_network || 'Сеть не указана'}</p>
              </div>
            ) : null}
          </article>
        ))}
      </section>
    </main>
  );
}
