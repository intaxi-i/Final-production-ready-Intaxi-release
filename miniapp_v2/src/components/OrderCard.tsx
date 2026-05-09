"use client";
import { useState } from "react";
import { Navigation, Eye, Check } from "lucide-react";

export function OrderCard({ order, actionLabel, onAction, onCounterOffer, disabled }: any) {
  const [v, setV] = useState(String(order.passenger_price));
  return (
    <div className="it-card mb-4 shadow-sm">
      <div className="flex justify-between items-center mb-6">
        <span className="text-[9px] font-display font-extrabold text-slate-300 uppercase tracking-widest italic">№{order.id}</span>
        <div className="flex items-center gap-1 text-brand-yellow font-display font-bold text-[11px] uppercase tracking-wider"><Eye size={12}/> {order.seen_by_drivers}</div>
      </div>
      <div className="space-y-6 mb-8 relative">
        <div className="absolute left-[7px] top-4 bottom-4 w-[1px] bg-slate-100" />
        <div className="flex gap-4 items-start relative">
          <div className="w-3.5 h-3.5 rounded-full border-[3px] border-brand-yellow bg-white z-10 mt-1" />
          <p className="text-[14px] font-bold leading-tight">{order.pickup_address}</p>
        </div>
        <div className="flex gap-4 items-start relative">
          <div className="w-3.5 h-3.5 rounded-full bg-brand-dark z-10 mt-1" />
          <p className="text-[14px] font-bold leading-tight text-slate-400">{order.destination_address}</p>
        </div>
      </div>
      <div className="flex justify-between items-center mb-8 font-display font-bold text-[9px] text-slate-300 uppercase tracking-widest border-y border-slate-50 py-3">
        <div className="flex items-center gap-1.5"><Navigation size={10}/> {order.estimated_distance_km || 0} KM</div>
        <div className="italic">⏳ {order.estimated_duration_min || "--"} MIN</div>
      </div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-[32px] font-display font-extrabold tracking-tighter leading-none">{order.passenger_price}<span className="text-[10px] ml-1 text-slate-400 font-sans tracking-normal font-normal">{order.currency}</span></h2>
        {actionLabel && <button onClick={onAction} disabled={disabled} className="bg-brand-yellow h-[44px] px-6 rounded-xl font-display font-bold text-[10px] uppercase tracking-widest active:scale-95 transition-all shadow-md">{actionLabel}</button>}
      </div>
      {onCounterOffer && (
        <div className="bg-slate-50 rounded-2xl p-4">
          <div className="grid grid-cols-3 gap-2 mb-3">
            {[10, 20, 30].map(p => <button key={p} onClick={() => onCounterOffer(Math.round(order.passenger_price*(1+p/100)))} className="h-[44px] bg-white rounded-xl font-display font-bold text-[11px] active:bg-brand-yellow shadow-sm transition-colors">+{p}%</button>)}
          </div>
          <div className="flex gap-2">
            <input type="number" value={v} onChange={e=>setV(e.target.value)} className="flex-1 bg-white rounded-xl px-4 font-display font-bold text-lg border-none outline-none shadow-sm" />
            <button onClick={()=>onCounterOffer(Number(v))} className="w-[52px] h-[52px] bg-brand-dark text-white rounded-xl flex items-center justify-center transition-all active:scale-90 shadow-lg"><Check size={20}/></button>
          </div>
        </div>
      )}
    </div>
  );
}