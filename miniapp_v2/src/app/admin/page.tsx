import Link from 'next/link';
import { CreditCard, Gift, Percent, ShieldCheck } from 'lucide-react';

const sections = [
  {
    title: 'Водители',
    description: 'Заявки на проверку профиля, автомобиля и допуска к женскому режиму.',
    href: '/admin/drivers',
    icon: ShieldCheck,
    primary: true,
  },
  {
    title: 'Комиссия',
    description: 'Правила комиссии по всему сервису, странам, городам или отдельным водителям.',
    href: '/admin/commission',
    icon: Percent,
  },
  {
    title: 'Платежи',
    description: 'Проверка заявок на пополнение баланса водителей.',
    href: '/admin/payments',
    icon: CreditCard,
  },
  {
    title: 'Донаты',
    description: 'Управление включёнными реквизитами поддержки проекта.',
    href: '/admin/donations',
    icon: Gift,
  },
];

export default function AdminPage() {
  return (
    <main className="shell stack">
      <section className="premium-hero">
        <div className="relative z-10">
          <p className="metric-label">Админ</p>
          <h1 className="title">Панель управления</h1>
          <p className="subtitle mt-2">Проверки, платежи и правила сервиса в одном месте.</p>
        </div>
      </section>

      <section className="grid grid-2">
        {sections.map((section) => {
          const Icon = section.icon;
          return (
            <Link className={`intercity-action ${section.primary ? 'primary' : ''}`} href={section.href} key={section.href}>
              <Icon size={24} />
              <div>
                <strong>{section.title}</strong>
                <span>{section.description}</span>
              </div>
            </Link>
          );
        })}
      </section>
    </main>
  );
}
