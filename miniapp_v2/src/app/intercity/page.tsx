'use client';

import Link from 'next/link';
import { ArrowRight, CarFront, MapPinned, Route } from 'lucide-react';
import { useEffect, useState } from 'react';
import { getMe } from '@/lib/api';
import { getDriverProfile } from '@/lib/api-extra';
import { APP_ROUTES } from '@/lib/constants';
import { t } from '@/lib/i18n';
import type { DriverProfile, UserMe } from '@/lib/types';

type LocalText = {
  title: string;
  passengerHint: string;
  driverHint: string;
  needRide: string;
  passengerRequest: string;
  driveRoute: string;
  offerSeats: string;
  offers: string;
  passengerAndRoutes: string;
  driverRoutes: string;
};

const LOCAL_TEXT: Record<string, LocalText> = {
  ru: {
    title: 'Куда едем?',
    passengerHint: 'Создайте заявку или посмотрите доступные маршруты между городами.',
    driverHint: 'Принимайте заявки пассажиров или публикуйте свои межгород-маршруты.',
    needRide: 'Нужна поездка',
    passengerRequest: 'Заявка пассажира',
    driveRoute: 'Еду по маршруту',
    offerSeats: 'Предложить места пассажирам',
    offers: 'Предложения',
    passengerAndRoutes: 'Заявки пассажиров и маршруты',
    driverRoutes: 'Маршруты водителей',
  },
  en: {
    title: 'Where are we going?',
    passengerHint: 'Create a request or view available routes between cities.',
    driverHint: 'Accept passenger requests or publish your intercity route.',
    needRide: 'Need a ride',
    passengerRequest: 'Passenger request',
    driveRoute: 'Driving a route',
    offerSeats: 'Offer seats to passengers',
    offers: 'Offers',
    passengerAndRoutes: 'Passenger requests and routes',
    driverRoutes: 'Driver routes',
  },
  uz: {
    title: 'Qayerga boramiz?',
    passengerHint: 'Buyurtma yarating yoki shaharlararo mavjud marshrutlarni ko‘ring.',
    driverHint: 'Yo‘lovchi buyurtmalarini qabul qiling yoki o‘z shaharlararo marshrutingizni joylang.',
    needRide: 'Safar kerak',
    passengerRequest: 'Yo‘lovchi buyurtmasi',
    driveRoute: 'Marshrut bo‘yicha ketyapman',
    offerSeats: 'Yo‘lovchilarga joy taklif qilish',
    offers: 'Takliflar',
    passengerAndRoutes: 'Yo‘lovchi buyurtmalari va marshrutlar',
    driverRoutes: 'Haydovchi marshrutlari',
  },
  tr: {
    title: 'Nereye gidiyoruz?',
    passengerHint: 'Bir istek oluşturun veya şehirler arası uygun rotaları görün.',
    driverHint: 'Yolcu isteklerini kabul edin veya şehirler arası rotanızı yayınlayın.',
    needRide: 'Yolculuk gerekiyor',
    passengerRequest: 'Yolcu isteği',
    driveRoute: 'Rota kullanıyorum',
    offerSeats: 'Yolculara koltuk teklif et',
    offers: 'Teklifler',
    passengerAndRoutes: 'Yolcu istekleri ve rotalar',
    driverRoutes: 'Sürücü rotaları',
  },
  kz: {
    title: 'Қайда барамыз?',
    passengerHint: 'Өтінім жасаңыз немесе қалалар арасындағы қолжетімді бағыттарды қараңыз.',
    driverHint: 'Жолаушы өтінімдерін қабылдаңыз немесе қалааралық бағытыңызды жариялаңыз.',
    needRide: 'Сапар керек',
    passengerRequest: 'Жолаушы өтінімі',
    driveRoute: 'Бағытпен барамын',
    offerSeats: 'Жолаушыларға орын ұсыну',
    offers: 'Ұсыныстар',
    passengerAndRoutes: 'Жолаушы өтінімдері және бағыттар',
    driverRoutes: 'Жүргізуші бағыттары',
  },
};

function localText(language?: string | null) {
  const key = String(language || 'ru').toLowerCase().split('-')[0];
  return LOCAL_TEXT[key] || LOCAL_TEXT.ru;
}

function isConfirmedDriver(profile: DriverProfile | null) {
  if (!profile?.status) return false;
  return ['approved', 'verified', 'active'].includes(profile.status.toLowerCase());
}

export default function IntercityPage() {
  const [me, setMe] = useState<UserMe | null>(null);
  const [driverProfile, setDriverProfile] = useState<DriverProfile | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadRole() {
      try {
        const user = await getMe();
        if (cancelled) return;
        setMe(user);
        if (user.active_role === 'driver') {
          const profile = await getDriverProfile().catch(() => null);
          if (!cancelled) setDriverProfile(profile);
        }
      } catch {
        // Intercity must remain usable for passengers even if role loading fails.
      }
    }
    void loadRole();
    return () => {
      cancelled = true;
    };
  }, []);

  const lang = me?.language;
  const text = localText(lang);
  const confirmedDriver = me?.active_role === 'driver' && isConfirmedDriver(driverProfile);

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10">
          <p className="metric-label">{t(lang, 'intercity')}</p>
          <h1 className="title">{text.title}</h1>
          <p className="subtitle mt-2">
            {confirmedDriver ? text.driverHint : text.passengerHint}
          </p>
        </div>
      </section>

      <section className="stack">
        <Link href={APP_ROUTES.intercityRequest} className="intercity-action primary">
          <MapPinned size={24} />
          <div>
            <strong>{text.needRide}</strong>
            <span>{text.passengerRequest}</span>
          </div>
          <ArrowRight size={20} />
        </Link>

        {confirmedDriver ? (
          <Link href={APP_ROUTES.intercityRoute} className="intercity-action">
            <Route size={24} />
            <div>
              <strong>{text.driveRoute}</strong>
              <span>{text.offerSeats}</span>
            </div>
            <ArrowRight size={20} />
          </Link>
        ) : null}

        <Link href={APP_ROUTES.intercityOffers} className="intercity-action dark">
          <CarFront size={24} />
          <div>
            <strong>{text.offers}</strong>
            <span>{confirmedDriver ? text.passengerAndRoutes : text.driverRoutes}</span>
          </div>
          <ArrowRight size={20} />
        </Link>
      </section>
    </main>
  );
}
