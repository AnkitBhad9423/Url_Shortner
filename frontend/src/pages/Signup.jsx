// src/pages/Signup.jsx
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import client from "../api/client";

export default function Signup() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // basic frontend validation
    if (!form.name.trim()) {
      setError("name is required bestie");
      return;
    }
    if (!form.email.trim()) {
      setError("email is required");
      return;
    }
    if (form.password.length < 6) {
      setError("password must be at least 6 characters");
      return;
    }

    setLoading(true);

    try {
      // 1. register
      await client.post("/auth/register", {
        name: form.name,
        email: form.email,
        password: form.password,
      });

      // 2. immediately login after register
      const loginRes = await client.post("/auth/login", {
        email: form.email,
        password: form.password,
      });

      const { access_token, name, role } = loginRes.data;

      // 3. save to context + localStorage
      login(access_token, { name, email: form.email, role });

      // 4. redirect to dashboard
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const msg = err.response?.data?.detail;
      if (msg === "Email already registered") {
        setError("this email is already taken. try logging in instead.");
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
            Create your account
          </h1>
          <p className="text-sm text-white/40">join the gang. it's free fr.</p>
        </div>

        {/* form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* name */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-white/50 uppercase tracking-widest">
              Name
            </label>
            <input
              name="name"
              type="text"
              placeholder="Ankit"
              value={form.name}
              onChange={handleChange}
              className="bg-[#1a1a1a] border border-white/10 rounded-xl px-4 py-3 text-sm font-mono text-white placeholder-white/20 outline-none focus:border-white/30 transition-colors"
            />
          </div>

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
              placeholder="min 6 characters"
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
                creating account...
              </span>
            ) : (
              "Create account ✦"
            )}
          </button>
        </form>

        {/* divider */}
        <div className="flex items-center gap-3 my-6">
          <div className="flex-1 h-px bg-white/10" />
          <span className="text-xs text-white/20">or</span>
          <div className="flex-1 h-px bg-white/10" />
        </div>

        {/* login link */}
        <p className="text-center text-sm text-white/40">
          already have an account?{" "}
          <Link
            to="/login"
            className="text-white font-medium hover:text-accent transition-colors"
          >
            log in
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
