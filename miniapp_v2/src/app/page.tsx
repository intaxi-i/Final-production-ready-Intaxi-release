import Link from 'next/link';
import { BottomNav } from '@/components/BottomNav';
import { PageHeader } from '@/components/PageHeader';
import { APP_ROUTES } from '@/lib/constants';
import { t } from '@/lib/i18n';

const links = [
  [t('ru', 'profile'), APP_ROUTES.profile, 'Личные данные, роль, страна, city и режимы.'],
  [t('ru', 'createOrder'), APP_ROUTES.cityCreate, 'Пассажир создаёт city-заказ и предлагает цену.'],
  [t('ru', 'myOrders'), APP_ROUTES.cityMyOrders, 'История и активные заявки пассажира.'],
  [t('ru', 'driverRegister'), APP_ROUTES.driverRegister, 'Профиль водителя и авто на проверку.'],
  [t('ru', 'driverOnline'), APP_ROUTES.driverOnline, 'Онлайн-статус водителя.'],
  [t('ru', 'availableOffers'), APP_ROUTES.cityOffers, 'Доступные city-заказы для водителя.'],
  [t('ru', 'paymentMethods'), APP_ROUTES.driverPaymentMethods, 'Карта/реквизиты водителя для оплаты напрямую.'],
  [t('ru', 'currentTrip'), APP_ROUTES.currentTrip, 'Статусы, реквизиты и текущая поездка.'],
  [t('ru', 'account'), APP_ROUTES.account, 'Баланс и заявки на пополнение.'],
  [t('ru', 'support'), APP_ROUTES.support, 'Обращения в поддержку.'],
  [t('ru', 'donate'), APP_ROUTES.donate, 'Публичные реквизиты поддержки проекта.'],
  [t('ru', 'admin'), APP_ROUTES.admin, 'Проверки, платежи, комиссии, настройки.'],
];

export default function HomePage() {
  return (
    <main className="shell stack with-bottom-nav">
      <section className="card stack hero-card">
        <span className="badge">Intaxi V2</span>
        <PageHeader
          title="Такси, где цену можно предложить самому"
          subtitle="Mini App V2 подключается к Backend V2 через единый API. Бизнес-логика остаётся на backend."
        />
        <div className="info-grid">
          <div className="card-soft"><strong>City flow</strong><p className="subtitle">Пассажир создаёт заказ, водитель принимает, поездка проходит по статусам.</p></div>
          <div className="card-soft"><strong>Women mode</strong><p className="subtitle">Отдельный режим заложен в профиль, проверку водителя и order mode.</p></div>
          <div className="card-soft"><strong>Admin</strong><p className="subtitle">Комиссии, платежи, водители и реквизиты управляются централизованно.</p></div>
        </div>
      </section>

      <section className="grid grid-2">
        {links.map(([label, href, description]) => (
          <Link className="card nav-card" href={href} key={href}>
            <strong>{label}</strong>
            <p className="subtitle">{description}</p>
          </Link>
        ))}
      </section>
      <BottomNav />
    </main>
  );
}
