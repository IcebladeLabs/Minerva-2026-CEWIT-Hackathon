import { useState } from "react";
import { api } from "../api";
import { Shield, Eye, EyeOff } from "lucide-react";

export default function Auth({ onAuth }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "login") await api.login(username, password);
      else await api.signup(username, email, password);
      onAuth();
    } catch (err) {
      setError(err.error || "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-sky-500/5 blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] rounded-full bg-indigo-500/5 blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-sky-500 to-indigo-600 mb-4 shadow-lg shadow-sky-500/20">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">
            Min<span className="text-sky-400">erva</span>
          </h1>
          <p className="text-gray-500 text-sm mt-1">Industrial AI Watchguard</p>
        </div>

        <form onSubmit={handleSubmit}
          className="glass border border-white/[0.06] rounded-2xl p-8 shadow-2xl shadow-black/40">
          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1 block">Username</label>
              <input type="text" required value={username} onChange={e => setUsername(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white placeholder-gray-600 focus:border-sky-500/50 focus:ring-1 focus:ring-sky-500/25 outline-none transition"
                placeholder="operator1" />
            </div>

            {mode === "signup" && (
              <div>
                <label className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1 block">Email</label>
                <input type="email" required value={email} onChange={e => setEmail(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white placeholder-gray-600 focus:border-sky-500/50 focus:ring-1 focus:ring-sky-500/25 outline-none transition"
                  placeholder="op@factory.local" />
              </div>
            )}

            <div>
              <label className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1 block">Password</label>
              <div className="relative">
                <input type={showPw ? "text" : "password"} required value={password} onChange={e => setPassword(e.target.value)}
                  className="w-full px-4 py-2.5 pr-11 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white placeholder-gray-600 focus:border-sky-500/50 focus:ring-1 focus:ring-sky-500/25 outline-none transition"
                  placeholder="••••••••" />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition">
                  {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
          </div>

          {error && (
            <div className="mt-4 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">{error}</div>
          )}

          <button type="submit" disabled={loading}
            className="mt-6 w-full py-2.5 rounded-lg bg-gradient-to-r from-sky-500 to-indigo-500 font-semibold text-white hover:brightness-110 active:brightness-95 transition disabled:opacity-50 shadow-lg shadow-sky-500/15">
            {loading ? "..." : mode === "login" ? "Sign In" : "Create Account"}
          </button>

          <p className="mt-4 text-center text-sm text-gray-500">
            {mode === "login" ? (
              <>No account?{" "}<button type="button" onClick={() => setMode("signup")} className="text-sky-400 hover:underline">Sign up</button></>
            ) : (
              <>Have an account?{" "}<button type="button" onClick={() => setMode("login")} className="text-sky-400 hover:underline">Sign in</button></>
            )}
          </p>
        </form>
      </div>
    </div>
  );
}

