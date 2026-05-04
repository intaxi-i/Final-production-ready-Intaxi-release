"use client";

type Props = {
  title?: string;
  fromLabel?: string;
  toLabel?: string;
  subtitle?: string;
  note?: string;
  actionLabel?: string;
  actionHref?: string;
  embedUrl?: string;
  provider?: string;
};

export default function MapBox({
  title = "Карта",
  fromLabel = "A",
  toLabel = "B",
  subtitle,
  note,
  actionLabel,
  actionHref,
  embedUrl,
  provider,
}: Props) {
  return (
    <div className="map-box">
      <div className="map-box-header">{title}</div>
      {subtitle ? <div className="map-subtitle">{subtitle}</div> : null}
      {provider ? <div className="map-note">{provider}</div> : null}

      {embedUrl ? (
        <div style={{ overflow: "hidden", borderRadius: 16, marginTop: 12 }}>
          <iframe
            src={embedUrl}
            title={title}
            style={{ width: "100%", height: 260, border: 0 }}
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
          />
        </div>
      ) : (
        <div className="map-road">
          <div className="map-pin">{fromLabel}</div>
          <div className="map-line" />
          <div className="map-pin">{toLabel}</div>
        </div>
      )}

      {note ? <div className="map-note">{note}</div> : null}

      {actionHref ? (
        <a
          href={actionHref}
          target="_blank"
          rel="noreferrer"
          className="button-secondary full"
          style={{ textAlign: "center", marginTop: 12 }}
        >
          {actionLabel || "Open map"}
        </a>
      ) : null}
    </div>
  );
}
