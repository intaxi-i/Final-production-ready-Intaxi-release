'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { Car, CheckCircle2, Globe2, ShieldCheck, UserRound, Users } from 'lucide-react';
import { getMe, updateMe, updateRole } from '@/lib/api';
import { getDriverProfile, getWallet } from '@/lib/api-extra';
import { APP_ROUTES, LANGUAGE_OPTIONS } from '@/lib/constants';
import { getWorldCountryOptions } from '@/lib/world-countries';
import { getTelegramUser } from '@/lib/telegram';
import type { DriverProfile, ProfileGender, UserMe, UserRole, Wallet } from '@/lib/types';

type ProfileText = {
  telegramUser: string;
  ratings: string;
  loadingProfile: string;
  profileLoadFailed: string;
  switchRoleFailed: string;
  saveFailed: string;
  roleLabel: string;
  roleTitle: string;
  passenger: string;
  driver: string;
  passengerHint: string;
  driverHint: string;
  driverSection: string;
  driverProfileMissing: string;
  driverApproved: string;
  driverPending: string;
  driverRejected: string;
  driverUnknown: string;
  cityAir: string;
  applyDriver: string;
  onlineStatus: string;
  city: string;
  createOrder: string;
  intercity: string;
  longTrip: string;
  settings: string;
  settingsTitle: string;
  language: string;
  country: string;
  womenMode: string;
  womenModeHint: string;
  enabled: string;
  disabled: string;
  balance: string;
  hold: string;
};

