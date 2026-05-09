import Link from "next/link";
import { Car, Map, User, Wallet, History } from "lucide-react";

const MENU = [
  { h: "/city/create", l: "Заказать", i: "map", dark: false },
  { h: "/city/offers", l: "Водителю", i: "car", dark: true },
  { h: "/city/my-orders", l: "Заказы", i: "history", dark: false },
  { h: "/wallet", l: "Баланс", i: "wallet", dark: false }
];

export default function HomePage() {
  return (
    <main className="px-6 pt-12 pb-24 min-h-screen flex flex-col font-sans">
      <header className="mb-12">
        <h1 className="text-4xl font-display font-extrabold tracking-tighter uppercase italic">InTaxi</h1>
        <p className="text-slate-400 font-bold text-[11px] uppercase tracking-widest mt-1 opacity-70">Ваша цена — ваши правила</p>
      </header>
      <div className="grid grid-cols-2 gap-4">
        {MENU.map(item => (
          <Link key={item.h} href={item.h} className={`it-card flex flex-col justify-between aspect-square active:scale-95 transition-transform ${item.dark ? "bg-brand-dark text-white border-none" : "bg-white"}`}>
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${item.dark ? "bg-white/10" : "bg-slate-50"}`}>
              {item.i === "map" && <Map className="text-brand-yellow" size={20}/>}
              {item.i === "car" && <Car className="text-brand-yellow" size={20}/>}
              {item.i === "history" && <History size={20} className="text-slate-300"/>}
              {item.i === "wallet" && <Wallet size={20} className="text-slate-300"/>}
            </div>
            <p className="font-display font-extrabold text-[10px] uppercase tracking-[0.2em]">{item.l}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}