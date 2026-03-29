import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { authApi } from "../api/endpoints";
import { useAuthStore } from "../store/authStore";
import { Brain, Mail, Lock, User, Eye, EyeOff, AlertCircle } from "lucide-react";

export default function RegisterPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [form, setForm] = useState({ email: "", password: "", full_name: "", age: "", sex: "" });
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleRegister = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const payload = { ...form, age: form.age ? parseInt(form.age) : undefined };
      const res = await authApi.register(payload);
      setAuth(res.data.user, res.data.access_token);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed.");
    } finally { setLoading(false); }
  };

  const handleGoogle = async () => {
    setError(""); setGoogleLoading(true);
    try {
      const res = await authApi.googleAuth("demo-token", "Demo Patient", null);
      setAuth(res.data.user, res.data.access_token);
      navigate("/dashboard");
    } catch (err) {
      setError("Google sign-in unavailable in demo mode.");
    } finally { setGoogleLoading(false); }
  };

  const strength = () => {
    const p = form.password;
    if (!p) return 0;
    let s = 0;
    if (p.length >= 8) s++;
    if (/[A-Z]/.test(p)) s++;
    if (/[0-9]/.test(p)) s++;
    if (/[^A-Za-z0-9]/.test(p)) s++;
    return s;
  };
  const s = strength();
  const strengthColors = ["", "#ef4444", "#f97316", "#f59e0b", "#10b981"];
  const strengthLabels = ["", "Weak", "Fair", "Good", "Strong"];

  return (
    <div className="page-center">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        style={{ width: "100%", maxWidth: 460 }}
      >
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div style={{
            display: "inline-flex", alignItems: "center", justifyContent: "center",
            width: 56, height: 56, borderRadius: 16,
            background: "linear-gradient(135deg, rgba(59,130,246,0.2), rgba(139,92,246,0.2))",
            border: "1px solid rgba(59,130,246,0.3)", marginBottom: "1rem"
          }}>
            <Brain size={28} color="var(--accent-blue)" />
          </div>
          <h1 style={{ fontFamily: "'Plus Jakarta Sans',sans-serif", fontSize: "1.75rem", fontWeight: 800, letterSpacing: "-0.03em", marginBottom: 8 }}>
            Create your account
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
            Start your intelligent health assessment
          </p>
        </div>

        <div className="card" style={{ padding: "2rem" }}>
          <button
            className="btn btn-google btn-full"
            onClick={handleGoogle}
            disabled={googleLoading}
            style={{ marginBottom: "1.25rem", fontSize: "0.95rem" }}
          >
            {googleLoading ? <div className="spinner" style={{ borderTopColor: "#4285f4" }} /> : (
              <svg width="20" height="20" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
            )}
            Continue with Google
          </button>

          <div className="form-divider">or register with email</div>

          {error && (
            <div style={{
              display: "flex", alignItems: "center", gap: 8,
              background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)",
              borderRadius: "var(--radius-md)", padding: "10px 14px",
              color: "#f87171", fontSize: "0.85rem", marginBottom: "1rem", marginTop: "0.5rem"
            }}>
              <AlertCircle size={16} /> {error}
            </div>
          )}

          <form onSubmit={handleRegister} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <div style={{ position: "relative" }}>
                <User size={16} style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
                <input name="full_name" type="text" className="form-input" placeholder="Jane Smith"
                  value={form.full_name} onChange={handleChange} style={{ paddingLeft: 42 }} />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Email address *</label>
              <div style={{ position: "relative" }}>
                <Mail size={16} style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
                <input name="email" type="email" required className="form-input" placeholder="you@example.com"
                  value={form.email} onChange={handleChange} style={{ paddingLeft: 42 }} />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Password *</label>
              <div style={{ position: "relative" }}>
                <Lock size={16} style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
                <input name="password" type={showPass ? "text" : "password"} required className="form-input"
                  placeholder="Min. 8 characters" value={form.password} onChange={handleChange}
                  style={{ paddingLeft: 42, paddingRight: 42 }} />
                <button type="button" onClick={() => setShowPass(!showPass)}
                  style={{ position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", display: "flex" }}>
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {form.password && (
                <div style={{ marginTop: 6 }}>
                  <div style={{ display: "flex", gap: 4, marginBottom: 4 }}>
                    {[1,2,3,4].map((i) => (
                      <div key={i} style={{ flex: 1, height: 3, borderRadius: 2, background: i <= s ? strengthColors[s] : "var(--border)", transition: "background 0.3s" }} />
                    ))}
                  </div>
                  <span style={{ fontSize: "0.75rem", color: strengthColors[s] }}>{strengthLabels[s]}</span>
                </div>
              )}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
              <div className="form-group">
                <label className="form-label">Age</label>
                <input name="age" type="number" min="1" max="120" className="form-input" placeholder="e.g. 28"
                  value={form.age} onChange={handleChange} />
              </div>
              <div className="form-group">
                <label className="form-label">Sex</label>
                <select name="sex" className="form-input" value={form.sex} onChange={handleChange}
                  style={{ cursor: "pointer" }}>
                  <option value="">Prefer not to say</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading} style={{ marginTop: 4 }}>
              {loading ? <><div className="spinner" /> Creating account...</> : "Create Account"}
            </button>
          </form>
        </div>

        <p style={{ textAlign: "center", marginTop: "1.25rem", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
          Already have an account?{" "}
          <Link to="/login" style={{ color: "var(--accent-blue-light)", fontWeight: 600, textDecoration: "none" }}>
            Sign in
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