const PROFILE_TEXT: Record<string, ProfileText> = {
  ru: {
    telegramUser: 'Telegram пользователь',
    ratings: 'оценок',
    loadingProfile: 'Загрузка профиля...',
    profileLoadFailed: 'Не удалось загрузить профиль',
    switchRoleFailed: 'Не удалось сменить режим',
    saveFailed: 'Не удалось сохранить настройки',
    roleLabel: 'Режим',
    roleTitle: 'Как вы используете Intaxi?',
    passenger: 'Пассажир',
    driver: 'Водитель',
    passengerHint: 'Заказывать поездки',
    driverHint: 'Принимать заказы',
    driverSection: 'Водитель',
    driverProfileMissing: 'Профиль водителя не создан',
    driverApproved: 'Водитель подтверждён',
    driverPending: 'Проверка водителя',
    driverRejected: 'Заявка водителя отклонена',
    driverUnknown: 'Неизвестный статус водителя',
    cityAir: 'Эфир заказов',
    applyDriver: 'Подать заявку водителя',
    onlineStatus: 'Онлайн-статус',
    city: 'Город',
    createOrder: 'Создать заказ',
    intercity: 'Межгород',
    longTrip: 'Дальняя поездка',
    settings: 'Настройки',
    settingsTitle: 'Язык, страна, женский режим',
    language: 'Язык',
    country: 'Страна',
    womenMode: 'Женский режим',
    womenModeHint: 'Показывает, что вы предпочитаете поездки в женском режиме. Фактический подбор зависит от серверной фильтрации.',
    enabled: 'Включён',
    disabled: 'Выключен',
    balance: 'Баланс',
    hold: 'Hold',
  },
  en: {
    telegramUser: 'Telegram user',
    ratings: 'ratings',
    loadingProfile: 'Loading profile...',
    profileLoadFailed: 'Could not load profile',
    switchRoleFailed: 'Could not switch mode',
    saveFailed: 'Could not save settings',
    roleLabel: 'Mode',
    roleTitle: 'How do you use Intaxi?',
    passenger: 'Passenger',
    driver: 'Driver',
    passengerHint: 'Order rides',
    driverHint: 'Accept orders',
    driverSection: 'Driver',
    driverProfileMissing: 'Driver profile has not been created',
    driverApproved: 'Driver verified',
    driverPending: 'Driver verification pending',
    driverRejected: 'Driver application rejected',
    driverUnknown: 'Unknown driver status',
    cityAir: 'Order feed',
    applyDriver: 'Apply as driver',
    onlineStatus: 'Online status',
    city: 'City',
    createOrder: 'Create order',
    intercity: 'Intercity',
    longTrip: 'Long trip',
    settings: 'Settings',
    settingsTitle: 'Language, country, women mode',
    language: 'Language',
    country: 'Country',
    womenMode: 'Women mode',
    womenModeHint: 'Shows that you prefer women-mode rides. Actual matching depends on server-side filtering.',
    enabled: 'Enabled',
    disabled: 'Disabled',
    balance: 'Balance',
    hold: 'Hold',
  },
  uz: {
    telegramUser: 'Telegram foydalanuvchisi',
    ratings: 'baho',
    loadingProfile: 'Profil yuklanmoqda...',
    profileLoadFailed: 'Profilni yuklab bo‘lmadi',
    switchRoleFailed: 'Rejimni almashtirib bo‘lmadi',
    saveFailed: 'Sozlamalarni saqlab bo‘lmadi',
    roleLabel: 'Rejim',
    roleTitle: 'Intaxi’dan qanday foydalanasiz?',
    passenger: 'Yo‘lovchi',
    driver: 'Haydovchi',
    passengerHint: 'Safar buyurtma qilish',
    driverHint: 'Buyurtmalarni qabul qilish',
    driverSection: 'Haydovchi',
    driverProfileMissing: 'Haydovchi profili yaratilmagan',
    driverApproved: 'Haydovchi tasdiqlangan',
    driverPending: 'Haydovchi tekshirilmoqda',
    driverRejected: 'Haydovchi arizasi rad etildi',
    driverUnknown: 'Haydovchi holati noma’lum',
    cityAir: 'Buyurtmalar efiri',
    applyDriver: 'Haydovchi arizasini yuborish',
    onlineStatus: 'Online holat',
    city: 'Shahar',
    createOrder: 'Buyurtma yaratish',
    intercity: 'Shaharlararo',
    longTrip: 'Uzoq safar',
    settings: 'Sozlamalar',
    settingsTitle: 'Til, davlat, ayollar rejimi',
    language: 'Til',
    country: 'Davlat',
    womenMode: 'Ayollar rejimi',
    womenModeHint: 'Ayollar rejimidagi safarlarni afzal ko‘rishingizni ko‘rsatadi. Amaldagi tanlash server filtrlashiga bog‘liq.',
    enabled: 'Yoqilgan',
    disabled: 'O‘chirilgan',
    balance: 'Balans',
    hold: 'Hold',
  },
  tr: {
    telegramUser: 'Telegram kullanıcısı',
    ratings: 'puan',
    loadingProfile: 'Profil yükleniyor...',
    profileLoadFailed: 'Profil yüklenemedi',
    switchRoleFailed: 'Mod değiştirilemedi',
    saveFailed: 'Ayarlar kaydedilemedi',
    roleLabel: 'Mod',
    roleTitle: 'Intaxi’yi nasıl kullanıyorsunuz?',
    passenger: 'Yolcu',
    driver: 'Sürücü',
    passengerHint: 'Yolculuk sipariş et',
    driverHint: 'Sipariş kabul et',
    driverSection: 'Sürücü',
    driverProfileMissing: 'Sürücü profili oluşturulmadı',
    driverApproved: 'Sürücü onaylandı',
    driverPending: 'Sürücü kontrol ediliyor',
    driverRejected: 'Sürücü başvurusu reddedildi',
    driverUnknown: 'Bilinmeyen sürücü durumu',
    cityAir: 'Sipariş akışı',
    applyDriver: 'Sürücü başvurusu yap',
    onlineStatus: 'Online durum',
    city: 'Şehir',
    createOrder: 'Sipariş oluştur',
    intercity: 'Şehirler arası',
    longTrip: 'Uzun yolculuk',
    settings: 'Ayarlar',
    settingsTitle: 'Dil, ülke, kadın modu',
    language: 'Dil',
    country: 'Ülke',
    womenMode: 'Kadın modu',
    womenModeHint: 'Kadın modundaki yolculukları tercih ettiğinizi gösterir. Gerçek eşleştirme sunucu filtrelemesine bağlıdır.',
    enabled: 'Açık',
    disabled: 'Kapalı',
    balance: 'Bakiye',
    hold: 'Hold',
  },
  kz: {
    telegramUser: 'Telegram пайдаланушысы',
    ratings: 'баға',
    loadingProfile: 'Профиль жүктелуде...',
    profileLoadFailed: 'Профильді жүктеу мүмкін болмады',
    switchRoleFailed: 'Режимді ауыстыру мүмкін болмады',
    saveFailed: 'Баптауларды сақтау мүмкін болмады',
    roleLabel: 'Режим',
    roleTitle: 'Intaxi-ді қалай қолданасыз?',
    passenger: 'Жолаушы',
    driver: 'Жүргізуші',
    passengerHint: 'Сапарға тапсырыс беру',
    driverHint: 'Тапсырыстарды қабылдау',
    driverSection: 'Жүргізуші',
    driverProfileMissing: 'Жүргізуші профилі жасалмаған',
    driverApproved: 'Жүргізуші расталды',
    driverPending: 'Жүргізуші тексерілуде',
    driverRejected: 'Жүргізуші өтінімі қабылданбады',
    driverUnknown: 'Жүргізуші күйі белгісіз',
    cityAir: 'Тапсырыстар эфирі',
    applyDriver: 'Жүргізушіге өтінім беру',
    onlineStatus: 'Online күй',
    city: 'Қала',
    createOrder: 'Тапсырыс жасау',
    intercity: 'Қалааралық',
    longTrip: 'Ұзақ сапар',
    settings: 'Баптаулар',
    settingsTitle: 'Тіл, ел, әйелдер режимі',
    language: 'Тіл',
    country: 'Ел',
    womenMode: 'Әйелдер режимі',
    womenModeHint: 'Әйелдер режиміндегі сапарларды қалайтыныңызды көрсетеді. Нақты таңдау сервер сүзгісіне байланысты.',
    enabled: 'Қосулы',
    disabled: 'Өшірулі',
    balance: 'Баланс',
    hold: 'Hold',
  },
};

