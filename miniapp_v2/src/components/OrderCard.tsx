"use client";
import { useState } from "react";
import { Navigation, Eye, Check } from "lucide-react";

export function OrderCard({ order, actionLabel, onAction, onCounterOffer, disabled }: any) {
  const [val, setVal] = useState(String(order.passenger_price));
  return (
    <article className="bg-white rounded-[2rem] p-6 shadow-premium border border-slate-100 mb-4">
      <div className="flex justify-between mb-4">
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">ID-{order.id}</span>
        <div className="flex items-center gap-1 text-brand-yellow font-bold text-xs"><Eye size={14}/> {order.seen_by_drivers}</div>
      </div>
      <div className="space-y-4 mb-6">
        <div className="flex gap-3"><div className="w-3 h-3 rounded-full border-2 border-brand-yellow mt-1 shrink-0"/><p className="text-sm font-bold leading-tight">{order.pickup_address}</p></div>
        <div className="flex gap-3"><div className="w-3 h-3 rounded-full bg-slate-900 mt-1 shrink-0"/><p className="text-sm font-bold leading-tight text-slate-600">{order.destination_address}</p></div>
      </div>
      <div className="flex justify-between items-center mb-6 border-y border-slate-50 py-3 text-[11px] font-bold text-slate-400 uppercase">
        <span className="flex items-center gap-1"><Navigation size={12}/> {order.estimated_distance_km || 0} km</span>
        <span>⏳ ~{order.estimated_duration_min || "--"} min</span>
      </div>
      <div className="flex items-center justify-between mb-6">
        <div className="text-2xl font-black font-display">{order.passenger_price} <span className="text-xs text-slate-400 font-sans">{order.currency}</span></div>
        {actionLabel && <button onClick={onAction} disabled={disabled} className="bg-brand-yellow px-8 py-3 rounded-xl font-bold text-sm active:scale-95 transition-all">{actionLabel}</button>}
      </div>
      {onCounterOffer && (
        <div className="bg-slate-50 p-4 rounded-[1.5rem]">
          <div className="grid grid-cols-3 gap-2 mb-3">
            {[10, 20, 30].map(p => <button key={p} onClick={() => onCounterOffer(Math.round(order.passenger_price*(1+p/100)))} className="bg-white py-4 rounded-xl font-black text-sm active:bg-brand-yellow transition-colors shadow-sm">+{p}%</button>)}
          </div>
          <div className="flex gap-2">
            <input type="number" value={val} onChange={e=>setVal(e.target.value)} className="w-full rounded-xl border-none bg-white px-4 font-bold text-lg focus:ring-2 focus:ring-brand-yellow"/>
            <button onClick={()=>onCounterOffer(Number(val))} className="bg-slate-900 text-white px-6 rounded-xl font-bold active:scale-95 transition-all"><Check/></button>
          </div>
        </div>
      )}
    </article>
  )
}