import Link from "next/link";

type Props = {
  href: string;
  title: string;
  text: string;
  badge?: string;
};

export default function ActionCard({ href, title, text, badge }: Props) {
  return (
    <Link href={href} className="menu-card">
      <div className="menu-card-row">
        <div className="menu-card-copy">
          <div className="menu-card-title">{title}</div>
          <div className="menu-card-text">{text}</div>
        </div>
        {badge ? <span className="pill small">{badge}</span> : null}
      </div>
    </Link>
  );
}