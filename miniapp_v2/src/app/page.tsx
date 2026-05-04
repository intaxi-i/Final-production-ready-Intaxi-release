import Link from 'next/link';
import { BottomNav } from '@/components/BottomNav';
import { PageHeader } from '@/components/PageHeader';
import { APP_ROUTES } from '@/lib/constants';
import { t } from '@/lib/i18n';

const links = [
  [t('ru', 'profile'), APP_ROUTES.profile, 'Личные данные, роль, страна, city и режимы.'],
  [t('ru', 'createOrder'), APP_ROUTES.cityCreate, 'Пассажир создаёт city-заказ и предлагает цену.'],
  [t('ru', 'myOrders'), APP_ROUTES.cityMyOrders, 'История и активные заявки пассажира.'],
  [t('ru', 'availableOffers'), APP_ROUTES.cityOffers, 'Доступные city-заказы для водителя.'],
  [t('ru', 'currentTrip'), APP_ROUTES.currentTrip, 'Статусы, реквизиты и текущая поездка.'],
  [t('ru', 'account'), APP_ROUTES.account, 'Баланс и заявки на пополнение.'],
  [t('ru', 'support'), APP_ROUTES.support, 'Обращения в поддержку.'],
  [t('ru', 'admin'), APP_ROUTES.admin, 'Проверки, платежи, комиссии, настройки.'],
];

export default function HomePage() {
  return (
    <main className="shell">
      <section className="card stack">
        <span className="badge w-fit">Intaxi V2</span>
        <PageHeader
          title="Такси, где цену можно предложить самому"
          subtitle="Mini App V2 подключается к Backend V2 через единый API."
        />
        <div className="grid grid-2">
          <div className="card-soft">
            <strong className="text-white">City flow</strong>
            <p className="subtitle">Пассажир создаёт заказ, водитель принимает.</p>
          </div>
          <div className="card-soft">
            <strong className="text-white">Women mode</strong>
            <p className="subtitle">Безопасные поездки для женщин.</p>
          </div>
        </div>
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