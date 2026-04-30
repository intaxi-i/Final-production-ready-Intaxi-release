import Link from 'next/link';

const links = [
  ['Профиль', '/profile'],
  ['Создать city-заказ', '/city/create'],
  ['Мои city-заказы', '/city/my-orders'],
  ['Водитель online', '/driver/online'],
  ['Доступные city-заказы', '/city/offers'],
  ['Реквизиты водителя', '/driver/payment-methods'],
  ['Текущая поездка', '/trip/current'],
  ['Поддержка проекта', '/donate'],
  ['Админ-панель', '/admin'],
];

export default function HomePage() {
  return (
    <main className="shell stack">
      <section className="card stack">
        <span className="badge">Intaxi V2</span>
        <div>
          <h1 className="title">Такси, где цену можно предложить самому</h1>
          <p className="subtitle">
            Mini App V2 подключается к Backend V2 через единый API. Бизнес-логика остаётся на backend.
          </p>
        </div>
      </section>

      <section className="grid grid-2">
        {links.map(([label, href]) => (
          <Link className="card" href={href} key={href}>
            <strong>{label}</strong>
            <p className="subtitle">Открыть раздел</p>
          </Link>
        ))}
      </section>
    </main>
  );
}
