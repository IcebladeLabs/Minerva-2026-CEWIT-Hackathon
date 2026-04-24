import { Video, Flame, UserX, AlertTriangle, HardHat, Radio, Trash2 } from "lucide-react";
import { api } from "../api";

const ZONE_STYLES = {
  restricted:      { label: "RESTRICTED",      bg: "bg-red-500/15",    text: "text-red-400",    border: "border-red-500/25" },
  production_line: { label: "PRODUCTION LINE", bg: "bg-amber-500/15",  text: "text-amber-400",  border: "border-amber-500/25" },
  general:         { label: "GENERAL",         bg: "bg-gray-500/15",   text: "text-gray-400",   border: "border-gray-500/25" },
};

const SEV_STYLES = {
  ok:       { label: "ALL CLEAR",  color: "text-emerald-400", dot: "bg-emerald-400",              anim: "" },
  warning:  { label: "WARNING",    color: "text-amber-400",   dot: "bg-amber-400",   anim: "animate-pulse-slow" },
  critical: { label: "CRITICAL",   color: "text-red-400",     dot: "bg-red-500",     anim: "animate-pulse-fast" },
};

const ANOMALY_ICONS = {
  fire: Flame, intruder: UserX, line_fault: AlertTriangle, safety: HardHat,
};

export default function FeedPanel({ feed, severity, anomalies, vlmDesc, onRemove }) {
  if (!feed) {
    return (
      <div className="rounded-xl border border-dashed border-white/[0.06] bg-white/[0.01] flex flex-col items-center justify-center text-gray-600 gap-2">
        <Video size={28} strokeWidth={1.5} />
        <span className="text-xs">No feed connected</span>
      </div>
    );
  }

  const zone = ZONE_STYLES[feed.zone_type] || ZONE_STYLES.general;
  const sev = SEV_STYLES[severity] || SEV_STYLES.ok;

  return (
    <div className={`rounded-xl border overflow-hidden flex flex-col bg-[var(--color-surface)] transition-all duration-300 ${
      severity === "critical" ? "border-red-500/40 shadow-lg shadow-red-500/10" :
      severity === "warning"  ? "border-amber-500/30 shadow-lg shadow-amber-500/5" :
      "border-white/[0.06]"
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-white/[0.02] border-b border-white/[0.04] shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <div className={`w-2 h-2 rounded-full shrink-0 ${feed.running ? "bg-emerald-400 animate-pulse-slow" : "bg-gray-600"}`} />
          <span className="text-xs font-semibold truncate">{feed.name}</span>
        </div>
        <div className="flex items-center gap-2">
          {feed.running && (
            <span className="text-[10px] text-gray-500 tabular-nums">{feed.fps} fps</span>
          )}
          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-bold ${zone.bg} ${zone.text} ${zone.border} border`}>
            {zone.label}
          </span>
          {onRemove && (
            <button onClick={onRemove} title="Remove feed"
              className="p-1 rounded hover:bg-red-500/15 text-gray-500 hover:text-red-400 transition">
              <Trash2 size={12} />
            </button>
          )}
        </div>
      </div>

      {/* Video */}
      <div className="flex-1 relative bg-black min-h-0 flex items-center justify-center">
        {feed.running ? (
          <img src={api.streamUrl(feed.feed_id)} alt={feed.name} className="w-full h-full object-contain" />
        ) : (
          <div className="text-gray-600 text-sm flex flex-col items-center gap-1">
            <Radio size={20} />
            <span className="text-xs">{feed.last_error || "Feed offline"}</span>
          </div>
        )}
        {severity === "critical" && (
          <div className="absolute inset-0 border-2 border-red-500/60 pointer-events-none animate-pulse-fast" />
        )}
      </div>

      {/* Status bar */}
      <div className={`flex items-center gap-3 px-3 py-2 border-t shrink-0 ${
        severity === "critical" ? "bg-red-500/[0.07] border-red-500/20" :
        severity === "warning"  ? "bg-amber-500/[0.05] border-amber-500/15" :
        "bg-white/[0.01] border-white/[0.04]"
      }`}>
        <div className={`flex items-center gap-1.5 shrink-0 ${sev.color}`}>
          <span className={`w-2 h-2 rounded-full ${sev.dot} ${sev.anim}`} />
          <span className="text-[10px] font-bold uppercase tracking-wider">{sev.label}</span>
        </div>

        {anomalies.length > 0 && (
          <div className="flex items-center gap-1.5">
            {[...new Set(anomalies.map(a => a.anomaly_type))].map(type => {
              const Icon = ANOMALY_ICONS[type] || AlertTriangle;
              const isCrit = anomalies.find(a => a.anomaly_type === type)?.severity === "critical";
              return (
                <span key={type}
                  className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                    isCrit ? "bg-red-500/15 text-red-400" : "bg-amber-500/15 text-amber-400"
                  }`}>
                  <Icon size={10} /> {type.replace("_", " ")}
                </span>
              );
            })}
          </div>
        )}

        {vlmDesc && (
          <div className="flex-1 min-w-0 text-[10px] text-gray-500 italic truncate" title={vlmDesc}>
            {vlmDesc}
          </div>
        )}
      </div>
    </div>
  );
}
