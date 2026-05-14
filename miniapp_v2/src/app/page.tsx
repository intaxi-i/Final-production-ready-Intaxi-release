"use client";

import Link from "next/link";
import { Car, Gift, Headphones, History, Map, Radio, Route, User, Wifi } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { getMe } from "@/lib/api";
import { getDriverProfile } from "@/lib/api-extra";
import { APP_ROUTES } from "@/lib/constants";
import type { DriverProfile, UserMe } from "@/lib/types";

type HomeText = {
  slogan: string;
  city: string;
  order: string;
  intercity: string;
  directions: string;
  history: string;
  profile: string;
  donate: string;
  support: string;
  air: string;
  cityOrders: string;
  passengerRequests: string;
  publishIntercityRoute: string;
  application: string;
  becomeDriver: string;
  online: string;
  driverStatus: string;
};

const HOME_TEXT: Record<string, HomeText> = {
  ru: { slogan: "Предлагай свою цену!", city: "Город", order: "Заказать", intercity: "Межгород", directions: "Направления", history: "История", profile: "Профиль", donate: "Донат", support: "Поддержка", air: "Эфир", cityOrders: "Городские заказы", passengerRequests: "Заявки пассажиров", publishIntercityRoute: "Опубликовать межгород-маршрут", application: "Заявка", becomeDriver: "Стать водителем", online: "Онлайн", driverStatus: "Статус водителя" },
  uz: { slogan: "O‘z narxingizni taklif qiling!", city: "Shahar", order: "Buyurtma berish", intercity: "Shaharlararo", directions: "Yo‘nalishlar", history: "Tarix", profile: "Profil", donate: "Donat", support: "Yordam", air: "Efir", cityOrders: "Shahar buyurtmalari", passengerRequests: "Yo‘lovchi buyurtmalari", publishIntercityRoute: "Shaharlararo marshrut qo‘yish", application: "Ariza", becomeDriver: "Haydovchi bo‘lish", online: "Online", driverStatus: "Haydovchi holati" },
  en: { slogan: "Offer your own price!", city: "City", order: "Order", intercity: "Intercity", directions: "Directions", history: "History", profile: "Profile", donate: "Donate", support: "Support", air: "Feed", cityOrders: "City orders", passengerRequests: "Passenger requests", publishIntercityRoute: "Publish intercity route", application: "Application", becomeDriver: "Become a driver", online: "Online", driverStatus: "Driver status" },
  tr: { slogan: "Kendi fiyatını teklif et!", city: "Şehir", order: "Sipariş ver", intercity: "Şehirler arası", directions: "Yönler", history: "Geçmiş", profile: "Profil", donate: "Bağış", support: "Destek", air: "Akış", cityOrders: "Şehir siparişleri", passengerRequests: "Yolcu talepleri", publishIntercityRoute: "Şehirler arası rota yayınla", application: "Başvuru", becomeDriver: "Sürücü ol", online: "Online", driverStatus: "Sürücü durumu" },
  kz: { slogan: "Өз бағаңызды ұсыныңыз!", city: "Қала", order: "Тапсырыс беру", intercity: "Қалааралық", directions: "Бағыттар", history: "Тарих", profile: "Профиль", donate: "Донат", support: "Көмек", air: "Эфир", cityOrders: "Қала тапсырыстары", passengerRequests: "Жолаушы өтінімдері", publishIntercityRoute: "Қалааралық маршрут жариялау", application: "Өтінім", becomeDriver: "Жүргізуші болу", online: "Онлайн", driverStatus: "Жүргізуші күйі" },
};

