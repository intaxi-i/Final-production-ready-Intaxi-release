'use client';

import { FormEvent, useEffect, useState } from 'react';
import { getMe, updateMe, updateRole } from '@/lib/api';
import type { ProfileGender, UserMe, UserRole } from '@/lib/types';

export default function ProfilePage() {
  const [me, setMe] = useState<UserMe | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      setMe(await getMe());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить профиль');
    } finally {
      setLoading(false);
    }
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSaving(true);
    setError(null);
    try {
      setMe(await updateMe({
        full_name: String(form.get('full_name') || ''),
        language: String(form.get('language') || 'ru'),
        country_code: String(form.get('country_code') || '') || null,
        profile_gender: String(form.get('profile_gender') || 'unspecified') as ProfileGender,
        is_adult_confirmed: form.get('is_adult_confirmed') === 'on',
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить профиль');
    } finally {
      setSaving(false);
    }
  }

  async function switchRole(role: UserRole) {
    setSaving(true);
    setError(null);
    try {
      setMe(await updateRole(role));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сменить роль');
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
        <div className="row">
          <div>
            <h1 className="title">Профиль</h1>
            <p className="subtitle">Роль, страна, язык и eligibility для отдельных режимов хранятся в Backend V2.</p>
          </div>
          <button className="button secondary" type="button" onClick={load} disabled={loading}>Обновить</button>
        </div>
        {error ? <p className="error">{error}</p> : null}
      </section>

      {loading ? <p className="subtitle">Загрузка...</p> : null}

      {me ? (
        <section className="card stack">
          <div className="row">
            <span className="badge">ID {me.id}</span>
            <span className="badge">role: {me.active_role || 'none'}</span>
          </div>
          <form className="stack" onSubmit={save}>
            <label className="label">Имя<input className="input" name="full_name" defaultValue={me.full_name} required /></label>
            <div className="grid grid-2">
              <label className="label">Язык<input className="input" name="language" defaultValue={me.language} /></label>
              <label className="label">Страна<input className="input" name="country_code" defaultValue={me.country_code || 'uz'} /></label>
              <label className="label">Пол<select className="select" name="profile_gender" defaultValue={me.profile_gender}><option value="unspecified">unspecified</option><option value="woman">woman</option><option value="man">man</option></select></label>
              <label className="label" style={{ alignContent: 'center' }}><span><input name="is_adult_confirmed" type="checkbox" defaultChecked={me.is_adult_confirmed} /> Подтверждаю совершеннолетие</span></label>
            </div>
            <button className="button" type="submit" disabled={saving}>{saving ? 'Сохраняем...' : 'Сохранить профиль'}</button>
          </form>
          <div className="actions">
            <button className="button secondary" type="button" disabled={saving} onClick={() => switchRole('passenger')}>Роль пассажир</button>
            <button className="button secondary" type="button" disabled={saving} onClick={() => switchRole('driver')}>Роль водитель</button>
          </div>
        </section>
      ) : null}
    </main>
  );
}
