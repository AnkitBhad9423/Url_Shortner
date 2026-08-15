// src/components/ShortenForm.jsx
import { useState } from "react";
import client from "../api/client";

export default function ShortenForm({ onSuccess }) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!url.trim()) {
      setError("paste a URL first bestie");
      return;
    }

    setLoading(true);
    try {
      const res = await client.post("/api/shorten", { long_url: url });
      onSuccess(res.data); // pass new link up to parent
      setUrl("");
    } catch (err) {
      const status = err.response?.status;
      if (status === 429) setError("slow down bestie, rate limit hit 🛑");
      else if (status === 400) setError("that URL is not valid fr");
      else if (status === 403) setError("that domain is blacklisted 🚫");
      else
        setError(err.response?.data?.detail || "something flopped. try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#111] border border-white/10 rounded-2xl p-6">
      <h2 className="text-sm font-medium text-white/40 uppercase tracking-widest mb-4">
        Shorten a new URL
      </h2>

      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="url"
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
            setError("");
          }}
          placeholder="https://your-long-url.com/goes/here"
          className="flex-1 bg-[#1a1a1a] border border-white/10 rounded-xl px-4 py-3 text-sm font-mono text-white placeholder-white/20 outline-none focus:border-white/30 transition-colors min-w-0"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-accent text-black font-bold text-sm px-5 rounded-xl hover:opacity-90 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:scale-100 whitespace-nowrap flex-shrink-0"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
              slaying...
            </span>
          ) : (
            "Slay it ✦"
          )}
        </button>
      </form>

      {error && (
        <p className="mt-3 text-xs text-red-400 font-mono bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
          {error}
        </p>
      )}
    </div>
  );
}
