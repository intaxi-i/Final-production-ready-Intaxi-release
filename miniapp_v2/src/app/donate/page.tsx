'use client';

import { useState } from 'react';
import { AlertTriangle, Check, Copy, ShieldCheck } from 'lucide-react';
import { BottomNav } from '@/components/BottomNav';
import { DONATION_WALLETS, walletChunks, walletFingerprint } from '@/lib/donation-wallets';

export default function DonatePage() {
  const [activeKey, setActiveKey] = useState(DONATION_WALLETS[0]?.key || '');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const active = DONATION_WALLETS.find((item) => item.key === activeKey) || DONATION_WALLETS[0];

  async function copyAddress(key: string, address: string) {
    await navigator.clipboard.writeText(address);
    setCopiedKey(key);
    window.setTimeout(() => setCopiedKey(null), 2200);
  }

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10 row">
          <div>
            <p className="metric-label">Донат</p>
            <h1 className="title">Поддержать Intaxi</h1>
            <p className="subtitle mt-2">Выберите монету и сеть. Перед отправкой сверяйте адрес, сеть и контрольный код.</p>
          </div>
          <ShieldCheck className="text-brand-yellow" size={34} />
        </div>
      </section>

      <section className="grid grid-cols-2 gap-3">
        {DONATION_WALLETS.map((wallet) => (
          <button key={wallet.key} type="button" className={`donate-chain ${active?.key === wallet.key ? 'active' : ''}`} onClick={() => setActiveKey(wallet.key)}>
            <span>{wallet.asset}</span>
            <small>{wallet.network}</small>
          </button>
        ))}
      </section>

      {active ? (
        <section className="card stack">
          <div className="row">
            <div>
              <p className="metric-label">{active.asset}</p>
              <h2 className="title" style={{ fontSize: 24 }}>{active.title}</h2>
            </div>
            <span className="order-badge">{active.network}</span>
          </div>

          {active.warning ? <p className="error">{active.warning}</p> : null}

          <div className="wallet-box">
            <p className="metric-label">Адрес</p>
            <code>{walletChunks(active.address)}</code>
          </div>

          <section className="metric-grid">
            <div className="metric-card">
              <div className="metric-label">Проверка</div>
              <div className="metric-value">{walletFingerprint(active.address)}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Код</div>
              <div className="metric-value">{active.checksum}</div>
            </div>
          </section>

          <button type="button" className="button primary full-submit" onClick={() => copyAddress(active.key, active.address)}>
            {copiedKey === active.key ? <Check size={18} /> : <Copy size={18} />}
            {copiedKey === active.key ? 'Скопировано' : 'Скопировать адрес'}
          </button>

          <div className="card-soft row">
            <div>
              <strong>Проверка перед отправкой</strong>
              <p className="subtitle mt-1">После вставки в кошелёк сверяйте первые 8 и последние 8 символов. Если адрес в кошельке отличается — не отправляйте.</p>
            </div>
            <AlertTriangle className="text-brand-yellow" />
          </div>

          <div className="card-soft">
            <strong>Защита от подмены</strong>
            <p className="subtitle mt-1">Адреса зашиты в клиентский код и отображаются полностью. Контрольный код нужен для ручной сверки с официальным экраном Intaxi.</p>
          </div>
        </section>
      ) : null}
      <BottomNav />
    </main>
  );
}
