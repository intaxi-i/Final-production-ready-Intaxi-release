'use client';

import Link from 'next/link';
import { ArrowRight, CarFront, MapPinned, Route } from 'lucide-react';
import { useEffect, useState } from 'react';
import { getMe } from '@/lib/api';
import { getDriverProfile } from '@/lib/api-extra';
import { APP_ROUTES } from '@/lib/constants';
import type { DriverProfile, UserMe } from '@/lib/types';

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

  const confirmedDriver = me?.active_role === 'driver' && isConfirmedDriver(driverProfile);

  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10">
          <p className="metric-label">Межгород</p>
          <h1 className="title">Куда едем?</h1>
          <p className="subtitle mt-2">
            {confirmedDriver
              ? 'Принимайте заявки пассажиров или публикуйте свои межгород-маршруты.'
              : 'Создайте заявку или посмотрите доступные маршруты между городами.'}
          </p>
        </div>
      </section>

      <section className="stack">
        <Link href={APP_ROUTES.intercityRequest} className="intercity-action primary">
          <MapPinned size={24} />
          <div>
            <strong>Нужна поездка</strong>
            <span>Заявка пассажира</span>
          </div>
          <ArrowRight size={20} />
        </Link>

        {confirmedDriver ? (
          <Link href={APP_ROUTES.intercityRoute} className="intercity-action">
            <Route size={24} />
            <div>
              <strong>Еду по маршруту</strong>
              <span>Предложить места пассажирам</span>
            </div>
            <ArrowRight size={20} />
          </Link>
        ) : null}

        <Link href={APP_ROUTES.intercityOffers} className="intercity-action dark">
          <CarFront size={24} />
          <div>
            <strong>Предложения</strong>
            <span>{confirmedDriver ? 'Заявки пассажиров и маршруты' : 'Маршруты водителей'}</span>
          </div>
          <ArrowRight size={20} />
        </Link>
      </section>
    </main>
  );
}
