'use client';

import { useEffect, useState } from 'react';
import {
  approveDriverProfile,
  approveWomanDriverProfile,
  listPendingDrivers,
  rejectDriverProfile,
} from '@/lib/api';
import type { PendingDriverProfile } from '@/lib/types';

export default function AdminDriversPage() {
  const [items, setItems] = useState<PendingDriverProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      setItems(await listPendingDrivers());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить водителей');
    } finally {
      setLoading(false);
    }
  }

  async function run(id: number, action: 'approve' | 'reject' | 'woman') {
    setActionId(id);
    setError(null);
    try {
      if (action === 'approve') await approveDriverProfile(id);
      if (action === 'reject') await rejectDriverProfile(id, 'rejected_by_admin');
      if (action === 'woman') await approveWomanDriverProfile(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось выполнить действие');
    } finally {
      setActionId(null);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <main className="shell stack">
      <section className="card stack">
        <div className="row">
          <div>
            <h1 className="title">Driver verification</h1>
            <p className="subtitle">Проверка водителей и отдельного режима допуска через Backend V2 с audit log.</p>
          </div>
          <button className="button secondary" type="button" onClick={load} disabled={loading}>Обновить</button>
        </div>
        {error ? <p className="error">{error}</p> : null}
      </section>

      {loading ? <p className="subtitle">Загрузка...</p> : null}
      {!loading && items.length === 0 ? <p className="subtitle">Заявок на проверку пока нет.</p> : null}

      <section className="grid grid-2">
        {items.map((item) => (
          <article className="card stack" key={item.id}>
            <div className="row">
              <span className="badge">profile #{item.id}</span>
              <span className="badge">user #{item.user_id}</span>
            </div>
            <div>
              <h2 className="title" style={{ fontSize: 22 }}>Driver profile</h2>
              <p className="subtitle">Country: {item.country_code}</p>
              <p className="subtitle">City: {item.city_id || 'not set'}</p>
              <p className="subtitle">Special mode: {item.woman_driver_status}</p>
            </div>
            <div className="actions">
              <button className="button" type="button" disabled={actionId === item.id} onClick={() => run(item.id, 'approve')}>Approve</button>
              <button className="button secondary" type="button" disabled={actionId === item.id} onClick={() => run(item.id, 'woman')}>Approve special mode</button>
              <button className="button danger" type="button" disabled={actionId === item.id} onClick={() => run(item.id, 'reject')}>Reject</button>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
