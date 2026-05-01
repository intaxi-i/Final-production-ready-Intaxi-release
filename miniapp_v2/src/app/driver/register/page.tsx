'use client';

import { FormEvent, useEffect, useState } from 'react';
import { getDriverProfile, listVehicles, submitDriverProfile, submitVehicle } from '@/lib/api-extra';
import type { DriverProfile, Vehicle } from '@/lib/types';

export default function DriverRegisterPage() {
  const [profile, setProfile] = useState<DriverProfile | null>(null);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const [profileData, vehicleData] = await Promise.all([getDriverProfile(), listVehicles()]);
      setProfile(profileData);
      setVehicles(vehicleData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить регистрацию');
    } finally {
      setLoading(false);
    }
  }

  async function submitProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSaving(true);
    setError(null);
    try {
      setProfile(await submitDriverProfile({
        country_code: String(form.get('country_code') || 'uz'),
        license_number: String(form.get('license_number') || '') || null,
        request_woman_mode: form.get('request_woman_mode') === 'on',
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отправить профиль');
    } finally {
      setSaving(false);
    }
  }

  async function submitVehicleForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSaving(true);
    setError(null);
    try {
      await submitVehicle({
        country_code: String(form.get('country_code') || 'uz'),
        brand: String(form.get('brand') || ''),
        model: String(form.get('model') || ''),
        year: Number(form.get('year') || 0) || null,
        color: String(form.get('color') || '') || null,
        plate: String(form.get('plate') || ''),
        capacity: Number(form.get('capacity') || 4),
        vehicle_class: String(form.get('vehicle_class') || 'economy'),
      });
      event.currentTarget.reset();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отправить авто');
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <main className="shell stack">
      <section className="card stack">
        <h1 className="title">Регистрация водителя</h1>
        <p className="subtitle">Профиль и авто уходят на админскую проверку через Backend V2.</p>
        {error ? <p className="error">{error}</p> : null}
      </section>

      <section className="card stack">
        <h2 className="title" style={{ fontSize: 22 }}>Профиль водителя</h2>
        {loading ? <p className="subtitle">Загрузка...</p> : null}
        {profile ? <p className="badge">status: {profile.status} · special: {profile.woman_driver_status}</p> : <p className="subtitle">Профиль ещё не отправлен.</p>}
        <form className="stack" onSubmit={submitProfile}>
          <div className="grid grid-2">
            <label className="label">Страна<input className="input" name="country_code" defaultValue={profile?.country_code || 'uz'} /></label>
            <label className="label">Номер лицензии<input className="input" name="license_number" defaultValue={profile?.license_number || ''} /></label>
          </div>
          <label className="label"><span><input name="request_woman_mode" type="checkbox" /> Запросить отдельный режим допуска</span></label>
          <button className="button" type="submit" disabled={saving}>{saving ? 'Отправляем...' : 'Отправить профиль'}</button>
        </form>
      </section>

      <section className="card stack">
        <h2 className="title" style={{ fontSize: 22 }}>Автомобиль</h2>
        <form className="stack" onSubmit={submitVehicleForm}>
          <div className="grid grid-2">
            <label className="label">Страна<input className="input" name="country_code" defaultValue="uz" /></label>
            <label className="label">Марка<input className="input" name="brand" required /></label>
            <label className="label">Модель<input className="input" name="model" required /></label>
            <label className="label">Год<input className="input" name="year" inputMode="numeric" /></label>
            <label className="label">Цвет<input className="input" name="color" /></label>
            <label className="label">Номер<input className="input" name="plate" required /></label>
            <label className="label">Мест<input className="input" name="capacity" defaultValue="4" inputMode="numeric" /></label>
            <label className="label">Класс<input className="input" name="vehicle_class" defaultValue="economy" /></label>
          </div>
          <button className="button" type="submit" disabled={saving}>{saving ? 'Отправляем...' : 'Отправить авто'}</button>
        </form>
      </section>

      <section className="grid grid-2">
        {vehicles.map((vehicle) => (
          <article className="card stack" key={vehicle.id}>
            <div className="row"><span className="badge">{vehicle.status}</span><span className="badge">{vehicle.vehicle_class}</span></div>
            <h2 className="title" style={{ fontSize: 22 }}>{vehicle.brand} {vehicle.model}</h2>
            <p className="subtitle">{vehicle.plate} · {vehicle.color || 'цвет не указан'} · {vehicle.capacity} мест</p>
          </article>
        ))}
      </section>
    </main>
  );
}
