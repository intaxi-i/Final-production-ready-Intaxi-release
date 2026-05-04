'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { APP_ROUTES } from '@/lib/constants';
import { t } from '@/lib/i18n';

const links = [
  { href: APP_ROUTES.home, labelKey: 'home' },
  { href: APP_ROUTES.cityCreate, labelKey: 'city' },
  { href: APP_ROUTES.cityOffers, labelKey: 'availableOffers' },
  { href: APP_ROUTES.currentTrip, labelKey: 'currentTrip' },
  { href: APP_ROUTES.profile, labelKey: 'profile' },
];

export function BottomNav({ lang = 'ru' }: { lang?: string }) {
  const pathname = usePathname();
  return (
    <div className="bottom-nav-wrap">
      <nav className="bottom-nav">
        {links.map((link) => {
          const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
          return (
            <Link key={link.href} href={link.href} className={`bottom-link${active ? ' active' : ''}`}>
              <span>{t(lang, link.labelKey)}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
