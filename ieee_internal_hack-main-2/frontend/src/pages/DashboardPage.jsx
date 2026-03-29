import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuthStore } from "../store/authStore";
import { useQuery } from "@tanstack/react-query";
import { sessionApi } from "../api/endpoints";
import { Cat, Activity, Clock, TrendingUp, ChevronRight, Shield, Zap, Eye } from "lucide-react";
import { format } from "date-fns";

const RISK_COLORS = { low: "var(--risk-low)", medium: "var(--risk-medium)", high: "var(--risk-high)", critical: "var(--risk-critical)" };

export default function DashboardPage() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const { data: historyData } = useQuery({ queryKey: ["history"], queryFn: () => sessionApi.getHistory().then(r => r.data) });

  const history = historyData || [];
  const lastSession = history[0];
  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 18) return "Good afternoon";
    return "Good evening";
  };

  const features = [
    { icon: Cat, title: "Adaptive Interview", desc: "Dynamic clinical questions, not a static form" },
    { icon: Activity, title: "Intensity Detection", desc: "Captures how you write, not just what you write" },
    { icon: Shield, title: "Bayesian Inference", desc: "Calibrated probabilistic risk assessment" },
    { icon: Zap, title: "Speech Input", desc: "Speak your answers naturally via microphone" },
    { icon: Eye, title: "Behavioral Analysis", desc: "Detects hesitation and clinical emphasis passively" },
    { icon: TrendingUp, title: "Temporal Tracking", desc: "Compares visits to detect escalating patterns" },
  ];

  return (
    <div className="page-container">
      {/* Hero */}
      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}>
        <div style={{ marginBottom: "4rem", marginTop: "2rem" }}>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem", marginBottom: 12, letterSpacing: "0.02em" }}>
            {greeting()}, <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>{user?.full_name?.split(" ")[0] || "there"}</span>
          </p>
          <h1 style={{ fontFamily: "'Plus Jakarta Sans',sans-serif", fontSize: "clamp(2.5rem,6vw,4rem)", fontWeight: 800, letterSpacing: "-0.05em", lineHeight: 1.05, marginBottom: "1.5rem", color: "var(--text-primary)" }}>
            Intelligence,<br />
            <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>refined for your health.</span>
          </h1>
          <p style={{ color: "var(--text-secondary)", maxWidth: 500, fontSize: "1.1rem", marginBottom: "3rem", lineHeight: 1.8 }}>
            Meowmeow interviews you conversationally, extracting highly subtle clinical signals to evaluate your systemic wellbeing.
          </p>
          <motion.button
            className="btn btn-primary btn-lg"
            onClick={() => navigate("/interview")}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            style={{ gap: 12, fontSize: "1rem", padding: "1.25rem 2.5rem" }}
          >
            <Cat size={20} /> Begin Assessment
            <ChevronRight size={18} />
          </motion.button>
        </div>

        {/* Stats row */}
        {history.length > 0 && (
          <div className="grid-3" style={{ marginBottom: "2.5rem" }}>
            {[
              { label: "Total Assessments", value: history.length, icon: Activity },
              { label: "Last Risk Tier", value: lastSession?.risk_tier?.toUpperCase() || "—", icon: Shield,
                color: RISK_COLORS[lastSession?.risk_tier] },
              { label: "Last Visit", value: lastSession?.created_at ? format(new Date(lastSession.created_at), "MMM d, yyyy") : "—", icon: Clock },
            ].map((stat, i) => (
              <motion.div key={i} className="card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
                style={{ padding: "1.5rem", display: "flex", flexDirection: "column", gap: 8 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--text-secondary)", fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  <stat.icon size={14} /> {stat.label}
                </div>
                <div style={{ fontSize: "1.5rem", fontWeight: 800, color: stat.color || "var(--text-primary)", fontFamily: "'Plus Jakarta Sans',sans-serif" }}>
                  {stat.value}
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {/* Last session CTA */}
        {lastSession && (
          <motion.div className="card card-glow" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
            style={{ padding: "1.5rem", marginBottom: "2.5rem", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
            <div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>Last Assessment</div>
              <div style={{ fontWeight: 700, fontSize: "1.05rem" }}>{lastSession.top_condition || "Assessment completed"}</div>
              <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: 2 }}>
                {lastSession.created_at ? format(new Date(lastSession.created_at), "PPP") : ""}
              </div>
            </div>
            <button className="btn btn-secondary" onClick={() => navigate(`/result/${lastSession.session_id}`)}>
              View Results <ChevronRight size={16} />
            </button>
          </motion.div>
        )}

        {/* Features grid */}
        <div style={{ marginBottom: "1rem" }}>
          <h2 style={{ fontFamily: "'Plus Jakarta Sans',sans-serif", fontSize: "1.25rem", fontWeight: 700, marginBottom: "1.25rem", color: "var(--text-secondary)" }}>
            Platform Capabilities
          </h2>
          <div className="grid-3">
            {features.map((f, i) => (
              <motion.div key={i} className="card" initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 + i * 0.1, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                style={{ padding: "1.5rem" }}>
                <div style={{ display: "inline-flex", padding: 12, borderRadius: "50%", background: "var(--bg-subtle)", marginBottom: 16 }}>
                  <f.icon size={18} color="var(--text-primary)" />
                </div>
                <div style={{ fontWeight: 600, marginBottom: 4, fontSize: "0.95rem" }}>{f.title}</div>
                <div style={{ color: "var(--text-secondary)", fontSize: "0.82rem", lineHeight: 1.5 }}>{f.desc}</div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Disclaimer */}
        <div style={{ marginTop: "4rem", padding: "1.25rem", borderTop: "1px solid var(--border-color)", fontSize: "0.8rem", color: "var(--text-muted)", lineHeight: 1.6, textAlign: "center" }}>
          Meowmeow is an informational probabilistic engine. Always consult a qualified healthcare provider for final medical diagnostics.
        </div>
      </motion.div>
    </div>
  );
}
