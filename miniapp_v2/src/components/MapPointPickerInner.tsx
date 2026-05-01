'use client';

import { CircleMarker, MapContainer, TileLayer, useMapEvents } from 'react-leaflet';
import type { LatLngExpression } from 'leaflet';
import 'leaflet/dist/leaflet.css';

type Props = {
  center: { lat: number; lng: number };
  picked: { lat: number; lng: number } | null;
  onPick: (value: { lat: number; lng: number }) => void;
};

function PickerEvents({ onPick }: { onPick: Props['onPick'] }) {
  useMapEvents({
    click(event) {
      onPick({ lat: Number(event.latlng.lat.toFixed(6)), lng: Number(event.latlng.lng.toFixed(6)) });
    },
  });
  return null;
}

export default function MapPointPickerInner({ center, picked, onPick }: Props) {
  const mapCenter: LatLngExpression = [center.lat, center.lng];
  const markerPosition: LatLngExpression | null = picked ? [picked.lat, picked.lng] : null;
  return (
    <MapContainer center={mapCenter} zoom={13} style={{ width: '100%', height: '100%' }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OpenStreetMap contributors" />
      <PickerEvents onPick={onPick} />
      {markerPosition ? <CircleMarker center={markerPosition} radius={10} pathOptions={{ color: '#0ea5e9', fillColor: '#38bdf8', fillOpacity: 0.9 }} /> : null}
    </MapContainer>
  );
}
