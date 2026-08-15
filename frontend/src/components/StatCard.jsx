// src/components/StatCard.jsx
export default function StatCard({ label, value, sub }) {
  return (
    <div className="bg-[#111] border border-white/10 rounded-2xl p-5">
      <p className="text-xs text-white/30 uppercase tracking-widest font-medium mb-2">
        {label}
      </p>
      <p className="text-3xl font-black tracking-tight text-white">
        {value ?? "—"}
      </p>
      {sub && <p className="text-xs text-white/30 font-mono mt-1">{sub}</p>}
    </div>
  );
}
