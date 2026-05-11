'use client';

import { useState } from 'react';
import { Check, Copy } from 'lucide-react';
import { DONATION_WALLETS, walletFingerprint } from '@/lib/donation-wallets';

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
    <main className="shell stack">
      <section className="premium-hero">
        <div className="relative z-10">
          <h1 className="title">Поддержать Intaxi</h1>
          <p className="subtitle mt-2">Выберите сеть, скопируйте адрес и проверьте первые и последние символы.</p>
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
            <code>{active.address}</code>
            <p className="subtitle">Проверка: {walletFingerprint(active.address)}</p>
          </div>
          <button type="button" className="button primary" onClick={() => copyAddress(active.key, active.address)}>
            {copiedKey === active.key ? <Check size={18} /> : <Copy size={18} />}
            {copiedKey === active.key ? 'Скопировано' : 'Скопировать адрес'}
          </button>
          <div className="card-soft">
            <strong>Важно</strong>
            <p className="subtitle mt-1">Сверьте адрес в кошельке с проверкой выше. Для USDT выберите сеть TRC20.</p>
          </div>
        </section>
      ) : null}
    </main>
  );
}
