"use client";
import { useEffect, useState } from "react";
import { getMe, updateRole } from "@/lib/api";
export default function ProfilePage() {
  const [me, setMe] = useState<any>(null);
  useEffect(() => { getMe().then(setMe); }, []);
  return (
    <main className="justify-center">
      <header className="mb-10 text-center"><h1 className="text-3xl font-black uppercase italic">Профиль</h1></header>
      <div className="it-card p-10 text-center">
        <div className="w-24 h-24 bg-brand-yellow rounded-[32px] mx-auto mb-6 flex items-center justify-center text-3xl font-black text-white shadow-xl shadow-yellow-400/30">{me?.full_name?.[0]}</div>
        <h2 className="text-2xl font-black mb-2">{me?.full_name}</h2>
        <p className="text-brand-yellow font-black">★ {me?.rating}</p>
      </div>
      <div className="grid grid-cols-2 gap-4 mt-8 w-full">
        <button onClick={() => updateRole("passenger").then(() => window.location.reload())} className="it-btn bg-brand-dark text-white">Пассажир</button>
        <button onClick={() => updateRole("driver").then(() => window.location.reload())} className="it-btn bg-brand-yellow text-slate-900">Водитель</button>
      </div>
    </main>
  );
}