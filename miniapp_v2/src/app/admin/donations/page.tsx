'use client';

import { useEffect, useState } from 'react';
import { Gift, Network, RefreshCw, ShieldCheck } from 'lucide-react';
import { listAdminDonationPaymentSettings, updateAdminDonationPaymentSetting } from '@/lib/api';
import type { DonationPaymentSetting } from '@/lib/types';

function statusLabel(active: boolean) {
  return active ? 'Включено' : 'Отключено';
}

function methodLabel(value: string) {
  if (value === 'crypto') return 'Криптовалюта';
  if (value === 'card') return 'Карта';
  if (value === 'bank_transfer') return 'Банковский перевод';
  if (value === 'cash') return 'Наличные';
  return 'Неизвестный способ';
}

function scopeLabel(country: string | null, currency: string | null) {
  const countryPart = country ? country.toUpperCase() : 'Все страны';
  const currencyPart = currency || 'любая валюта';
  return `${countryPart} · ${currencyPart}`;
}

export default function AdminSupportSettingsPage() {
  const [items, setItems] = useState<DonationPaymentSetting[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      setItems(await listAdminDonationPaymentSettings());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить настройки');
    } finally {
      setLoading(false);
    }
  }

  async function toggle(item: DonationPaymentSetting) {
    setSavingId(item.id);
    setError(null);
    try {
      await updateAdminDonationPaymentSetting(item.id, { is_active: !item.is_active });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось изменить статус');
    } finally {
      setSavingId(null);
    }
  }

  useEffect(() => { load(); }, []);

  const activeCount = items.filter((item) => item.is_active).length;
  const cryptoCount = items.filter((item) => item.method_type === 'crypto').length;

  return (
    <main className="shell stack">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">Админ · донаты</p>
            <h1 className="title">Реквизиты поддержки</h1>
            <p className="subtitle mt-2">Управляйте видимостью способов поддержки проекта. Публичный экран показывает только включённые реквизиты.</p>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={load} disabled={loading} aria-label="Обновить">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {error ? <p className="error mt-4">{error}</p> : null}
      </section>

      <section className="metric-grid">
        <div className="metric-card"><div className="metric-label">Всего</div><div className="metric-value">{items.length}</div></div>
        <div className="metric-card"><div className="metric-label">Включено</div><div className="metric-value">{activeCount}</div></div>
        <div className="metric-card"><div className="metric-label">Крипто</div><div className="metric-value">{cryptoCount}</div></div>
        <div className="metric-card"><div className="metric-label">Безопасность</div><div className="metric-value">Ручная проверка</div></div>
      </section>

      {loading ? <section className="card"><p className="subtitle">Загрузка...</p></section> : null}
      {!loading && items.length === 0 ? <section className="card"><p className="subtitle">Настройки донатов пока не созданы.</p></section> : null}

      <section className="grid grid-2">
        {items.map((item) => (
          <article className="card stack" key={item.id}>
            <div className="row">
              <span className="order-badge">{methodLabel(item.method_type)}</span>
              <span className={`order-badge ${item.is_active ? 'bg-brand-yellow text-brand-dark' : ''}`}>{statusLabel(item.is_active)}</span>
            </div>
            <div>
              <h2 className="title" style={{ fontSize: 22 }}>{item.title}</h2>
              <p className="subtitle mt-1">{scopeLabel(item.country_code, item.currency)}</p>
            </div>
            <div className="card-soft stack">
              <div className="row">
                <div>
                  <p className="metric-label">Сеть</p>
                  <strong>{item.digital_asset_network || 'не указана'}</strong>
                </div>
                <Network className="text-brand-yellow" />
              </div>
              <div>
                <p className="metric-label">Адрес / карта</p>
                <p className="subtitle break-all">{item.digital_asset_address_preview || item.card_number_masked || 'не указано'}</p>
              </div>
              {item.instructions ? <p className="subtitle">{item.instructions}</p> : null}
            </div>
            <button className={item.is_active ? 'button secondary' : 'button primary'} type="button" disabled={savingId === item.id} onClick={() => toggle(item)}>
              {item.is_active ? 'Отключить' : 'Включить'}
            </button>
          </article>
        ))}
      </section>

      <section className="card-soft row">
        <div>
          <strong>Контроль реквизитов</strong>
          <p className="subtitle mt-1">После изменения реквизитов обязательно сверяйте публичный экран донатов и контрольные символы адресов.</p>
        </div>
        <ShieldCheck className="text-brand-yellow" />
      </section>
    </main>
  );
}