function normalizeLanguage(language?: string | null) {
  const code = String(language || "ru").toLowerCase().split("-")[0];
  return HOME_TEXT[code] ? code : "ru";
}

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
    return () => { cancelled = true; };
  }, []);

  const activeRole = me?.active_role || "passenger";
  const confirmedDriver = activeRole === "driver" && isConfirmedDriver(driverProfile);
  const text = useMemo(() => HOME_TEXT[normalizeLanguage(me?.language)], [me?.language]);
  const smallLabel = "min-w-0 break-words text-xs font-black uppercase tracking-[0.14em]";

  return (
    <main className="shell flex flex-col justify-center">
      <section className="premium-hero mb-5">
        <div className="relative z-10">
          <h1 className="brand-wordmark" aria-label="Intaxi"><span className="brand-in">In</span><span className="brand-taxi">taxi</span></h1>
          <p className="mt-4 text-xl font-black tracking-[-0.04em] text-slate-950">{text.slogan}</p>
        </div>
      </section>

      {activeRole === "driver" ? (
        <section className="grid grid-cols-2 gap-4">
          {confirmedDriver ? (<>
            <Link href={APP_ROUTES.cityOffers} className="nav-card bg-brand-yellow text-brand-dark border-none shadow-[0_18px_42px_rgba(255,196,0,0.24)]"><div className="nav-icon bg-white/80 text-brand-dark"><Radio size={24} /></div><div><p className="text-xl font-black tracking-[-0.04em]">{text.air}</p><p className="mt-1 text-xs font-black uppercase tracking-[0.16em] text-slate-700">{text.cityOrders}</p></div></Link>
            <Link href={APP_ROUTES.intercityOffers} className="nav-card dark"><div className="nav-icon"><Car size={24} /></div><div><p className="text-xl font-black tracking-[-0.04em]">{text.intercity}</p><p className="nav-label mt-1">{text.passengerRequests}</p></div></Link>
            <Link href={APP_ROUTES.intercityRoute} className="it-card col-span-2 flex min-h-[86px] items-center justify-between gap-4 border-brand-yellow/40 bg-white active:scale-95 transition"><div className="flex min-w-0 items-center gap-4"><Route className="shrink-0 text-brand-yellow" /><span className={`${smallLabel} text-slate-700`}>{text.publishIntercityRoute}</span></div><span className="shrink-0 text-xl font-black text-slate-300">→</span></Link>
          </>) : (<>
            <Link href="/driver/register" className="nav-card bg-brand-yellow text-brand-dark border-none shadow-[0_18px_42px_rgba(255,196,0,0.24)]"><div className="nav-icon bg-white/80 text-brand-dark"><Car size={24} /></div><div><p className="text-xl font-black tracking-[-0.04em]">{text.application}</p><p className="mt-1 text-xs font-black uppercase tracking-[0.16em] text-slate-700">{text.becomeDriver}</p></div></Link>
            <Link href="/driver/online" className="nav-card dark"><div className="nav-icon"><Wifi size={24} /></div><div><p className="text-xl font-black tracking-[-0.04em]">{text.online}</p><p className="nav-label mt-1">{text.driverStatus}</p></div></Link>
          </>)}
          <Link href="/profile" className="it-card flex min-h-[86px] items-center gap-4 bg-white active:scale-95 transition"><User className="shrink-0 text-brand-yellow" /><span className={`${smallLabel} text-slate-600`}>{text.profile}</span></Link>
          <Link href="/support" className="it-card flex min-h-[86px] items-center gap-4 bg-white active:scale-95 transition"><Headphones className="shrink-0 text-brand-yellow" /><span className={`${smallLabel} text-slate-600`}>{text.support}</span></Link>
        </section>
      ) : (
        <section className="grid grid-cols-2 gap-4">
          <Link href="/city/create" className="nav-card bg-brand-yellow text-brand-dark border-none shadow-[0_18px_42px_rgba(255,196,0,0.24)]"><div className="nav-icon bg-white/80 text-brand-dark"><Map size={24} /></div><div><p className="text-xl font-black tracking-[-0.04em]">{text.city}</p><p className="mt-1 text-xs font-black uppercase tracking-[0.16em] text-slate-700">{text.order}</p></div></Link>
          <Link href={APP_ROUTES.intercity} className="nav-card dark"><div className="nav-icon"><Route size={24} /></div><div><p className="text-xl font-black tracking-[-0.04em]">{text.intercity}</p><p className="nav-label mt-1">{text.directions}</p></div></Link>
          <Link href="/city/my-orders" className="it-card flex min-h-[86px] items-center gap-4 bg-slate-950 text-white active:scale-95 transition"><History className="shrink-0 text-brand-yellow" /><span className={`${smallLabel} text-white/75`}>{text.history}</span></Link>
          <Link href="/profile" className="it-card flex min-h-[86px] items-center gap-4 bg-white active:scale-95 transition"><User className="shrink-0 text-brand-yellow" /><span className={`${smallLabel} text-slate-600`}>{text.profile}</span></Link>
          <Link href="/donate" className="it-card flex min-h-[76px] items-center gap-4 bg-white active:scale-95 transition"><Gift className="shrink-0 text-brand-yellow" /><span className={`${smallLabel} text-slate-600`}>{text.donate}</span></Link>
          <Link href="/support" className="it-card flex min-h-[76px] items-center gap-4 bg-white active:scale-95 transition"><Headphones className="shrink-0 text-brand-yellow" /><span className={`${smallLabel} text-slate-600`}>{text.support}</span></Link>
        </section>
      )}
    </main>
  );
}
