'use client';

import { FormEvent, useEffect, useState } from 'react';
import { Headphones, MessageCircle, RefreshCw, ShieldCheck } from 'lucide-react';
import { BottomNav } from '@/components/BottomNav';
import { createSupportTicket, listMySupportTickets } from '@/lib/api-extra';
import type { SupportTicket } from '@/lib/types';

function ticketTypeLabel(value: string) {
  if (value === 'trip') return 'Поездка';
  if (value === 'payment') return 'Оплата';
  if (value === 'driver') return 'Водитель';
  if (value === 'safety') return 'Безопасность';
  return 'Общий вопрос';
}

function priorityLabel(value: string) {
  if (value === 'high') return 'Срочно';
  if (value === 'low') return 'Не срочно';
  return 'Обычный';
}

function statusLabel(value: string) {
  if (value === 'open') return 'Открыто';
  if (value === 'in_progress') return 'В работе';
  if (value === 'resolved') return 'Решено';
  if (value === 'closed') return 'Закрыто';
  return value;
}

export default function SupportPage() {
  const [items, setItems] = useState<SupportTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      setItems(await listMySupportTickets());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить обращения');
    } finally {
      setLoading(false);
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const text = String(form.get('message') || '').trim();
    if (!text) {
      setError('Опишите вопрос или проблему.');
      return;
    }

    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await createSupportTicket({
        ticket_type: String(form.get('ticket_type') || 'general'),
        priority: String(form.get('priority') || 'normal'),
        subject: String(form.get('subject') || '').trim() || null,
        message: text,
      });
      event.currentTarget.reset();
      setMessage('Обращение отправлено. Мы ответим в этом разделе.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать обращение');
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
            <p className="metric-label">Помощь</p>
            <h1 className="title">Поддержка</h1>
            <p className="subtitle mt-2">Напишите, что случилось. Обращение увидит команда поддержки Intaxi.</p>
          </div>
          <Headphones className="text-brand-yellow" size={34} />
        </div>
      </section>

      {error ? <p className="error">{error}</p> : null}
      {message ? <p className="success">{message}</p> : null}

      <section className="metric-grid">
        <div className="metric-card"><div className="metric-label">Всего</div><div className="metric-value">{items.length}</div></div>
        <div className="metric-card"><div className="metric-label">Открытых</div><div className="metric-value">{items.filter((item) => !['resolved', 'closed'].includes(item.status)).length}</div></div>
      </section>

      <form className="card stack" onSubmit={submit}>
        <div className="row">
          <div>
            <p className="metric-label">Новое обращение</p>
            <h2 className="title" style={{ fontSize: 22 }}>Чем помочь?</h2>
          </div>
          <MessageCircle className="text-brand-yellow" />
        </div>
        <div className="grid grid-2">
          <label className="label">Тема
            <select className="select" name="ticket_type" defaultValue="general">
              <option value="general">Общий вопрос</option>
              <option value="trip">Поездка</option>
              <option value="payment">Оплата</option>
              <option value="driver">Водитель</option>
              <option value="safety">Безопасность</option>
            </select>
          </label>
          <label className="label">Срочность
            <select className="select" name="priority" defaultValue="normal">
              <option value="low">Не срочно</option>
              <option value="normal">Обычный</option>
              <option value="high">Срочно</option>
            </select>
          </label>
        </div>
        <label className="label">Заголовок
          <input className="input" name="subject" placeholder="Например: водитель не приехал" />
        </label>
        <label className="label">Сообщение
          <textarea className="input" name="message" rows={4} placeholder="Опишите ситуацию простыми словами" required />
        </label>
        <button className="button primary full-submit" type="submit" disabled={saving}>{saving ? 'Отправляем...' : 'Отправить обращение'}</button>
      </form>

      <section className="card stack">
        <div className="row">
          <div>
            <p className="metric-label">История</p>
            <h2 className="title" style={{ fontSize: 22 }}>Мои обращения</h2>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={load} disabled={loading} aria-label="Обновить">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {loading ? <p className="subtitle">Загрузка...</p> : null}
        {!loading && items.length === 0 ? <p className="subtitle">Обращений пока нет.</p> : null}
        <div className="stack">
          {items.map((item) => (
            <article className="card-soft" key={item.id}>
              <div className="row">
                <span className="order-badge">#{item.id}</span>
                <span className="order-badge">{statusLabel(item.status)}</span>
              </div>
              <div className="mt-4">
                <p className="metric-label">{ticketTypeLabel(item.ticket_type)} · {priorityLabel(item.priority)}</p>
                <h3 className="title mt-1" style={{ fontSize: 22 }}>{item.subject || ticketTypeLabel(item.ticket_type)}</h3>
                <p className="subtitle mt-2">{item.message}</p>
                {item.admin_notes ? <p className="success mt-3">Ответ поддержки: {item.admin_notes}</p> : null}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="card-soft row">
        <div>
          <strong>Безопасность</strong>
          <p className="subtitle mt-1">Не отправляйте пароли, коды SMS и seed-фразы. Поддержка Intaxi их не запрашивает.</p>
        </div>
        <ShieldCheck className="text-brand-yellow" />
      </section>
      <BottomNav />
    </main>
  );
}
