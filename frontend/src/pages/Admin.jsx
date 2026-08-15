// src/pages/Admin.jsx
import { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import StatCard from "../components/StatCard";
import client from "../api/client";

export default function Admin() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [links, setLinks] = useState([]);
  const [tab, setTab] = useState("overview"); // 'overview' | 'users' | 'links'
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [statsRes, usersRes, linksRes] = await Promise.all([
        client.get("/admin/stats"),
        client.get("/admin/users"),
        client.get("/admin/links"),
      ]);
      setStats(statsRes.data);
      setUsers(usersRes.data.users || []);
      setLinks(linksRes.data.links || []);
    } catch (err) {
      console.error("admin fetch failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleBan = async (userId, isBanned) => {
    const action = isBanned ? "unban" : "ban";
    if (!window.confirm(`${action} this user?`)) return;
    try {
      await client.post(`/admin/users/${userId}/${action}`);
      setUsers((prev) =>
        prev.map((u) =>
          u._id === userId ? { ...u, is_banned: !isBanned } : u,
        ),
      );
    } catch (err) {
      alert(`${action} failed`);
    }
  };

  const handleDeleteLink = async (short_code) => {
    if (!window.confirm("force delete this link?")) return;
    try {
      await client.delete(`/admin/links/${short_code}`);
      setLinks((prev) => prev.filter((l) => l.short_code !== short_code));
    } catch (err) {
      alert("delete failed");
    }
  };

  const tabs = ["overview", "users", "links"];

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <Navbar />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 pt-24 pb-16">
        {/* header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-3xl font-black tracking-tight">Admin Panel</h1>
            <span className="text-xs font-mono px-2.5 py-1 rounded-lg bg-accent/10 text-accent border border-accent/20">
              superuser
            </span>
          </div>
          <p className="text-sm text-white/30">
            you have full access. don't cook the wrong things.
          </p>
        </div>

        {/* tabs */}
        <div className="flex gap-1 mb-8 bg-[#111] border border-white/10 rounded-xl p-1 w-fit">
          {tabs.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all capitalize
                ${
                  tab === t
                    ? "bg-accent text-black"
                    : "text-white/40 hover:text-white"
                }`}
            >
              {t}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-24 text-white/20 text-sm font-mono">
            <span className="w-4 h-4 border-2 border-white/20 border-t-white/60 rounded-full animate-spin mr-3" />
            loading admin data...
          </div>
        ) : (
          <>
            {/* ── OVERVIEW TAB ── */}
            {tab === "overview" && stats && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatCard
                  label="Total Users"
                  value={stats.total_users}
                  sub="registered"
                />
                <StatCard
                  label="Total Links"
                  value={stats.total_links}
                  sub="all users"
                />
                <StatCard
                  label="Total Clicks"
                  value={stats.total_clicks}
                  sub="all time"
                />
                <StatCard
                  label="Banned Users"
                  value={stats.banned_users}
                  sub="accounts"
                />
              </div>
            )}

            {/* ── USERS TAB ── */}
            {tab === "users" && (
              <div className="flex flex-col gap-2">
                <p className="text-xs text-white/30 font-mono mb-2">
                  {users.length} users total
                </p>
                {users.map((u) => (
                  <div
                    key={u._id}
                    className="flex items-center gap-4 px-4 py-3 bg-[#111] border border-white/10 rounded-xl hover:border-white/20 transition-colors"
                  >
                    {/* name + email */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {u.name}
                      </p>
                      <p className="text-xs font-mono text-white/30 truncate">
                        {u.email}
                      </p>
                    </div>

                    {/* role badge */}
                    <span
                      className={`text-xs font-mono px-2.5 py-1 rounded-lg border flex-shrink-0
                      ${
                        u.role === "admin"
                          ? "text-accent border-accent/20 bg-accent/10"
                          : "text-white/30 border-white/10"
                      }`}
                    >
                      {u.role}
                    </span>

                    {/* link count */}
                    <span className="text-xs font-mono text-white/20 flex-shrink-0 hidden sm:block">
                      {u.link_count ?? 0} links
                    </span>

                    {/* banned badge */}
                    {u.is_banned && (
                      <span className="text-xs font-mono px-2 py-1 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20 flex-shrink-0">
                        banned
                      </span>
                    )}

                    {/* ban / unban button — don't show for admin */}
                    {u.role !== "admin" && (
                      <button
                        onClick={() => handleBan(u._id, u.is_banned)}
                        className={`text-xs px-3 py-1.5 rounded-lg border transition-all flex-shrink-0
                          ${
                            u.is_banned
                              ? "text-green-400 border-green-500/30 hover:bg-green-500/10"
                              : "text-red-400 border-red-500/30 hover:bg-red-500/10"
                          }`}
                      >
                        {u.is_banned ? "unban" : "ban"}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* ── LINKS TAB ── */}
            {tab === "links" && (
              <div className="flex flex-col gap-2">
                <p className="text-xs text-white/30 font-mono mb-2">
                  {links.length} links total
                </p>
                {links.map((link) => (
                  <div
                    key={link.short_code}
                    className="flex items-center gap-3 px-4 py-3 bg-[#111] border border-white/10 rounded-xl hover:border-white/20 transition-colors"
                  >
                    {/* short code */}
                    <span className="font-mono text-sm text-accent font-medium w-20 flex-shrink-0">
                      {link.short_code}
                    </span>

                    {/* long url */}
                    <span className="flex-1 text-sm text-white/40 truncate font-mono min-w-0">
                      {link.long_url}
                    </span>

                    {/* owner */}
                    <span className="text-xs font-mono text-white/20 flex-shrink-0 hidden sm:block">
                      {link.created_by || "unknown"}
                    </span>

                    {/* clicks */}
                    <span className="text-xs font-mono text-white/20 flex-shrink-0">
                      {link.click_count ?? 0} clicks
                    </span>

                    {/* delete */}
                    <button
                      onClick={() => handleDeleteLink(link.short_code)}
                      className="text-xs px-3 py-1.5 rounded-lg border border-white/10 text-white/20 hover:text-red-400 hover:border-red-500/30 hover:bg-red-500/10 transition-all flex-shrink-0"
                    >
                      del
                    </button>
                  </div>
                ))}

                {links.length === 0 && (
                  <div className="text-center py-16 border border-white/10 border-dashed rounded-2xl">
                    <p className="text-white/20 text-sm font-mono">
                      no links in system
                    </p>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
