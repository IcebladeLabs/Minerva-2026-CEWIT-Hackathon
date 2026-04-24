import { useState } from "react";
import { api } from "../api";
import { X, Video } from "lucide-react";

export default function AddFeedModal({ onClose, onAdded }) {
  const [name, setName] = useState("");
  const [source, setSource] = useState("");
  const [zoneType, setZoneType] = useState("general");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/feeds", { name, source, zone_type: zoneType });
      onAdded();
    } catch (err) {
      setError(err.error || "Failed to add feed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
         onClick={onClose}>
      <div className="glass border border-white/[0.06] rounded-2xl p-6 w-full max-w-md shadow-2xl shadow-black/50"
           onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <Video size={18} className="text-sky-400" />
            <h2 className="text-lg font-bold">Add Camera Feed</h2>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1 block">Camera Name</label>
            <input type="text" required value={name} onChange={e => setName(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white placeholder-gray-600 focus:border-sky-500/50 focus:ring-1 focus:ring-sky-500/25 outline-none transition"
              placeholder="Assembly Line Cam 1" />
          </div>

          <div>
            <label className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1 block">Source</label>
            <input type="text" required value={source} onChange={e => setSource(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white placeholder-gray-600 focus:border-sky-500/50 focus:ring-1 focus:ring-sky-500/25 outline-none transition"
              placeholder="/home/cewit_admin/videos/factory.mp4" />
            <p className="text-[10px] text-gray-600 mt-1">File path to .mp4, device number (0), or rtsp:// URL</p>
          </div>

          <div>
            <label className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1 block">Zone Type</label>
            <select value={zoneType} onChange={e => setZoneType(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white focus:border-sky-500/50 outline-none transition">
              <option value="general">General</option>
              <option value="restricted">Restricted Area</option>
              <option value="production_line">Production Line</option>
            </select>
          </div>

          {error && (
            <div className="px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">{error}</div>
          )}

          <div className="flex gap-3 pt-2">
            <button type="submit" disabled={loading}
              className="flex-1 py-2.5 rounded-lg bg-gradient-to-r from-sky-500 to-indigo-500 font-semibold text-white hover:brightness-110 transition disabled:opacity-50 shadow-md shadow-sky-500/15">
              {loading ? "Adding..." : "Add Feed"}
            </button>
            <button type="button" onClick={onClose}
              className="flex-1 py-2.5 rounded-lg border border-white/[0.08] text-gray-400 hover:text-white hover:border-white/15 transition">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
