"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { login, register, getMe } from "@/lib/api";
import { Award, Lock, Mail, User, ShieldAlert, ArrowRight, UserPlus } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);

  // Form states
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [department, setDepartment] = useState("");
  const [division, setDivision] = useState("");

  // Check if already authenticated — skip network call if no token stored
  useEffect(() => {
    async function checkAuth() {
      // If no token in storage, no need to hit the network
      if (typeof window !== "undefined" && !localStorage.getItem("token")) {
        setCheckingAuth(false);
        return;
      }
      try {
        await getMe();
        router.push("/chat");
      } catch (err) {
        // Token invalid or backend unreachable — clear it and show login
        if (typeof window !== "undefined") localStorage.removeItem("token");
        setCheckingAuth(false);
      }
    }
    checkAuth();
  }, [router]);


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isLogin) {
        await login(email, password);
        router.push("/chat");
      } else {
        await register({
          employee_id: employeeId,
          name,
          email,
          password,
          role: "employee",
          division: division || null,
          department: department || null
        });
        // Success - toggle to login
        setIsLogin(true);
        setError("Account registered successfully! Please log in.");
        setPassword("");
      }
    } catch (err: any) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  if (checkingAuth) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
          <span className="text-sm font-medium text-slate-500">Loading portal...</span>
        </div>
      </div>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-tr from-slate-900 via-slate-800 to-navy-dark p-6">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-100/10">
        {/* Banner Title */}
        <div className="bg-gradient-to-br from-slate-800 to-slate-950 p-8 text-center text-white border-b border-slate-800">
          <div className="inline-flex p-3 rounded-2xl bg-white/10 mb-4 backdrop-blur-md">
            <Award className="w-8 h-8 text-amber-400" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight font-sans">
            Indian Railways
          </h1>
          <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-semibold">
            Administrative AI Assessment Portal
          </p>
        </div>

        {/* Auth Body */}
        <div className="p-8">
          {/* Tab Selector */}
          <div className="flex rounded-xl bg-slate-100 p-1 mb-6">
            <button
              onClick={() => { setIsLogin(true); setError(null); }}
              className={`flex-1 py-2 px-3 rounded-lg text-sm font-semibold transition-all ${isLogin
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-500 hover:text-slate-800"
                }`}
            >
              Sign In
            </button>
            <button
              onClick={() => { setIsLogin(false); setError(null); }}
              className={`flex-1 py-2 px-3 rounded-lg text-sm font-semibold transition-all ${!isLogin
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-500 hover:text-slate-800"
                }`}
            >
              Register
            </button>
          </div>

          {/* Error / Success Alert */}
          {error && (
            <div className={`flex gap-2 text-xs rounded-xl p-3 mb-5 border ${error.includes("successfully")
                ? "bg-emerald-50 text-emerald-800 border-emerald-100"
                : "bg-rose-50 text-rose-800 border-rose-100"
              }`}>
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <>
                <div className="space-y-1">
                  <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">
                    Full Name
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-2.5 w-4.5 h-4.5 text-slate-400" />
                    <input
                      type="text"
                      required
                      placeholder="e.g. John Doe"
                      value={name}
                      onChange={e => setName(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-slate-500/20"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">
                    Employee ID
                  </label>
                  <div className="relative">
                    <UserPlus className="absolute left-3 top-2.5 w-4.5 h-4.5 text-slate-400" />
                    <input
                      type="text"
                      required
                      placeholder="e.g. EMP9982"
                      value={employeeId}
                      onChange={e => setEmployeeId(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-slate-500/20"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">
                      Department
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Mechanical"
                      value={department}
                      onChange={e => setDepartment(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-slate-500/20"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">
                      Division
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Sealdah"
                      value={division}
                      onChange={e => setDivision(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-slate-500/20"
                    />
                  </div>
                </div>
              </>
            )}

            <div className="space-y-1">
              <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 w-4.5 h-4.5 text-slate-400" />
                <input
                  type="email"
                  required
                  placeholder="e.g. employee@railway.gov.in"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-slate-500/20"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 w-4.5 h-4.5 text-slate-400" />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-slate-500/20"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-tr from-slate-800 to-slate-900 hover:from-slate-700 hover:to-slate-800 text-white rounded-xl py-2.5 text-sm font-semibold shadow-md transition-all disabled:opacity-50 mt-4"
            >
              <span>{loading ? "Processing..." : isLogin ? "Sign In" : "Register"}</span>
              {!loading && <ArrowRight className="w-4 h-4" />}
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}