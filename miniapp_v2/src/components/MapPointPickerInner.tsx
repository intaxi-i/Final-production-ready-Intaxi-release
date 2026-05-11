'use client';

import { useEffect } from 'react';
import { CircleMarker, MapContainer, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import type { LatLngExpression } from 'leaflet';
import 'leaflet/dist/leaflet.css';

type Props = {
  center: { lat: number; lng: number };
  picked: { lat: number; lng: number } | null;
  onPick: (value: { lat: number; lng: number }) => void;
};

function ChangeView({ center }: { center: Props['center'] }) {
  const map = useMap();
  useEffect(() => {
    map.setView([center.lat, center.lng], map.getZoom() || 13, { animate: true });
  }, [center.lat, center.lng, map]);
  return null;
}

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
      <ChangeView center={center} />
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OpenStreetMap contributors" />
      <PickerEvents onPick={onPick} />
      {markerPosition ? <CircleMarker center={markerPosition} radius={10} pathOptions={{ color: '#ffc400', fillColor: '#ffc400', fillOpacity: 0.9 }} /> : null}
    </MapContainer>
  );
}
