'use client';

import dynamic from 'next/dynamic';
import { useMemo, useState } from 'react';
import { reverseGeocode } from '@/lib/geo';

const LeafletPicker = dynamic(() => import('@/components/MapPointPickerInner'), { ssr: false });

type Props = {
  lang: string;
  triggerLabel: string;
  title: string;
  confirmLabel: string;
  cancelLabel: string;
  initialLat?: number | null;
  initialLng?: number | null;
  onConfirm: (payload: { address: string; lat: string; lng: string; city?: string; region?: string; countryCode?: string }) => void;
};

function loadingText(lang: string) {
  if (lang === 'uz') return 'Nuqta tasdiqlanmoqda...';
  if (lang === 'kz') return 'Нүкте расталуда...';
  if (lang === 'en') return 'Confirming point...';
  return 'Подтверждаем точку...';
}

export function MapPointPicker({ lang, triggerLabel, title, confirmLabel, cancelLabel, initialLat, initialLng, onConfirm }: Props) {
  const [open, setOpen] = useState(false);
  const [picked, setPicked] = useState<{ lat: number; lng: number } | null>(initialLat != null && initialLng != null ? { lat: initialLat, lng: initialLng } : null);
  const [busy, setBusy] = useState(false);
  const center = useMemo(() => picked || { lat: 41.311081, lng: 69.240562 }, [picked]);

  async function confirm() {
    if (!picked) return;
    try {
      setBusy(true);
      const result = await reverseGeocode(picked.lat, picked.lng);
      onConfirm({ address: result.address, lat: String(result.lat), lng: String(result.lng), city: result.city, region: result.region, countryCode: result.countryCode });
      setOpen(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button type="button" className="button secondary" onClick={() => setOpen(true)}>{triggerLabel}</button>
      {open ? (
        <div className="map-modal">
          <div className="card stack" style={{ margin: 0 }}>
            <strong>{title}</strong>
            <p className="subtitle">{picked ? `${picked.lat.toFixed(6)}, ${picked.lng.toFixed(6)}` : '—'}</p>
          </div>
          <div className="map-panel">
            <LeafletPicker center={center} picked={picked} onPick={setPicked} />
          </div>
          <div className="actions">
            <button type="button" className="button secondary" onClick={() => setOpen(false)}>{cancelLabel}</button>
            <button type="button" className="button" onClick={confirm} disabled={!picked || busy}>{busy ? loadingText(lang) : confirmLabel}</button>
          </div>
        </div>
      ) : null}
    </>
  );
}