function normalizeLanguage(language?: string | null) {
  const code = String(language || 'ru').toLowerCase().split('-')[0];
  return PROFILE_TEXT[code] ? code : 'ru';
}

function textFor(language?: string | null) {
  return PROFILE_TEXT[normalizeLanguage(language)];
}

function isConfirmedDriver(profile: DriverProfile | null) {
  if (!profile?.status) return false;
  return ['approved', 'verified', 'active'].includes(profile.status.toLowerCase());
}

function statusText(profile: DriverProfile | null, text: ProfileText) {
  if (!profile) return text.driverProfileMissing;
  if (isConfirmedDriver(profile)) return text.driverApproved;
  if (profile.status === 'pending') return text.driverPending;
  if (profile.status === 'rejected') return text.driverRejected;
  return text.driverUnknown;
}

export default function ProfilePage() {
  const [me, setMe] = useState<UserMe | null>(null);
  const [driverProfile, setDriverProfile] = useState<DriverProfile | null>(null);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const tgUser = typeof window !== 'undefined' ? getTelegramUser() : null;
  const text = textFor(me?.language || tgUser?.language_code || 'ru');
  const countryOptions = useMemo(() => getWorldCountryOptions(me?.language || tgUser?.language_code || 'ru'), [me?.language, tgUser?.language_code]);

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
      setError(err instanceof Error ? err.message : text.profileLoadFailed);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const avatarUrl = useMemo(() => me?.photo_url || tgUser?.photo_url || '', [me?.photo_url, tgUser?.photo_url]);
  const name = me?.full_name || [tgUser?.first_name, tgUser?.last_name].filter(Boolean).join(' ') || text.telegramUser;
  const username = me?.username || tgUser?.username || '';
  const confirmedDriver = isConfirmedDriver(driverProfile);
  const activeRole = me?.active_role || 'passenger';

  async function setRole(role: UserRole) {
    setSaving(true);
    setError(null);
    try {
      setMe(await updateRole(role));
    } catch (err) {
      setError(err instanceof Error ? err.message : text.switchRoleFailed);
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
      setError(err instanceof Error ? err.message : text.saveFailed);
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero text-center">
        <div className="relative z-10 mx-auto mb-5 flex h-24 w-24 items-center justify-center overflow-hidden rounded-[32px] bg-slate-950 text-white shadow-[0_16px_36px_rgba(15,23,42,0.18)]">
          {avatarUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={avatarUrl} alt={name} className="h-full w-full object-cover" />
          ) : <UserRound size={40} />}
        </div>
        <div className="relative z-10">
          <h1 className="title">{name}</h1>
          <p className="subtitle mt-1">{username ? `@${username}` : text.telegramUser}</p>
          <div className="mt-4 inline-flex rounded-full bg-brand-yellow px-4 py-2 text-xs font-black text-brand-dark">★ {me?.rating ?? 0} · {me?.rating_count ?? 0} {text.ratings}</div>
        </div>
      </section>

      {error ? <p className="error">{error}</p> : null}
      {loading ? <section className="card"><p className="subtitle">{text.loadingProfile}</p></section> : null}

      <section className="card stack">
        <div className="row">
          <div>
            <p className="metric-label">{text.roleLabel}</p>
            <h2 className="title" style={{ fontSize: 22 }}>{text.roleTitle}</h2>
          </div>
          <Users className="text-brand-yellow" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <button type="button" className={`min-h-[86px] rounded-3xl p-4 text-left transition active:scale-95 ${activeRole === 'passenger' ? 'bg-brand-dark text-white' : 'bg-slate-50 text-slate-950'}`} disabled={saving} onClick={() => setRole('passenger')}>
            <span className="block text-base font-black">{text.passenger}</span>
            <small className="mt-1 block text-xs font-bold opacity-70">{text.passengerHint}</small>
          </button>
          <button type="button" className={`min-h-[86px] rounded-3xl p-4 text-left transition active:scale-95 ${activeRole === 'driver' ? 'bg-brand-yellow text-brand-dark' : 'bg-slate-50 text-slate-950'}`} disabled={saving} onClick={() => setRole('driver')}>
            <span className="block text-base font-black">{text.driver}</span>
            <small className="mt-1 block text-xs font-bold opacity-70">{text.driverHint}</small>
          </button>
        </div>
      </section>

      {activeRole === 'driver' ? (
        <section className="card stack">
          <div className="row">
            <div>
              <p className="metric-label">{text.driverSection}</p>
              <h2 className="title" style={{ fontSize: 22 }}>{statusText(driverProfile, text)}</h2>
            </div>
            {confirmedDriver ? <CheckCircle2 className="text-brand-yellow" /> : <ShieldCheck className="text-slate-300" />}
          </div>
          {confirmedDriver ? <Link href={APP_ROUTES.cityOffers} className="button primary">{text.cityAir}</Link> : <Link href="/driver/register" className="button secondary">{text.applyDriver}</Link>}
          <Link href="/driver/online" className="button secondary">{text.onlineStatus}</Link>
        </section>
      ) : (
        <section className="grid grid-2">
          <Link href={APP_ROUTES.cityCreate} className="intercity-action primary"><Car size={22} /><div><strong>{text.city}</strong><span>{text.createOrder}</span></div></Link>
          <Link href={APP_ROUTES.intercity} className="intercity-action"><Globe2 size={22} /><div><strong>{text.intercity}</strong><span>{text.longTrip}</span></div></Link>
        </section>
      )}

      <section className="card stack">
        <div><p className="metric-label">{text.settings}</p><h2 className="title" style={{ fontSize: 22 }}>{text.settingsTitle}</h2></div>
        <div className="grid grid-2">
          <label className="label">{text.language}<select className="select" value={me?.language || 'ru'} onChange={(event) => saveProfile({ language: event.target.value })} disabled={saving}>{LANGUAGE_OPTIONS.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}</select></label>
          <label className="label">{text.country}<select className="select" value={me?.country_code || 'uz'} onChange={(event) => saveProfile({ country_code: event.target.value })} disabled={saving}>{countryOptions.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}</select></label>
        </div>
        <div className="row rounded-3xl bg-slate-50 p-4">
          <div><strong>{text.womenMode}</strong><p className="subtitle mt-1">{text.womenModeHint}</p></div>
          <button type="button" className={`rounded-2xl px-4 py-3 text-xs font-black ${me?.profile_gender === 'woman' ? 'bg-brand-yellow text-brand-dark' : 'bg-white text-slate-700'}`} disabled={saving} onClick={() => saveProfile({ profile_gender: me?.profile_gender === 'woman' ? 'unspecified' : 'woman' })}>{me?.profile_gender === 'woman' ? text.enabled : text.disabled}</button>
        </div>
      </section>

      <section className="metric-grid">
        <div className="metric-card"><div className="metric-label">{text.balance}</div><div className="metric-value">{wallet ? `${wallet.balance} ${wallet.currency || ''}` : '—'}</div></div>
        <div className="metric-card"><div className="metric-label">{text.hold}</div><div className="metric-value">{wallet?.hold_balance ?? 0}</div></div>
      </section>
    </main>
  );
}
