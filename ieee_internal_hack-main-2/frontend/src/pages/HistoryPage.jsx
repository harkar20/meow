import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { sessionApi } from "../api/endpoints";
import { format } from "date-fns";
import { Clock, ChevronRight, Brain, Activity } from "lucide-react";

const RISK_COLORS = {
  low: "var(--risk-low)", medium: "var(--risk-medium)",
  high: "var(--risk-high)", critical: "var(--risk-critical)"
};
const RISK_BG = {
  low: "rgba(16,185,129,0.1)", medium: "rgba(245,158,11,0.1)",
  high: "rgba(249,115,22,0.1)", critical: "rgba(239,68,68,0.1)"
};

export default function HistoryPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({
    queryKey: ["history"],
    queryFn: () => sessionApi.getHistory().then((r) => r.data),
  });

  const sessions = data || [];

  return (
    <div className="page-container" style={{ maxWidth: 800 }}>
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "2rem", flexWrap: "wrap", gap: 12 }}>
          <div>
            <h1 style={{ fontFamily: "'Plus Jakarta Sans',sans-serif", fontSize: "1.75rem", fontWeight: 800, letterSpacing: "-0.03em" }}>
              Assessment History
            </h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginTop: 4 }}>
              Your past clinical interviews and risk outputs
            </p>
          </div>
          <button className="btn btn-primary" onClick={() => navigate("/interview")} style={{ gap: 8 }}>
            <Brain size={16} /> New Assessment
          </button>
        </div>

        {isLoading && (
          <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}>
            <div className="spinner spinner-lg" />
          </div>
        )}

        {!isLoading && sessions.length === 0 && (
          <div className="card" style={{ padding: "3rem", textAlign: "center" }}>
            <Activity size={48} color="var(--text-muted)" style={{ marginBottom: 16, opacity: 0.5 }} />
            <h2 style={{ fontWeight: 700, marginBottom: 8 }}>No assessments yet</h2>
            <p style={{ color: "var(--text-secondary)", marginBottom: 20 }}>
              Start your first clinical interview to see your history here.
            </p>
            <button className="btn btn-primary" onClick={() => navigate("/interview")}>
              Start First Assessment
            </button>
          </div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {sessions.map((s, i) => (
            <motion.div key={s.session_id}
              className="card"
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.06 }}
              style={{
                padding: "1.25rem 1.5rem",
                display: "flex", alignItems: "center", gap: "1rem",
                cursor: s.status === "completed" ? "pointer" : "default"
              }}
              onClick={() => s.status === "completed" && navigate(`/result/${s.session_id}`)}
              whileHover={s.status === "completed" ? { borderColor: "rgba(59,130,246,0.3)" } : {}}
            >
              {/* Risk indicator */}
              <div style={{
                width: 48, height: 48, borderRadius: 12, flexShrink: 0,
                background: RISK_BG[s.risk_tier] || "rgba(255,255,255,0.05)",
                border: `1px solid ${RISK_COLORS[s.risk_tier] || "var(--border)"}33`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "1.1rem", fontWeight: 900,
                color: RISK_COLORS[s.risk_tier] || "var(--text-muted)",
                fontFamily: "'Plus Jakarta Sans',sans-serif"
              }}>
                {s.risk_tier ? s.risk_tier[0].toUpperCase() : "?"}
              </div>

              {/* Info */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: "0.95rem", marginBottom: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {s.top_condition || "Assessment completed"}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--text-muted)", fontSize: "0.8rem" }}>
                  <Clock size={12} />
                  {s.created_at ? format(new Date(s.created_at), "MMM d, yyyy • h:mm a") : "—"}
                </div>
              </div>

              {/* Status badge */}
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span className={`badge badge-${s.risk_tier || "medium"}`}>
                  {s.risk_tier?.toUpperCase() || "—"}
                </span>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "capitalize" }}>
                  {s.status}
                </span>
                {s.status === "completed" && <ChevronRight size={16} color="var(--text-muted)" />}
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
