'use client';

import { FormEvent, useEffect, useState } from 'react';
import { CreditCard, RefreshCw, WalletCards } from 'lucide-react';
import { BottomNav } from '@/components/BottomNav';
import { createTopup, getWallet, listTopups } from '@/lib/api-extra';
import type { Topup, Wallet } from '@/lib/types';

function formatAmount(value?: number | null, currency?: string | null) {
  if (typeof value !== 'number') return '—';
  return `${value.toLocaleString('ru-RU')} ${currency || ''}`.trim();
}

export default function AccountPage() {
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [items, setItems] = useState<Topup[]>([]);
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('UZS');
  const [method, setMethod] = useState('card');
  const [receipt, setReceipt] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const [walletData, itemData] = await Promise.all([
        getWallet().catch(() => null),
        listTopups().catch(() => []),
      ]);
      setWallet(walletData);
      setItems(itemData);
      if (walletData?.currency) setCurrency(walletData.currency);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить кошелёк');
    } finally {
      setLoading(false);
    }
  }

  async function submitTopup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);

    const numericAmount = Number(amount);
    if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
      setError('Укажите сумму пополнения.');
      return;
    }

    setSubmitting(true);
    try {
      await createTopup({
        amount: numericAmount,
        currency,
        method,
        receipt_file_id: receipt.trim() || null,
      });
      setAmount('');
      setReceipt('');
      setMessage('Заявка на пополнение отправлена. После проверки баланс обновится.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отправить заявку');
    } finally {
      setSubmitting(false);
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">Кошелёк</p>
            <h1 className="title">Баланс водителя</h1>
            <p className="subtitle mt-2">Пополнения проходят проверку. Активный баланс используется для комиссий и поездок.</p>
          </div>
          <button className="button secondary !min-h-[48px] !px-4" type="button" onClick={load} disabled={loading} aria-label="Обновить">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </section>

      {error ? <p className="error">{error}</p> : null}
      {message ? <p className="success">{message}</p> : null}

      <section className="metric-grid">
        <div className="metric-card">
          <div className="metric-label">Доступно</div>
          <div className="metric-value">{formatAmount(wallet?.balance, wallet?.currency)}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">В удержании</div>
          <div className="metric-value">{formatAmount(wallet?.hold_balance, wallet?.currency)}</div>
        </div>
      </section>

      <form className="card stack" onSubmit={submitTopup}>
        <div className="row">
          <div>
            <p className="metric-label">Пополнение</p>
            <h2 className="title" style={{ fontSize: 22 }}>Создать заявку</h2>
          </div>
          <WalletCards className="text-brand-yellow" />
        </div>
        <div className="grid grid-2">
          <label className="label">Сумма
            <input className="input price-input" inputMode="numeric" value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="100000" required />
          </label>
          <label className="label">Валюта
            <select className="select" value={currency} onChange={(event) => setCurrency(event.target.value)}>
              <option value="UZS">UZS</option>
              <option value="KZT">KZT</option>
              <option value="TRY">TRY</option>
              <option value="SAR">SAR</option>
              <option value="USD">USD</option>
            </select>
          </label>
        </div>
        <label className="label">Способ оплаты
          <select className="select" value={method} onChange={(event) => setMethod(event.target.value)}>
            <option value="card">Карта</option>
            <option value="bank_transfer">Банковский перевод</option>
            <option value="cash">Наличные</option>
            <option value="crypto">Криптовалюта</option>
          </select>
        </label>
        <label className="label">ID/номер чека, если есть
          <input className="input" value={receipt} onChange={(event) => setReceipt(event.target.value)} placeholder="Номер операции или комментарий" />
        </label>
        <button className="button primary full-submit" type="submit" disabled={submitting}>{submitting ? 'Отправляем...' : 'Отправить заявку'}</button>
      </form>

      <section className="card stack">
        <div className="row">
          <div>
            <p className="metric-label">История</p>
            <h2 className="title" style={{ fontSize: 22 }}>Пополнения</h2>
          </div>
          <CreditCard className="text-brand-yellow" />
        </div>
        {loading ? <p className="subtitle">Загрузка...</p> : null}
        {!loading && items.length === 0 ? <p className="subtitle">Заявок на пополнение пока нет.</p> : null}
        <div className="stack">
          {items.map((item) => (
            <article className="card-soft" key={item.id}>
              <div className="row">
                <strong>#{item.id}</strong>
                <span className="order-badge">{item.status}</span>
              </div>
              <h3 className="title mt-3" style={{ fontSize: 22 }}>{item.amount.toLocaleString('ru-RU')} {item.currency}</h3>
              <p className="subtitle mt-1">Способ: {item.method}</p>
              {item.rejection_reason ? <p className="error mt-3">{item.rejection_reason}</p> : null}
            </article>
          ))}
        </div>
      </section>
      <BottomNav />
    </main>
  );
}
