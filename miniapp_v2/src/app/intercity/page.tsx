import Link from 'next/link';
import { ArrowRight, CarFront, MapPinned, Route } from 'lucide-react';
import { APP_ROUTES } from '@/lib/constants';

export default function IntercityPage() {
  return (
    <main className="shell stack with-bottom-nav">
      <section className="premium-hero">
        <div className="relative z-10">
          <p className="metric-label">Межгород</p>
          <h1 className="title">Куда едем?</h1>
          <p className="subtitle mt-2">Создайте заявку, предложите маршрут или посмотрите доступные поездки между городами.</p>
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
            <span>Активные заявки и маршруты</span>
          </div>
          <ArrowRight size={20} />
        </Link>
      </section>
    </main>
  );
}
