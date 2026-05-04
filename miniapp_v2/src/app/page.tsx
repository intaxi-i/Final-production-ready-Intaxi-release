import Link from 'next/link';
import { BottomNav } from '@/components/BottomNav';
import { PageHeader } from '@/components/PageHeader';
import { APP_ROUTES } from '@/lib/constants';
import { t } from '@/lib/i18n';

const links = [
  [t('ru', 'profile'), APP_ROUTES.profile, 'Личные данные, роль и страна.'],
  [t('ru', 'createOrder'), APP_ROUTES.cityCreate, 'Пассажир создаёт city-заказ.'],
  [t('ru', 'myOrders'), APP_ROUTES.cityMyOrders, 'История и активные заявки.'],
  [t('ru', 'availableOffers'), APP_ROUTES.cityOffers, 'Доступные заказы для водителя.'],
  [t('ru', 'currentTrip'), APP_ROUTES.currentTrip, 'Текущая поездка и чат.'],
  [t('ru', 'wallet'), APP_ROUTES.wallet, 'Баланс и пополнение.'],
  [t('ru', 'admin'), APP_ROUTES.admin, 'Настройки и управление.'],
];

export default function HomePage() {
  return (
    <main className="shell">
      <section className="card stack">
        <span className="badge w-fit">Intaxi V2</span>
        <PageHeader
          title="Такси InTaxi"
          subtitle="Пассажир сам предлагает цену за поездку."
        />
      </section>

      <section className="grid grid-2 pb-24">
        {links.map(([label, href, description]) => (
          <Link className="card stack no-underline transition-opacity hover:opacity-80" href={href} key={href}>
            <strong className="text-white">{label}</strong>
            <p className="subtitle">{description}</p>
          </Link>
        ))}
      </section>
      <BottomNav />
    </main>
  );
}