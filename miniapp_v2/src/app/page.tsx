import Link from "next/link";
import { Car, Map, User, Wallet } from "lucide-react";
export default function HomePage() {
  return (
    <main className="p-6">
      <header className="mb-10 mt-4">
        <div className="bg-brand-yellow w-12 h-12 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-yellow-400/30"><Car size={24}/></div>
        <h1 className="text-4xl font-black tracking-tighter font-display">InTaxi <span className="text-brand-yellow">V2</span></h1>
        <p className="text-slate-400 font-medium italic">Premium Ride-Sharing</p>
      </header>
      <div className="grid grid-cols-2 gap-4">
        <Link href="/city/create" className="bg-white p-6 rounded-[2rem] shadow-premium flex flex-col gap-8 active:scale-95 transition-all">
          <div className="w-10 h-10 bg-slate-50 rounded-xl flex items-center justify-center"><Map className="text-brand-yellow"/></div>
          <p className="font-bold text-xs uppercase tracking-widest">Заказать</p>
        </Link>
        <Link href="/city/offers" className="bg-slate-900 text-white p-6 rounded-[2rem] shadow-premium flex flex-col gap-8 active:scale-95 transition-all">
          <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center"><Car className="text-brand-yellow"/></div>
          <p className="font-bold text-xs uppercase tracking-widest">Водителю</p>
        </Link>
      </div>
    </main>
  )
}