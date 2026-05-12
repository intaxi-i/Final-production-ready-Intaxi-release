'use client';

import { useEffect, useState } from 'react';
import { RefreshCw, ShieldCheck, UserCheck } from 'lucide-react';
import {
  approveDriverProfile,
  approveWomanDriverProfile,
  listPendingDrivers,
  rejectDriverProfile,
} from '@/lib/api';
import type { PendingDriverProfile } from '@/lib/types';

function womanStatusLabel(value: string) {
  if (value === 'approved') return 'Женский режим подтверждён';
  if (value === 'pending') return 'Женский режим на проверке';
  if (value === 'rejected') return 'Женский режим отклонён';
  return 'Без отдельного допуска';
}

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
      if (action === 'reject') await rejectDriverProfile(id, 'Отклонено администратором');
      if (action === 'woman') await approveWomanDriverProfile(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось выполнить действие');
    } finally {
      setActionId(null);
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <main className="shell stack">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">Админ · водители</p>
            <h1 className="title">Проверка водителей</h1>
            <p className="subtitle mt-2">Подтверждайте профиль водителя и отдельный допуск к женскому режиму.</p>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={load} disabled={loading} aria-label="Обновить">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {error ? <p className="error mt-4">{error}</p> : null}
      </section>

      <section className="metric-grid">
        <div className="metric-card"><div className="metric-label">На проверке</div><div className="metric-value">{items.length}</div></div>
        <div className="metric-card"><div className="metric-label">Женский режим</div><div className="metric-value">{items.filter((item) => item.woman_driver_status === 'pending').length}</div></div>
      </section>

      {loading ? <section className="card"><p className="subtitle">Загрузка...</p></section> : null}
      {!loading && items.length === 0 ? <section className="card"><p className="subtitle">Заявок на проверку пока нет.</p></section> : null}

      <section className="grid grid-2">
        {items.map((item) => (
          <article className="card stack" key={item.id}>
            <div className="row">
              <span className="order-badge">Профиль #{item.id}</span>
              <span className="order-badge">Пользователь #{item.user_id}</span>
            </div>
            <div>
              <h2 className="title" style={{ fontSize: 22 }}>Заявка водителя</h2>
              <p className="subtitle mt-1">Страна: {item.country_code.toUpperCase()}</p>
              <p className="subtitle">Город: {item.city_id || 'не выбран'}</p>
              <p className="subtitle">{womanStatusLabel(item.woman_driver_status)}</p>
            </div>
            <div className="actions">
              <button className="button primary" type="button" disabled={actionId === item.id} onClick={() => run(item.id, 'approve')}>
                <UserCheck size={18} /> Подтвердить
              </button>
              <button className="button secondary" type="button" disabled={actionId === item.id || item.woman_driver_status !== 'pending'} onClick={() => run(item.id, 'woman')}>
                <ShieldCheck size={18} /> Женский режим
              </button>
              <button className="button danger" type="button" disabled={actionId === item.id} onClick={() => run(item.id, 'reject')}>Отклонить</button>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
