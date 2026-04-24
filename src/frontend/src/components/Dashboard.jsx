import { useState, useEffect, useCallback } from "react";
import { api } from "../api";
import {
  Shield, LogOut, Plus, Flame, UserX, AlertTriangle, HardHat
} from "lucide-react";
import FeedPanel from "./FeedPanel";
import AddFeedModal from "./AddFeedModal";

const SEVERITY_CONFIG = {
  critical: { color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/30", dot: "bg-red-500" },
  warning:  { color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/30", dot: "bg-amber-500" },
  info:     { color: "text-sky-400", bg: "bg-sky-500/10", border: "border-sky-500/30", dot: "bg-sky-500" },
};

const ANOMALY_ICONS = {
  fire: Flame, intruder: UserX, line_fault: AlertTriangle, safety: HardHat,
};

export default function Dashboard({ onLogout }) {
  const [user, setUser] = useState(null);
  const [feeds, setFeeds] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [detections, setDetections] = useState({});
  const [vlmDescs, setVlmDescs] = useState({});
  const [stats, setStats] = useState({ total_incidents: 0, critical_incidents: 0, incidents_today: 0, total_alerts: 0 });
  const [online, setOnline] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [h, f, i, s, d] = await Promise.all([
        api.get("/health"), api.get("/feeds"),
        api.get("/incidents?limit=40"), api.get("/stats"), api.get("/detections"),
      ]);
      setOnline(true);
      setFeeds(f.feeds || []);
      setIncidents(i.incidents || []);
      setStats(s);
      setDetections(d.detections || {});
      setVlmDescs(d.vlm_descriptions || {});
    } catch (err) {
      if (err.status === 401) { api.clearToken(); window.location.reload(); return; }
      setOnline(false);
    }
  }, []);

  useEffect(() => {
    api.get("/me").then(d => setUser(d.user)).catch(() => { api.clearToken(); window.location.reload(); });
    refresh();
    const iv = setInterval(refresh, 2500);
    return () => clearInterval(iv);
  }, [refresh]);

  async function removeFeed(feedId) {
    try {
      await api.del(`/feeds/${feedId}`);
      refresh();
    } catch (err) {
      console.error("Failed to remove feed", err);
    }
  }

  function currentSeverity(feedId) {
    const dets = detections[feedId] || [];
    const anomalies = dets.filter(d => d.anomaly_type);
    if (anomalies.some(d => d.severity === "critical")) return "critical";
    if (anomalies.some(d => d.severity === "warning")) return "warning";
    return "ok";
  }

  function currentAnomalies(feedId) {
    return (detections[feedId] || []).filter(d => d.anomaly_type);
  }

  const slots = [...feeds];
  while (slots.length < 4) slots.push(null);

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Top Bar */}
      <header className="flex items-center justify-between px-5 py-2.5 bg-[var(--color-surface)] border-b border-white/[0.05] shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center shadow-md shadow-sky-500/15">
            <Shield size={16} className="text-white" />
          </div>
          <h1 className="text-lg font-bold tracking-tight">
            Min<span className="text-sky-400">erva</span>
          </h1>
          <span className="text-[10px] font-bold uppercase tracking-widest text-gray-600 ml-1 hidden sm:inline">
            Industrial AI Watchguard
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
            online ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${online ? "bg-emerald-400 animate-pulse-slow" : "bg-red-400 animate-pulse-fast"}`} />
            {online ? "System Online" : "Disconnected"}
          </div>
          {user && <span className="text-xs text-gray-500">Operator: <strong className="text-gray-300">{user.usr}</strong></span>}
          <button onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-sky-500 to-indigo-500 text-xs font-semibold text-white hover:brightness-110 transition shadow-md shadow-sky-500/15">
            <Plus size={14} /> Add Feed
          </button>
          <button onClick={onLogout}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/[0.06] text-xs text-gray-400 hover:text-red-400 hover:border-red-500/30 transition">
            <LogOut size={14} />
          </button>
        </div>
      </header>

      {/* Body */}
      <div className="flex flex-1 min-h-0">
        {/* Sidebar */}
        <aside className="w-72 shrink-0 bg-[var(--color-surface)] border-r border-white/[0.05] flex flex-col overflow-hidden">
          <div className="p-4 border-b border-white/[0.05]">
            <h3 className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-3">Overview</h3>
            <div className="grid grid-cols-2 gap-2">
              <StatCard value={feeds.filter(f => f.running).length + "/" + feeds.length} label="Feeds" accent="emerald" />
              <StatCard value={stats.incidents_today} label="Today" accent="sky" />
              <StatCard value={stats.critical_incidents} label="Critical" accent="red" />
              <StatCard value={stats.total_alerts} label="Alerts" accent="amber" />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            <h3 className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-3 sticky top-0 bg-[var(--color-surface)] pb-1 z-10">
              Incident Timeline
            </h3>
            {incidents.length === 0 ? (
              <p className="text-gray-600 text-xs mt-2">No incidents yet.</p>
            ) : (
              <div className="space-y-2">
                {incidents.slice(0, 30).map((inc, i) => {
                  const sev = SEVERITY_CONFIG[inc.severity] || SEVERITY_CONFIG.info;
                  const Icon = ANOMALY_ICONS[inc.anomaly_type] || AlertTriangle;
                  return (
                    <div key={inc.id || i}
                      className={`flex gap-2.5 p-2.5 rounded-lg ${sev.bg} border ${sev.border} border-opacity-50`}>
                      {inc.snapshot && (
                        <img src={`/snapshots/${inc.snapshot}`} alt="" className="w-14 h-10 rounded object-cover shrink-0 bg-black" />
                      )}
                      <div className="flex-1 min-w-0">
                        <div className={`flex items-center gap-1 text-[10px] font-bold uppercase ${sev.color}`}>
                          <Icon size={11} /> {inc.anomaly_type}
                        </div>
                        <div className="text-[11px] text-gray-400 truncate">
                          {inc.class_name} ({(inc.confidence * 100).toFixed(0)}%) — {inc.feed_name}
                        </div>
                        <div className="text-[10px] text-gray-600 mt-0.5">{inc.created_at}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </aside>

        {/* 2x2 Feed Grid */}
        <main className="flex-1 p-2 min-w-0">
          <div className="grid grid-cols-2 grid-rows-2 gap-2 h-full">
            {slots.slice(0, 4).map((feed, idx) => (
              <FeedPanel
                key={feed ? feed.feed_id : `empty-${idx}`}
                feed={feed}
                severity={feed ? currentSeverity(feed.feed_id) : "ok"}
                anomalies={feed ? currentAnomalies(feed.feed_id) : []}
                vlmDesc={feed ? (vlmDescs[feed.feed_id] || "") : ""}
                onRemove={feed ? () => removeFeed(feed.feed_id) : null}
              />
            ))}
          </div>
        </main>
      </div>

      {showAddModal && (
        <AddFeedModal
          onClose={() => setShowAddModal(false)}
          onAdded={() => { setShowAddModal(false); refresh(); }}
        />
      )}
    </div>
  );
}

function StatCard({ value, label, accent }) {
  const colors = { emerald: "text-emerald-400", sky: "text-sky-400", red: "text-red-400", amber: "text-amber-400" };
  return (
    <div className="rounded-xl bg-white/[0.03] border border-white/[0.04] p-3 text-center">
      <div className={`text-2xl font-extrabold ${colors[accent] || "text-gray-100"}`}>{value}</div>
      <div className="text-[9px] font-bold uppercase tracking-widest text-gray-500 mt-0.5">{label}</div>
    </div>
  );
}
