'use client';

import { useEffect, useState } from 'react';
import { getDriverOnline, setDriverOnline, updateRole } from '@/lib/api';
import type { DriverOnlineState } from '@/lib/types';

export default function DriverOnlinePage() {
  const [state, setState] = useState<DriverOnlineState | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      setState(await getDriverOnline());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить статус водителя');
    } finally {
      setLoading(false);
    }
  }

  async function toggle(next: boolean) {
    setSaving(true);
    setError(null);
    try {
      await updateRole('driver');
      setState(await setDriverOnline({ is_online: next, country_code: 'uz' }));
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
          <h1 className="title">Водитель online</h1>
          <p className="subtitle">Онлайн-статус и busy-флаг хранятся в Backend V2, чтобы водитель не взял две активные поездки.</p>
        </div>
        {error ? <p className="error">{error}</p> : null}
      </section>

      <section className="card stack">
        {loading ? <p className="subtitle">Загрузка...</p> : null}
        {state ? (
          <>
            <div className="grid grid-2">
              <div className="card-soft"><strong>{state.is_online ? 'online' : 'offline'}</strong><p className="subtitle">Статус</p></div>
              <div className="card-soft"><strong>{state.is_busy ? 'busy' : 'free'}</strong><p className="subtitle">Занятость</p></div>
            </div>
            <div className="actions">
              <button className="button" type="button" disabled={saving || state.is_online} onClick={() => toggle(true)}>Выйти online</button>
              <button className="button secondary" type="button" disabled={saving || !state.is_online} onClick={() => toggle(false)}>Уйти offline</button>
            </div>
          </>
        ) : null}
      </section>
    </main>
  );
}
