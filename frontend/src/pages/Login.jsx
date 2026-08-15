// src/pages/Login.jsx
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import client from "../api/client";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!form.email.trim()) {
      setError("email is required");
      return;
    }
    if (!form.password) {
      setError("password is required");
      return;
    }

    setLoading(true);

    try {
      const res = await client.post("/auth/login", {
        email: form.email,
        password: form.password,
      });

      const { access_token, name, role } = res.data;

      login(access_token, { name, email: form.email, role });

      const saved = localStorage.getItem("token");
      console.log("Token saved before navigate:", saved ? "✅" : "❌");
      // admin goes to /admin, regular user goes to /dashboard
      navigate(role === "admin" ? "/admin" : "/dashboard", { replace: true });
    } catch (err) {
      const status = err.response?.status;
      const msg = err.response?.data?.detail;

      if (status === 401) {
        setError("wrong email or password. try again.");
      } else if (status === 403) {
        setError("your account has been banned. contact support.");
      } else {
        setError(msg || "something went wrong. try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
      {/* logo */}
      <a href="/" className="mb-8 text-xl font-black tracking-tighter">
        snip<span className="text-accent">.</span>it
      </a>

      {/* card */}
      <div className="w-full max-w-md bg-[#111] border border-white/10 rounded-2xl p-8">
        {/* heading */}
        <div className="mb-7">
          <h1 className="text-2xl font-extrabold tracking-tight mb-1">
            Welcome back
          </h1>
          <p className="text-sm text-white/40">
            log back in. your links missed you fr.
          </p>
        </div>

        {/* form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* email */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-white/50 uppercase tracking-widest">
              Email
            </label>
            <input
              name="email"
              type="email"
              placeholder="ankit@gmail.com"
              value={form.email}
              onChange={handleChange}
              className="bg-[#1a1a1a] border border-white/10 rounded-xl px-4 py-3 text-sm font-mono text-white placeholder-white/20 outline-none focus:border-white/30 transition-colors"
            />
          </div>

          {/* password */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-white/50 uppercase tracking-widest">
              Password
            </label>
            <input
              name="password"
              type="password"
              placeholder="your password"
              value={form.password}
              onChange={handleChange}
              className="bg-[#1a1a1a] border border-white/10 rounded-xl px-4 py-3 text-sm font-mono text-white placeholder-white/20 outline-none focus:border-white/30 transition-colors"
            />
          </div>

          {/* error */}
          {error && (
            <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 font-mono">
              {error}
            </div>
          )}

          {/* submit */}
          <button
            type="submit"
            disabled={loading}
            className="mt-1 bg-accent text-black font-bold text-sm rounded-xl py-3 hover:opacity-90 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:scale-100"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-3.5 h-3.5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                logging in...
              </span>
            ) : (
              "Log in ✦"
            )}
          </button>
        </form>

        {/* divider */}
        <div className="flex items-center gap-3 my-6">
          <div className="flex-1 h-px bg-white/10" />
          <span className="text-xs text-white/20">or</span>
          <div className="flex-1 h-px bg-white/10" />
        </div>

        {/* signup link */}
        <p className="text-center text-sm text-white/40">
          don't have an account?{" "}
          <Link
            to="/signup"
            className="text-white font-medium hover:text-accent transition-colors"
          >
            sign up
          </Link>
        </p>
      </div>

      {/* footer */}
      <p className="mt-6 text-xs text-white/20">
        rate limited · secured · built with FastAPI
      </p>
    </div>
  );
}
