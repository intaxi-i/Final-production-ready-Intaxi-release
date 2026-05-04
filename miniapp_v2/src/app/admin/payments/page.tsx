'use client';

import { useEffect, useState } from 'react';
import { approvePayment, listPendingPayments, rejectPayment } from '@/lib/api';
import type { PendingPayment } from '@/lib/types';

export default function AdminPaymentsPage() {
  const [items, setItems] = useState<PendingPayment[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      setItems(await listPendingPayments());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить платежи');
    } finally {
      setLoading(false);
    }
  }

  async function run(id: number, action: 'approve' | 'reject') {
    setActionId(id);
    setError(null);
    try {
      if (action === 'approve') await approvePayment(id);
      if (action === 'reject') await rejectPayment(id, 'rejected_by_admin');
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
            <h1 className="title">Payment topups</h1>
            <p className="subtitle">Подтверждение пополнений водителей. Одобрение создаёт wallet ledger entry.</p>
          </div>
          <button className="button secondary" type="button" onClick={load} disabled={loading}>Обновить</button>
        </div>
        {error ? <p className="error">{error}</p> : null}
      </section>

      {loading ? <p className="subtitle">Загрузка...</p> : null}
      {!loading && items.length === 0 ? <p className="subtitle">Ожидающих платежей нет.</p> : null}

      <section className="grid grid-2">
        {items.map((item) => (
          <article className="card stack" key={item.id}>
            <div className="row">
              <span className="badge">payment #{item.id}</span>
              <span className="badge">{item.status}</span>
            </div>
            <div>
              <h2 className="title" style={{ fontSize: 22 }}>{item.amount} {item.currency}</h2>
              <p className="subtitle">Driver user #{item.driver_user_id}</p>
            </div>
            <div className="actions">
              <button className="button" type="button" disabled={actionId === item.id} onClick={() => run(item.id, 'approve')}>Approve</button>
              <button className="button danger" type="button" disabled={actionId === item.id} onClick={() => run(item.id, 'reject')}>Reject</button>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
