'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { Car, CheckCircle2, Globe2, ShieldCheck, UserRound, Users } from 'lucide-react';
import { getMe, updateMe, updateRole } from '@/lib/api';
import { getDriverProfile, getWallet } from '@/lib/api-extra';
import { APP_ROUTES, COUNTRY_OPTIONS, LANGUAGE_OPTIONS } from '@/lib/constants';
import { getTelegramUser } from '@/lib/telegram';
import type { DriverProfile, ProfileGender, UserMe, UserRole, Wallet } from '@/lib/types';

function isConfirmedDriver(profile: DriverProfile | null) {
  if (!profile?.status) return false;
  return ['approved', 'verified', 'active'].includes(profile.status.toLowerCase());
}

function statusText(profile: DriverProfile | null) {
  if (!profile) return 'Профиль водителя не создан';
  if (isConfirmedDriver(profile)) return 'Водитель подтверждён';
  if (profile.status === 'pending') return 'Проверка водителя';
  if (profile.status === 'rejected') return 'Заявка водителя отклонена';
  return `Статус водителя: ${profile.status}`;
}

export default function ProfilePage() {
  const [me, setMe] = useState<UserMe | null>(null);
  const [driverProfile, setDriverProfile] = useState<DriverProfile | null>(null);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const tgUser = typeof window !== 'undefined' ? getTelegramUser() : null;

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const [user, profile, walletData] = await Promise.all([
        getMe(),
        getDriverProfile().catch(() => null),
        getWallet().catch(() => null),
      ]);
      setMe(user);
      setDriverProfile(profile);
      setWallet(walletData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить профиль');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const avatarUrl = useMemo(() => me?.photo_url || tgUser?.photo_url || '', [me?.photo_url, tgUser?.photo_url]);
  const name = me?.full_name || [tgUser?.first_name, tgUser?.last_name].filter(Boolean).join(' ') || 'Пользователь';
  const username = me?.username || tgUser?.username || '';
  const confirmedDriver = isConfirmedDriver(driverProfile);
  const activeRole = me?.active_role || 'passenger';

  async function setRole(role: UserRole) {
    setSaving(true);
    setError(null);
    try {
      setMe(await updateRole(role));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сменить режим');
    } finally {
      setSaving(false);
    }
  }

  async function saveProfile(patch: { language?: string; country_code?: string | null; profile_gender?: ProfileGender }) {
    setSaving(true);
    setError(null);
    try {
      setMe(await updateMe(patch));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить настройки');
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero text-center">
        <div className="relative z-10 mx-auto mb-5 flex h-24 w-24 items-center justify-center overflow-hidden rounded-[32px] bg-slate-950 text-white shadow-[0_16px_36px_rgba(15,23,42,0.18)]">
          {avatarUrl ? <Image src={avatarUrl} alt={name} fill sizes="96px" className="object-cover" /> : <UserRound size={40} />}
        </div>
        <div className="relative z-10">
          <h1 className="title">{name}</h1>
          <p className="subtitle mt-1">{username ? `@${username}` : 'Telegram пользователь'}</p>
          <div className="mt-4 inline-flex rounded-full bg-brand-yellow px-4 py-2 text-xs font-black text-brand-dark">★ {me?.rating ?? 0} · {me?.rating_count ?? 0} оценок</div>
        </div>
      </section>

      {error ? <p className="error">{error}</p> : null}
      {loading ? <section className="card"><p className="subtitle">Загрузка профиля...</p></section> : null}

      <section className="card stack">
        <div className="row">
          <div>
            <p className="metric-label">Режим</p>
            <h2 className="title" style={{ fontSize: 22 }}>Как вы используете Intaxi?</h2>
          </div>
          <Users className="text-brand-yellow" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <button type="button" className={`min-h-[86px] rounded-3xl p-4 text-left transition active:scale-95 ${activeRole === 'passenger' ? 'bg-brand-dark text-white' : 'bg-slate-50 text-slate-950'}`} disabled={saving} onClick={() => setRole('passenger')}>
            <span className="block text-base font-black">Пассажир</span>
            <small className="mt-1 block text-xs font-bold opacity-70">Заказывать поездки</small>
          </button>
          <button type="button" className={`min-h-[86px] rounded-3xl p-4 text-left transition active:scale-95 ${activeRole === 'driver' ? 'bg-brand-yellow text-brand-dark' : 'bg-slate-50 text-slate-950'}`} disabled={saving} onClick={() => setRole('driver')}>
            <span className="block text-base font-black">Водитель</span>
            <small className="mt-1 block text-xs font-bold opacity-70">Принимать заказы</small>
          </button>
        </div>
      </section>

      {activeRole === 'driver' ? (
        <section className="card stack">
          <div className="row">
            <div>
              <p className="metric-label">Водитель</p>
              <h2 className="title" style={{ fontSize: 22 }}>{statusText(driverProfile)}</h2>
            </div>
            {confirmedDriver ? <CheckCircle2 className="text-brand-yellow" /> : <ShieldCheck className="text-slate-300" />}
          </div>
          {confirmedDriver ? <Link href={APP_ROUTES.cityOffers} className="button primary">Эфир заказов</Link> : <Link href="/driver/register" className="button secondary">Подать заявку водителя</Link>}
          <Link href="/driver/online" className="button secondary">Онлайн-статус</Link>
        </section>
      ) : (
        <section className="grid grid-2">
          <Link href={APP_ROUTES.cityCreate} className="intercity-action primary"><Car size={22} /><div><strong>Город</strong><span>Создать заказ</span></div></Link>
          <Link href={APP_ROUTES.intercity} className="intercity-action"><Globe2 size={22} /><div><strong>Межгород</strong><span>Дальняя поездка</span></div></Link>
        </section>
      )}

      <section className="card stack">
        <div><p className="metric-label">Настройки</p><h2 className="title" style={{ fontSize: 22 }}>Язык, страна, женский режим</h2></div>
        <div className="grid grid-2">
          <label className="label">Язык<select className="select" value={me?.language || 'ru'} onChange={(event) => saveProfile({ language: event.target.value })} disabled={saving}>{LANGUAGE_OPTIONS.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}</select></label>
          <label className="label">Страна<select className="select" value={me?.country_code || 'uz'} onChange={(event) => saveProfile({ country_code: event.target.value })} disabled={saving}>{COUNTRY_OPTIONS.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}</select></label>
        </div>
        <div className="row rounded-3xl bg-slate-50 p-4">
          <div><strong>Женский режим</strong><p className="subtitle mt-1">Фильтр поездок women-mode.</p></div>
          <button type="button" className={`rounded-2xl px-4 py-3 text-xs font-black ${me?.profile_gender === 'woman' ? 'bg-brand-yellow text-brand-dark' : 'bg-white text-slate-700'}`} disabled={saving} onClick={() => saveProfile({ profile_gender: me?.profile_gender === 'woman' ? 'unspecified' : 'woman' })}>{me?.profile_gender === 'woman' ? 'Включён' : 'Выключен'}</button>
        </div>
      </section>

      <section className="metric-grid">
        <div className="metric-card"><div className="metric-label">Баланс</div><div className="metric-value">{wallet ? `${wallet.balance} ${wallet.currency || ''}` : '—'}</div></div>
        <div className="metric-card"><div className="metric-label">Hold</div><div className="metric-value">{wallet?.hold_balance ?? 0}</div></div>
      </section>
    </main>
  );
}
