"use client";
import { useState } from "react";
import { Navigation, Eye, Check } from "lucide-react";
export function OrderCard({ order, actionLabel, onAction, onCounterOffer, disabled }: any) {
  const [v, setV] = useState(String(order.passenger_price));
  return (
    <div className="it-card mb-4 border-none shadow-xl">
      <div className="flex justify-between items-center mb-6">
        <span className="text-[9px] font-black text-slate-200 uppercase tracking-tighter">№{order.id}</span>
        <div className="flex items-center gap-1.5 text-brand-yellow font-black text-xs"><Eye size={14}/> {order.seen_by_drivers}</div>
      </div>
      <div className="space-y-6 mb-8 relative">
        <div className="absolute left-[7.5px] top-4 bottom-4 w-[1px] bg-slate-50" />
        <div className="flex gap-4 items-start relative">
          <div className="w-4 h-4 rounded-full border-[3px] border-brand-yellow bg-white z-10 mt-1" />
          <p className="text-[14px] font-bold leading-tight uppercase tracking-tight">{order.pickup_address}</p>
        </div>
        <div className="flex gap-4 items-start relative">
          <div className="w-4 h-4 rounded-full bg-brand-dark z-10 mt-1" />
          <p className="text-[14px] font-bold leading-tight text-slate-300 uppercase">{order.destination_address}</p>
        </div>
      </div>
      <div className="flex justify-between items-center bg-slate-50 mx-[-24px] px-6 py-4 mb-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">
        <div className="flex items-center gap-1.5"><Navigation size={12}/> {order.estimated_distance_km || 0} KM</div>
        <div className="italic">⏳ {order.estimated_duration_min || "--"} MIN</div>
      </div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-4xl font-black tracking-tighter">{order.passenger_price}<span className="text-xs ml-1 text-slate-300 uppercase">{order.currency}</span></h2>
        {actionLabel && <button onClick={onAction} disabled={disabled} className="bg-brand-yellow h-[50px] px-8 rounded-2xl font-black text-[10px] uppercase tracking-widest shadow-lg shadow-yellow-400/20">{actionLabel}</button>}
      </div>
      {onCounterOffer && (
        <div className="mt-6 p-4 bg-slate-50 rounded-[20px]">
          <div className="grid grid-cols-3 gap-2 mb-4">
            {[10, 20, 30].map(p => <button key={p} onClick={() => onCounterOffer(Math.round(order.passenger_price*(1+p/100)))} className="h-[48px] bg-white rounded-xl font-black text-xs transition-colors active:bg-brand-yellow shadow-sm">+{p}%</button>)}
          </div>
          <div className="flex gap-2">
            <input type="number" value={v} onChange={e=>setV(e.target.value)} className="flex-1 bg-white rounded-xl px-5 font-black text-xl outline-none" />
            <button onClick={()=>onCounterOffer(Number(v))} className="w-[60px] h-[60px] bg-brand-dark text-white rounded-xl flex items-center justify-center"><Check/></button>
          </div>
        </div>
      )}
    </div>
  );
}