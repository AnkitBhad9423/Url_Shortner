// src/pages/Dashboard.jsx
import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";
import ShortenForm from "../components/ShortenForm";
import LinkRow from "../components/LinkRow";
import StatCard from "../components/StatCard";
import client from "../api/client";

export default function Dashboard() {
  const { user } = useAuth();

  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // fetch user's links on mount
  useEffect(() => {
    fetchLinks();
  }, []);

  const fetchLinks = async () => {
    setLoading(true);
    try {
      const res = await client.get("/api/links");
      setLinks(res.data.links || []);
    } catch (err) {
      setError("failed to load links. refresh and try again.");
    } finally {
      setLoading(false);
    }
  };

  // called by ShortenForm on success — prepend new link to list
  const handleNewLink = (newLink) => {
    setLinks((prev) => [
      {
        ...newLink,
        click_count: 0,
      },
      ...prev,
    ]);
  };

  // called by LinkRow on delete — remove from list
  const handleDelete = (short_code) => {
    setLinks((prev) => prev.filter((l) => l.short_code !== short_code));
  };

  // derived stats
  const totalClicks = links.reduce((sum, l) => sum + (l.click_count || 0), 0);

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <Navbar />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 pt-24 pb-16">
        {/* greeting */}
        <div className="mb-8">
          <h1 className="text-3xl font-black tracking-tight mb-1">
            hey, {user?.name?.split(" ")[0]} 👋
          </h1>
          <p className="text-sm text-white/30">
            here are all your links. slay as usual.
          </p>
        </div>

        {/* stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-8">
          <StatCard label="Total Links" value={links.length} sub="all time" />
          <StatCard
            label="Total Clicks"
            value={totalClicks}
            sub="across all links"
          />
          <StatCard label="Account" value={user?.role} sub={user?.email} />
        </div>

        {/* shorten form */}
        <div className="mb-6">
          <ShortenForm onSuccess={handleNewLink} />
        </div>

        {/* links list */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium text-white/40 uppercase tracking-widest">
              Your Links
            </h2>
            <span className="text-xs font-mono text-white/20">
              {links.length} total
            </span>
          </div>

          {/* loading */}
          {loading && (
            <div className="flex items-center justify-center py-16 text-white/20 text-sm font-mono">
              <span className="w-4 h-4 border-2 border-white/20 border-t-white/60 rounded-full animate-spin mr-3" />
              loading your links...
            </div>
          )}

          {/* error */}
          {error && !loading && (
            <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 font-mono">
              {error}
            </div>
          )}

          {/* empty state */}
          {!loading && !error && links.length === 0 && (
            <div className="text-center py-16 border border-white/10 border-dashed rounded-2xl">
              <p className="text-white/20 text-sm font-mono mb-1">
                no links yet bestie
              </p>
              <p className="text-white/10 text-xs font-mono">
                paste a URL above and slay it
              </p>
            </div>
          )}

          {/* links */}
          {!loading && !error && links.length > 0 && (
            <div className="flex flex-col gap-2">
              {links.map((link) => (
                <LinkRow
                  key={link.short_code}
                  link={link}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
