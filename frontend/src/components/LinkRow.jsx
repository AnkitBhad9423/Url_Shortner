// src/components/LinkRow.jsx
import { useState } from "react";
import client from "../api/client";

const BACKEND_URL = import.meta.env.BACKEND_URL || "http://localhost:8000";
export default function LinkRow({ link, onDelete }) {
  const [copied, setCopied] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const shortUrl = `${BACKEND_URL}/ch/${link.short_code}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(shortUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDelete = async () => {
    if (!window.confirm("delete this link fr?")) return;
    setDeleting(true);
    try {
      await client.delete(`/api/links/${link.short_code}`);
      onDelete(link.short_code); // tell parent to remove from list
    } catch (err) {
      alert("delete failed. try again.");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="flex items-center gap-3 px-4 py-3 bg-[#111] border border-white/10 rounded-xl hover:border-white/20 transition-colors group">
      {/* short code */}
      <span className="font-mono text-sm text-accent font-medium w-20 flex-shrink-0">
        {link.short_code}
      </span>

      {/* long url — truncated */}
      <span className="flex-1 text-sm text-white/40 truncate font-mono min-w-0">
        {link.long_url}
      </span>

      {/* click count */}
      <span className="text-xs font-mono text-white/30 flex-shrink-0 hidden sm:block">
        {link.click_count ?? 0} clicks
      </span>

      {/* copy button */}
      <button
        onClick={handleCopy}
        className={`text-xs px-3 py-1.5 rounded-lg border transition-all flex-shrink-0
          ${
            copied
              ? "text-green-400 border-green-500/30 bg-green-500/10"
              : "text-white/40 border-white/10 hover:text-white hover:border-white/30"
          }`}
      >
        {copied ? "copied ✓" : "copy"}
      </button>

      {/* delete button */}
      <button
        onClick={handleDelete}
        disabled={deleting}
        className="text-xs px-3 py-1.5 rounded-lg border border-white/10 text-white/20 hover:text-red-400 hover:border-red-500/30 hover:bg-red-500/10 transition-all flex-shrink-0 disabled:opacity-40"
      >
        {deleting ? "..." : "del"}
      </button>
    </div>
  );
}
