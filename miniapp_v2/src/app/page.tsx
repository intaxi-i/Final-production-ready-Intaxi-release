import Link from "next/link";
import { Car, Gift, Headphones, History, Map, User, Wallet } from "lucide-react";

export default function HomePage() {
  return (
    <main className="shell flex flex-col justify-center">
      <section className="premium-hero mb-5">
        <div className="relative z-10">
          <p className="mb-3 text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">Telegram Mini App</p>
          <h1 className="brand-wordmark" aria-label="Intaxi">
            <span className="brand-in">In</span><span className="brand-taxi">taxi</span>
          </h1>
          <p className="mt-4 max-w-[300px] text-sm font-bold leading-relaxed text-slate-500">
            Премиальный сервис поездок: пассажир и водитель могут предлагать свою цену.
          </p>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-4">
        <Link href="/city/create" className="nav-card">
          <div className="nav-icon"><Map size={24} /></div>
          <div>
            <p className="text-xl font-black tracking-[-0.04em] text-slate-950">Заказать</p>
            <p className="nav-label mt-1">City ride</p>
          </div>
        </Link>

        <Link href="/city/offers" className="nav-card dark">
          <div className="nav-icon"><Car size={24} /></div>
          <div>
            <p className="text-xl font-black tracking-[-0.04em]">Водителю</p>
            <p className="nav-label mt-1">Эфир заказов</p>
          </div>
        </Link>

        <Link href="/city/my-orders" className="it-card flex min-h-[86px] items-center gap-4 active:scale-95 transition">
          <History className="text-brand-yellow" />
          <span className="text-xs font-black uppercase tracking-[0.14em] text-slate-500">История</span>
        </Link>

        <Link href="/account" className="it-card flex min-h-[86px] items-center gap-4 active:scale-95 transition">
          <Wallet className="text-brand-yellow" />
          <span className="text-xs font-black uppercase tracking-[0.14em] text-slate-500">Аккаунт</span>
        </Link>

        <Link href="/profile" className="it-card col-span-2 flex min-h-[82px] items-center justify-between gap-4 active:scale-95 transition">
          <div className="flex items-center gap-4">
            <User className="text-brand-yellow" />
            <span className="text-xs font-black uppercase tracking-[0.14em] text-slate-500">Профиль пользователя</span>
          </div>
          <span className="text-xl font-black text-slate-300">→</span>
        </Link>

        <Link href="/donate" className="it-card flex min-h-[76px] items-center gap-4 active:scale-95 transition">
          <Gift className="text-brand-yellow" />
          <span className="text-xs font-black uppercase tracking-[0.14em] text-slate-500">Донат</span>
        </Link>

        <Link href="/support" className="it-card flex min-h-[76px] items-center gap-4 active:scale-95 transition">
          <Headphones className="text-brand-yellow" />
          <span className="text-xs font-black uppercase tracking-[0.14em] text-slate-500">Поддержка</span>
        </Link>
      </section>
    </main>
  );
}
