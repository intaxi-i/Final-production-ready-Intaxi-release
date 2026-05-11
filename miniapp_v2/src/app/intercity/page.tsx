import Link from 'next/link';
import { ArrowRight, CarFront, MapPinned, Route } from 'lucide-react';
import { APP_ROUTES } from '@/lib/constants';

export default function IntercityPage() {
  return (
    <main className="shell stack">
      <section className="premium-hero">
        <div className="relative z-10">
          <h1 className="title">Межгород</h1>
          <p className="subtitle mt-2">Направления между городами: создавайте заявку, маршрут или смотрите доступные предложения.</p>
        </div>
      </section>

      <section className="stack">
        <Link href={APP_ROUTES.intercityRequest} className="intercity-action primary">
          <MapPinned size={24} />
          <div>
            <strong>Нужна поездка</strong>
            <span>Создать межгород-заявку пассажира</span>
          </div>
          <ArrowRight size={20} />
        </Link>

        <Link href={APP_ROUTES.intercityRoute} className="intercity-action">
          <Route size={24} />
          <div>
            <strong>Еду по маршруту</strong>
            <span>Предложить места пассажирам</span>
          </div>
          <ArrowRight size={20} />
        </Link>

        <Link href={APP_ROUTES.intercityOffers} className="intercity-action dark">
          <CarFront size={24} />
          <div>
            <strong>Предложения</strong>
            <span>Посмотреть доступный межгород</span>
          </div>
          <ArrowRight size={20} />
        </Link>
      </section>

      <section className="card-soft">
        <strong>В разработке интерфейса</strong>
        <p className="subtitle mt-1">Бэкенд межгорода уже предусмотрен маршрутизацией приложения. Следующий шаг — подключить реальные формы и списки к существующим endpoint-ам без изменения backend-логики.</p>
      </section>
    </main>
  );
}
