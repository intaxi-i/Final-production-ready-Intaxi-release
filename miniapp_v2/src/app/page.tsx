"use client";

import Link from "next/link";
import { Car, Gift, Headphones, History, Map, Route, User } from "lucide-react";
import { useEffect, useState } from "react";
import { getMe } from "@/lib/api";
import { getDriverProfile } from "@/lib/api-extra";
import { APP_ROUTES } from "@/lib/constants";
import type { DriverProfile, UserMe } from "@/lib/types";

function isConfirmedDriver(profile: DriverProfile | null) {
  if (!profile?.status) return false;
  return ["approved", "verified", "active"].includes(profile.status.toLowerCase());
}

export default function HomePage() {
  const [me, setMe] = useState<UserMe | null>(null);
  const [driverProfile, setDriverProfile] = useState<DriverProfile | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const user = await getMe();
        if (cancelled) return;
        setMe(user);
        if (user.active_role === "driver") {
          const profile = await getDriverProfile().catch(() => null);
          if (!cancelled) setDriverProfile(profile);
        }
      } catch {
        // The home screen must stay usable even if profile loading fails.
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const showDriverFeed = me?.active_role === "driver" && isConfirmedDriver(driverProfile);

  return (
    <main className="shell flex flex-col justify-center">
      <section className="premium-hero mb-5">
        <div className="relative z-10">
          <h1 className="brand-wordmark" aria-label="Intaxi">
            <span className="brand-in">In</span><span className="brand-taxi">taxi</span>
          </h1>
          <p className="mt-4 text-xl font-black tracking-[-0.04em] text-slate-950">
            Предлагай свою цену!
          </p>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-4">
        <Link href="/city/create" className="nav-card bg-brand-yellow text-brand-dark border-none shadow-[0_18px_42px_rgba(255,196,0,0.24)]">
          <div className="nav-icon bg-white/80 text-brand-dark"><Map size={24} /></div>
          <div>
            <p className="text-xl font-black tracking-[-0.04em]">Город</p>
            <p className="mt-1 text-xs font-black uppercase tracking-[0.16em] text-slate-700">Заказать</p>
          </div>
        </Link>

        <Link href={APP_ROUTES.intercity} className="nav-card dark">
          <div className="nav-icon"><Route size={24} /></div>
          <div>
            <p className="text-xl font-black tracking-[-0.04em]">Межгород</p>
            <p className="nav-label mt-1">Направления</p>
          </div>
        </Link>

        {showDriverFeed ? (
          <Link href="/city/offers" className="it-card col-span-2 flex min-h-[86px] items-center justify-between gap-4 border-brand-yellow/40 bg-white active:scale-95 transition">
            <div className="flex items-center gap-4">
              <Car className="text-brand-yellow" />
              <span className="text-xs font-black uppercase tracking-[0.14em] text-slate-700">Эфир заказов</span>
            </div>
            <span className="text-xl font-black text-slate-300">→</span>
          </Link>
        ) : null}

        <Link href="/city/my-orders" className="it-card flex min-h-[86px] items-center gap-4 bg-slate-950 text-white active:scale-95 transition">
          <History className="text-brand-yellow" />
          <span className="text-xs font-black uppercase tracking-[0.14em] text-white/75">История</span>
        </Link>

        <Link href="/profile" className="it-card flex min-h-[86px] items-center gap-4 bg-white active:scale-95 transition">
          <User className="text-brand-yellow" />
          <span className="text-xs font-black uppercase tracking-[0.14em] text-slate-600">Профиль</span>
        </Link>

        <Link href="/donate" className="it-card flex min-h-[76px] items-center gap-4 bg-white active:scale-95 transition">
          <Gift className="text-brand-yellow" />
          <span className="text-xs font-black uppercase tracking-[0.14em] text-slate-600">Донат</span>
        </Link>

        <Link href="/support" className="it-card flex min-h-[76px] items-center gap-4 bg-white active:scale-95 transition">
          <Headphones className="text-brand-yellow" />
          <span className="text-xs font-black uppercase tracking-[0.14em] text-slate-600">Поддержка</span>
        </Link>
      </section>
    </main>
  );
}
