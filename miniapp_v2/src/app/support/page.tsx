'use client';

import { FormEvent, useEffect, useState } from 'react';
import { createSupportTicket, listMySupportTickets } from '@/lib/api-extra';
import type { SupportTicket } from '@/lib/types';

export default function SupportPage() {
  const [items, setItems] = useState<SupportTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    setSaving(true);
    setError(null);
    try {
      await createSupportTicket({
        ticket_type: String(form.get('ticket_type') || 'general'),
        priority: String(form.get('priority') || 'normal'),
        subject: String(form.get('subject') || '') || null,
        message: String(form.get('message') || ''),
      });
      event.currentTarget.reset();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать обращение');
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <main className="shell stack">
      <section className="card stack">
        <h1 className="title">Поддержка</h1>
        <p className="subtitle">Обращения хранятся в Backend V2 и доступны админке.</p>
        {error ? <p className="error">{error}</p> : null}
      </section>

      <section className="card stack">
        <h2 className="title" style={{ fontSize: 22 }}>Новое обращение</h2>
        <form className="stack" onSubmit={submit}>
          <div className="grid grid-2">
            <label className="label">Тип<input className="input" name="ticket_type" defaultValue="general" /></label>
            <label className="label">Приоритет<input className="input" name="priority" defaultValue="normal" /></label>
          </div>
          <label className="label">Тема<input className="input" name="subject" /></label>
          <label className="label">Сообщение<textarea className="input" name="message" rows={4} required /></label>
          <button className="button" type="submit" disabled={saving}>{saving ? 'Отправляем...' : 'Отправить'}</button>
        </form>
      </section>

      <section className="grid grid-2">
        {loading ? <p className="subtitle">Загрузка...</p> : null}
        {items.map((item) => (
          <article className="card stack" key={item.id}>
            <div className="row"><span className="badge">#{item.id}</span><span className="badge">{item.status}</span></div>
            <h2 className="title" style={{ fontSize: 22 }}>{item.subject || item.ticket_type}</h2>
            <p className="subtitle">{item.message}</p>
            {item.admin_notes ? <p className="subtitle">Admin: {item.admin_notes}</p> : null}
          </article>
        ))}
      </section>
    </main>
  );
}
