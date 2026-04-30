import Link from 'next/link';

const sections = [
  {
    title: 'Driver verification',
    description: 'Проверка водителей, авто и отдельного режима допуска.',
    href: '/admin/drivers',
  },
  {
    title: 'Commission rules',
    description: 'Глобальная, country, city и driver комиссия.',
    href: '/admin/commission',
  },
  {
    title: 'Payments',
    description: 'Пополнения баланса водителей и ledger-контроль.',
    href: '/admin/payments',
  },
  {
    title: 'Donation settings',
    description: 'Реквизиты поддержки проекта, управляемые только админкой.',
    href: '/admin/donations',
  },
];

export default function AdminPage() {
  return (
    <main className="shell stack">
      <section className="card stack">
        <span className="badge">Admin V2</span>
        <div>
          <h1 className="title">Админ-панель Intaxi V2</h1>
          <p className="subtitle">
            Все админские действия должны идти через Backend V2 API и писать audit log.
          </p>
        </div>
      </section>

      <section className="grid grid-2">
        {sections.map((section) => (
          <Link className="card stack" href={section.href} key={section.href}>
            <h2 className="title" style={{ fontSize: 22 }}>{section.title}</h2>
            <p className="subtitle">{section.description}</p>
          </Link>
        ))}
      </section>
    </main>
  );
}
