'use client';

import { FormEvent, useEffect, useState } from 'react';
import { CarFront, CheckCircle2, FileCheck2, ShieldCheck } from 'lucide-react';
import { BottomNav } from '@/components/BottomNav';
import { getDriverProfile, listVehicles, submitDriverProfile, submitVehicle } from '@/lib/api-extra';
import { COUNTRY_OPTIONS } from '@/lib/constants';
import type { DriverProfile, Vehicle } from '@/lib/types';

function statusLabel(status?: string | null) {
  if (!status) return 'Не отправлено';
  if (status === 'pending') return 'На проверке';
  if (['approved', 'verified', 'active'].includes(status)) return 'Подтверждено';
  if (status === 'rejected') return 'Отклонено';
  return status;
}

function vehicleClassLabel(value: string) {
  if (value === 'comfort') return 'Комфорт';
  if (value === 'business') return 'Бизнес';
  if (value === 'minivan') return 'Минивэн';
  return 'Эконом';
}

export default function DriverRegisterPage() {
  const [profile, setProfile] = useState<DriverProfile | null>(null);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const [profileData, vehicleData] = await Promise.all([
        getDriverProfile().catch(() => null),
        listVehicles().catch(() => []),
      ]);
      setProfile(profileData);
      setVehicles(vehicleData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить данные водителя');
    } finally {
      setLoading(false);
    }
  }

  async function submitProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      setProfile(await submitDriverProfile({
        country_code: String(form.get('country_code') || 'uz'),
        license_number: String(form.get('license_number') || '') || null,
        request_woman_mode: form.get('request_woman_mode') === 'on',
      }));
      setMessage('Профиль отправлен на проверку.');
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
    setMessage(null);
    try {
      await submitVehicle({
        country_code: String(form.get('country_code') || profile?.country_code || 'uz'),
        brand: String(form.get('brand') || '').trim(),
        model: String(form.get('model') || '').trim(),
        year: Number(form.get('year') || 0) || null,
        color: String(form.get('color') || '').trim() || null,
        plate: String(form.get('plate') || '').trim(),
        capacity: Number(form.get('capacity') || 4),
        vehicle_class: String(form.get('vehicle_class') || 'economy'),
      });
      event.currentTarget.reset();
      setMessage('Автомобиль отправлен на проверку.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отправить автомобиль');
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
            <p className="metric-label">Водитель</p>
            <h1 className="title">Регистрация</h1>
            <p className="subtitle mt-2">Заполните профиль и данные автомобиля. После проверки откроется эфир заказов.</p>
          </div>
          <ShieldCheck className="text-brand-yellow" size={34} />
        </div>
      </section>

      {error ? <p className="error">{error}</p> : null}
      {message ? <p className="success">{message}</p> : null}

      <section className="metric-grid">
        <div className="metric-card"><div className="metric-label">Профиль</div><div className="metric-value">{loading ? '...' : statusLabel(profile?.status)}</div></div>
        <div className="metric-card"><div className="metric-label">Авто</div><div className="metric-value">{vehicles.length}</div></div>
      </section>

      <section className="card stack">
        <div className="row">
          <div>
            <p className="metric-label">Шаг 1</p>
            <h2 className="title" style={{ fontSize: 22 }}>Профиль водителя</h2>
          </div>
          <FileCheck2 className="text-brand-yellow" />
        </div>
        {profile?.rejection_reason ? <p className="error">{profile.rejection_reason}</p> : null}
        <form className="stack" onSubmit={submitProfile}>
          <div className="grid grid-2">
            <label className="label">Страна
              <select className="select" name="country_code" defaultValue={profile?.country_code || 'uz'}>
                {COUNTRY_OPTIONS.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}
              </select>
            </label>
            <label className="label">Номер лицензии
              <input className="input" name="license_number" defaultValue={profile?.license_number || ''} placeholder="Серия и номер" />
            </label>
          </div>
          <label className="women-setting cursor-pointer">
            <span>
              <strong>Допуск к женскому режиму</strong>
              <p className="subtitle mt-1">Отметьте, если хотите проходить отдельную проверку для women-mode.</p>
            </span>
            <input name="request_woman_mode" type="checkbox" className="h-6 w-6 accent-brand-yellow" defaultChecked={profile?.woman_driver_status === 'pending' || profile?.woman_driver_status === 'approved'} />
          </label>
          <button className="button primary full-submit" type="submit" disabled={saving}>{saving ? 'Отправляем...' : 'Отправить профиль'}</button>
        </form>
      </section>

      <section className="card stack">
        <div className="row">
          <div>
            <p className="metric-label">Шаг 2</p>
            <h2 className="title" style={{ fontSize: 22 }}>Автомобиль</h2>
          </div>
          <CarFront className="text-brand-yellow" />
        </div>
        <form className="stack" onSubmit={submitVehicleForm}>
          <div className="grid grid-2">
            <label className="label">Страна
              <select className="select" name="country_code" defaultValue={profile?.country_code || 'uz'}>
                {COUNTRY_OPTIONS.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}
              </select>
            </label>
            <label className="label">Марка<input className="input" name="brand" placeholder="Chevrolet" required /></label>
            <label className="label">Модель<input className="input" name="model" placeholder="Cobalt" required /></label>
            <label className="label">Год<input className="input" name="year" inputMode="numeric" placeholder="2022" /></label>
            <label className="label">Цвет<input className="input" name="color" placeholder="Белый" /></label>
            <label className="label">Госномер<input className="input" name="plate" placeholder="01 A 123 AA" required /></label>
            <label className="label">Мест<input className="input" name="capacity" defaultValue="4" inputMode="numeric" /></label>
            <label className="label">Класс
              <select className="select" name="vehicle_class" defaultValue="economy">
                <option value="economy">Эконом</option>
                <option value="comfort">Комфорт</option>
                <option value="business">Бизнес</option>
                <option value="minivan">Минивэн</option>
              </select>
            </label>
          </div>
          <button className="button primary full-submit" type="submit" disabled={saving}>{saving ? 'Отправляем...' : 'Отправить автомобиль'}</button>
        </form>
      </section>

      {vehicles.length > 0 ? (
        <section className="stack">
          {vehicles.map((vehicle) => (
            <article className="card stack" key={vehicle.id}>
              <div className="row"><span className="order-badge">{statusLabel(vehicle.status)}</span><span className="order-badge">{vehicleClassLabel(vehicle.vehicle_class)}</span></div>
              <div>
                <h2 className="title" style={{ fontSize: 22 }}>{vehicle.brand} {vehicle.model}</h2>
                <p className="subtitle mt-1">{vehicle.plate} · {vehicle.color || 'цвет не указан'} · {vehicle.capacity} мест</p>
              </div>
              {vehicle.rejection_reason ? <p className="error">{vehicle.rejection_reason}</p> : null}
            </article>
          ))}
        </section>
      ) : null}
      <BottomNav />
    </main>
  );
}
