'use client';

import { useEffect, useState } from 'react';
import { getWallet, listTopups } from '@/lib/api-extra';
import type { Topup, Wallet } from '@/lib/types';

export default function AccountPage() {
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [items, setItems] = useState<Topup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const [walletData, itemData] = await Promise.all([getWallet(), listTopups()]);
      setWallet(walletData);
      setItems(itemData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить данные');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <main className="shell stack">
      <section className="card stack">
        <div className="row">
          <div>
            <h1 className="title">Аккаунт водителя</h1>
            <p className="subtitle">Баланс и заявки отображаются из Backend V2.</p>
          </div>
          <button className="button secondary" type="button" onClick={load} disabled={loading}>Обновить</button>
        </div>
        {error ? <p className="error">{error}</p> : null}
      </section>

      <section className="card stack">
        <h2 className="title" style={{ fontSize: 22 }}>{wallet ? `${wallet.balance} ${wallet.currency || ''}` : '—'}</h2>
        <p className="subtitle">Hold: {wallet?.hold_balance ?? 0}</p>
      </section>

      <section className="grid grid-2">
        {items.map((item) => (
          <article className="card stack" key={item.id}>
            <div className="row"><span className="badge">#{item.id}</span><span className="badge">{item.status}</span></div>
            <h2 className="title" style={{ fontSize: 22 }}>{item.amount} {item.currency}</h2>
            <p className="subtitle">Method: {item.method}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
