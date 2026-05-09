import Link from "next/link";
import { Car, Map, User, Wallet, History } from "lucide-react";

export default function HomePage() {
  return (
    <main className="px-8 pt-24 pb-12 min-h-screen flex flex-col justify-between font-sans">
      <header className="flex flex-col items-center">
        <div className="w-16 h-16 bg-brand-yellow rounded-2xl flex items-center justify-center mb-6 shadow-xl shadow-yellow-400/30">
          <Car size={32} />
        </div>
        <h1 className="text-5xl font-black tracking-tighter leading-none">
          <span className="text-brand-yellow tracking-[-0.05em]">In</span>taxi
        </h1>
      </header>

      <div className="space-y-4 mb-8">
        <div className="grid grid-cols-2 gap-4">
          <Link href="/city/create" className="it-card flex flex-col justify-between aspect-square active:scale-95 transition-all">
            <div className="w-12 h-12 bg-slate-50 rounded-2xl flex items-center justify-center text-brand-yellow"><Map size={24}/></div>
            <p className="font-extrabold text-[14px] uppercase tracking-widest text-slate-400">Заказать</p>
          </Link>
          <Link href="/city/offers" className="it-card bg-brand-dark text-white flex flex-col justify-between aspect-square active:scale-95 transition-all border-none">
            <div className="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center text-brand-yellow"><Car size={24}/></div>
            <p className="font-extrabold text-[14px] uppercase tracking-widest opacity-60">Водителю</p>
          </Link>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Link href="/city/my-orders" className="it-card flex flex-col justify-between p-5 active:scale-95 transition-all">
            <History className="text-slate-200" />
            <p className="font-extrabold text-[12px] uppercase tracking-widest text-slate-400">История</p>
          </Link>
          <Link href="/wallet" className="it-card flex flex-col justify-between p-5 active:scale-95 transition-all">
            <Wallet className="text-slate-200" />
            <p className="font-extrabold text-[12px] uppercase tracking-widest text-slate-400">Кошелек</p>
          </Link>
        </div>
      </div>
    </main>
  );
}