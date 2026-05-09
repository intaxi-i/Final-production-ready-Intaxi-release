"use client";
import { useState } from "react";
import { Navigation, Eye, Check } from "lucide-react";
export function OrderCard({ order, actionLabel, onAction, onCounterOffer, disabled }: any) {
  const [v, setV] = useState(String(order.passenger_price));
  return (
    <div className="it-card mb-4 overflow-hidden relative border-none shadow-lg">
      <div className="flex justify-between items-center mb-6">
        <span className="text-[10px] font-black text-slate-200 uppercase tracking-tighter">№{order.id}</span>
        <div className="flex items-center gap-1.5 text-brand-yellow font-black text-xs"><Eye size={14}/> {order.seen_by_drivers}</div>
      </div>
      <div className="space-y-6 mb-8 relative">
        <div className="absolute left-[7px] top-3 bottom-3 w-[1px] bg-slate-100" />
        <div className="flex gap-4 items-start">
          <div className="w-3.5 h-3.5 rounded-full border-2 border-brand-yellow bg-white z-10 mt-1" />
          <p className="text-sm font-bold tracking-tight leading-tight">{order.pickup_address}</p>
        </div>
        <div className="flex gap-4 items-start">
          <div className="w-3.5 h-3.5 rounded-full bg-slate-900 z-10 mt-1" />
          <p className="text-sm font-bold tracking-tight leading-tight text-slate-400">{order.destination_address}</p>
        </div>
      </div>
      <div className="flex justify-between items-center bg-slate-50 mx-[-24px] px-6 py-3 mb-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">
        <div className="flex items-center gap-1.5"><Navigation size={12}/> {order.estimated_distance_km || 0} KM</div>
        <div className="italic">⏳ {order.estimated_duration_min || "--"} MIN</div>
      </div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-4xl font-black tracking-tighter italic">{order.passenger_price}<span className="text-xs ml-1 text-slate-300 font-normal uppercase tracking-normal">{order.currency}</span></h2>
        {actionLabel && <button onClick={onAction} disabled={disabled} className="bg-brand-yellow h-12 px-8 rounded-2xl font-black text-xs uppercase tracking-widest active:scale-95 transition-all shadow-lg shadow-yellow-400/20">{actionLabel}</button>}
      </div>
      {onCounterOffer && (
        <div className="mt-6 pt-6 border-t border-slate-50">
          <div className="grid grid-cols-3 gap-2 mb-4">
            {[10, 20, 30].map(p => <button key={p} onClick={() => onCounterOffer(Math.round(order.passenger_price*(1+p/100)))} className="h-12 bg-slate-50 rounded-xl font-black text-xs active:bg-brand-yellow transition-all">+{p}%</button>)}
          </div>
          <div className="flex gap-2">
            <input type="number" value={v} onChange={e=>setV(e.target.value)} className="flex-1 bg-slate-50 rounded-2xl px-5 font-black text-xl outline-none" />
            <button onClick={()=>onCounterOffer(Number(v))} className="w-16 h-16 bg-slate-900 text-white rounded-2xl flex items-center justify-center transition-all active:scale-90"><Check/></button>
          </div>
        </div>
      )}
    </div>
  );
}