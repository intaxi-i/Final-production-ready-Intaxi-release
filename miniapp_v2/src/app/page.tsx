import Link from "next/link";
import { Car, Map, User, Wallet, History } from "lucide-react";

export default function HomePage() {
  return (
    <main className="justify-center">
      <header className="mb-12 text-center">
        <h1 className="text-5xl font-black tracking-tighter italic">
          <span className="text-brand-yellow tracking-tighter">In</span>taxi
        </h1>
      </header>

      <div className="w-full max-w-[400px] grid grid-cols-2 gap-4">
        <Link href="/city/create" className="it-card aspect-square flex flex-col justify-between active:scale-95 transition-all">
          <div className="w-12 h-12 bg-slate-50 rounded-2xl flex items-center justify-center text-brand-yellow shadow-inner"><Map size={24}/></div>
          <p className="font-black text-[12px] uppercase tracking-widest text-slate-400">Заказать</p>
        </Link>
        <Link href="/city/offers" className="it-card bg-brand-dark text-white aspect-square flex flex-col justify-between border-none active:scale-95 transition-all">
          <div className="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center text-brand-yellow"><Car size={24}/></div>
          <p className="font-black text-[12px] uppercase tracking-widest opacity-60">Водителю</p>
        </Link>
        <Link href="/city/my-orders" className="it-card h-[80px] col-span-1 flex items-center gap-4 active:scale-95 transition-all">
          <History className="text-slate-200"/> <span className="font-black text-[10px] uppercase tracking-widest text-slate-400">История</span>
        </Link>
        <Link href="/wallet" className="it-card h-[80px] col-span-1 flex items-center gap-4 active:scale-95 transition-all">
          <Wallet className="text-slate-200"/> <span className="font-black text-[10px] uppercase tracking-widest text-slate-400">Кошелек</span>
        </Link>
        <Link href="/profile" className="it-card h-[80px] col-span-2 flex items-center justify-center gap-4 active:scale-95 transition-all">
          <User className="text-slate-200"/> <span className="font-black text-[10px] uppercase tracking-widest text-slate-400">Профиль пользователя</span>
        </Link>
      </div>
    </main>
  );
}