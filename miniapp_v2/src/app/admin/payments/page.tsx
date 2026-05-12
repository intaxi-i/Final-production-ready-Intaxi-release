'use client';

import { useEffect, useState } from 'react';
import { CheckCircle2, CreditCard, RefreshCw, XCircle } from 'lucide-react';
import { approvePayment, listPendingPayments, rejectPayment } from '@/lib/api';
import type { PendingPayment } from '@/lib/types';

function statusLabel(value: string) {
  if (value === 'pending') return 'Ожидает проверки';
  if (value === 'approved') return 'Подтверждено';
  if (value === 'rejected') return 'Отклонено';
  return value;
}

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
      if (action === 'reject') await rejectPayment(id, 'Отклонено администратором');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось выполнить действие');
    } finally {
      setActionId(null);
    }
  }

  useEffect(() => { load(); }, []);

  const totalAmount = items.reduce((sum, item) => sum + item.amount, 0);

  return (
    <main className="shell stack">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">Админ · платежи</p>
            <h1 className="title">Пополнения водителей</h1>
            <p className="subtitle mt-2">Проверяйте заявки на пополнение и подтверждайте только корректные платежи.</p>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={load} disabled={loading} aria-label="Обновить">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {error ? <p className="error mt-4">{error}</p> : null}
      </section>

      <section className="metric-grid">
        <div className="metric-card"><div className="metric-label">Ожидают</div><div className="metric-value">{items.length}</div></div>
        <div className="metric-card"><div className="metric-label">Сумма</div><div className="metric-value">{totalAmount.toLocaleString('ru-RU')}</div></div>
      </section>

      {loading ? <section className="card"><p className="subtitle">Загрузка...</p></section> : null}
      {!loading && items.length === 0 ? <section className="card"><p className="subtitle">Ожидающих платежей нет.</p></section> : null}

      <section className="grid grid-2">
        {items.map((item) => (
          <article className="card stack" key={item.id}>
            <div className="row">
              <span className="order-badge">Платёж #{item.id}</span>
              <span className="order-badge">{statusLabel(item.status)}</span>
            </div>
            <div className="row rounded-3xl bg-slate-50 p-4">
              <div>
                <p className="metric-label">Сумма</p>
                <h2 className="title" style={{ fontSize: 26 }}>{item.amount.toLocaleString('ru-RU')} {item.currency}</h2>
                <p className="subtitle mt-1">Водитель #{item.driver_user_id}</p>
              </div>
              <CreditCard className="text-brand-yellow" />
            </div>
            <div className="actions">
              <button className="button primary" type="button" disabled={actionId === item.id} onClick={() => run(item.id, 'approve')}>
                <CheckCircle2 size={18} /> Подтвердить
              </button>
              <button className="button danger" type="button" disabled={actionId === item.id} onClick={() => run(item.id, 'reject')}>
                <XCircle size={18} /> Отклонить
              </button>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
