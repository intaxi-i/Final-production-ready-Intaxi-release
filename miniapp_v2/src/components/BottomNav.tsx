'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { getMe } from '@/lib/api';
import { getDriverProfile } from '@/lib/api-extra';
import { APP_ROUTES } from '@/lib/constants';
import { t } from '@/lib/i18n';
import type { DriverProfile, UserMe } from '@/lib/types';

type NavLink = {
  href: string;
  labelKey: string;
  fallback: string;
};

function isConfirmedDriver(profile: DriverProfile | null) {
  if (!profile?.status) return false;
  return ['approved', 'verified', 'active'].includes(profile.status.toLowerCase());
}

const passengerLinks: NavLink[] = [
  { href: APP_ROUTES.home, labelKey: 'home', fallback: 'Главная' },
  { href: APP_ROUTES.cityCreate, labelKey: 'city', fallback: 'Город' },
  { href: APP_ROUTES.intercity, labelKey: 'intercity', fallback: 'Межгород' },
  { href: APP_ROUTES.cityMyOrders, labelKey: 'myOrders', fallback: 'История' },
  { href: APP_ROUTES.profile, labelKey: 'profile', fallback: 'Профиль' },
];

const confirmedDriverLinks: NavLink[] = [
  { href: APP_ROUTES.home, labelKey: 'home', fallback: 'Главная' },
  { href: APP_ROUTES.cityOffers, labelKey: 'availableOffers', fallback: 'Эфир' },
  { href: APP_ROUTES.intercityOffers, labelKey: 'intercity', fallback: 'Межгород' },
  { href: '/driver/online', labelKey: 'driverOnline', fallback: 'Онлайн' },
  { href: APP_ROUTES.profile, labelKey: 'profile', fallback: 'Профиль' },
];

const pendingDriverLinks: NavLink[] = [
  { href: APP_ROUTES.home, labelKey: 'home', fallback: 'Главная' },
  { href: '/driver/register', labelKey: 'driverRegister', fallback: 'Заявка' },
  { href: '/driver/online', labelKey: 'driverOnline', fallback: 'Онлайн' },
  { href: '/support', labelKey: 'support', fallback: 'Помощь' },
  { href: APP_ROUTES.profile, labelKey: 'profile', fallback: 'Профиль' },
];

export function BottomNav() {
  const pathname = usePathname();
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
        // Bottom navigation must remain usable even if user profile loading fails.
      }
    }
    void loadRole();
    return () => {
      cancelled = true;
    };
  }, []);

  const links = useMemo(() => {
    if (me?.active_role !== 'driver') return passengerLinks;
    return isConfirmedDriver(driverProfile) ? confirmedDriverLinks : pendingDriverLinks;
  }, [driverProfile, me?.active_role]);

  const lang = me?.language || 'ru';

  return (
    <div className="bottom-nav-wrap">
      <nav className="bottom-nav" aria-label="Основная навигация">
        {links.map((link) => {
          const active = pathname === link.href || (link.href !== APP_ROUTES.home && pathname.startsWith(`${link.href}/`));
          const label = t(lang, link.labelKey) || link.fallback;
          return (
            <Link key={link.href} href={link.href} className={`bottom-link${active ? ' active' : ''}`}>
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
