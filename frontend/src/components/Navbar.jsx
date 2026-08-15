// src/components/Navbar.jsx
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0a]/80 backdrop-blur border-b border-white/10">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        {/* logo */}
        <Link
          to={user?.role === "admin" ? "/admin" : "/dashboard"}
          className="text-lg font-black tracking-tighter"
        >
          snip<span className="text-accent">.</span>it
        </Link>

        {/* right side */}
        <div className="flex items-center gap-3">
          {/* admin badge + link */}
          {user?.role === "admin" && (
            <Link
              to="/admin"
              className="text-xs font-mono px-3 py-1.5 rounded-lg bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20 transition-colors"
            >
              admin panel
            </Link>
          )}

          {/* dashboard link for admin */}
          {user?.role === "admin" && (
            <Link
              to="/dashboard"
              className="text-xs text-white/40 hover:text-white transition-colors"
            >
              my links
            </Link>
          )}

          {/* user name */}
          <span className="text-sm text-white/50 font-mono hidden sm:block">
            {user?.name}
          </span>

          {/* logout */}
          <button
            onClick={handleLogout}
            className="text-xs font-medium px-3 py-1.5 rounded-lg border border-white/10 text-white/40 hover:text-white hover:border-white/30 transition-all"
          >
            logout
          </button>
        </div>
      </div>
    </nav>
  );
}
