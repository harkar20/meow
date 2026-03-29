import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { motion } from "framer-motion";
import { sessionApi } from "../api/endpoints";
import {
  Shield, AlertTriangle, CheckCircle, XCircle,
  TrendingUp, TrendingDown, Minus, Download, RotateCcw,
  Activity, MessageSquare, ChevronRight
} from "lucide-react";

const RISK_CONFIG = {
  low:      { color: "var(--risk-low)",      bg: "rgba(16,185,129,0.08)",  border: "rgba(16,185,129,0.25)",  icon: CheckCircle,   label: "LOW RISK" },
  medium:   { color: "var(--risk-medium)",   bg: "rgba(245,158,11,0.08)",   border: "rgba(245,158,11,0.25)",   icon: AlertTriangle, label: "MEDIUM RISK" },
  high:     { color: "var(--risk-high)",     bg: "rgba(249,115,22,0.08)",   border: "rgba(249,115,22,0.25)",   icon: AlertTriangle, label: "HIGH RISK" },
  critical: { color: "var(--risk-critical)", bg: "rgba(239,68,68,0.08)",    border: "rgba(239,68,68,0.25)",    icon: XCircle,       label: "CRITICAL" },
};

const TRAJECTORY_CONFIG = {
  stable:    { icon: Minus,         color: "var(--risk-low)",    cls: "badge-stable",    label: "STABLE" },
  worsening: { icon: TrendingDown,  color: "var(--risk-critical)",cls: "badge-worsening", label: "WORSENING" },
  improving: { icon: TrendingUp,    color: "var(--accent-blue)", cls: "badge-improving", label: "IMPROVING" },
  new_onset: { icon: Activity,      color: "var(--risk-medium)", cls: "badge-medium",    label: "NEW ONSET" },
};

export default function ResultPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState("patient");

  const { data, isLoading, error } = useQuery({
    queryKey: ["result", sessionId],
    queryFn: () => sessionApi.getResult(sessionId).then((r) => r.data),
  });

  if (isLoading) return (
    <div className="page-center" style={{ flexDirection: "column", gap: 16 }}>
      <div className="spinner spinner-lg" />
      <p style={{ color: "var(--text-secondary)" }}>Running clinical inference…</p>
    </div>
  );

  if (error) return (
    <div className="page-center">
      <div style={{ textAlign: "center", color: "#f87171" }}>Failed to load results. <button className="btn btn-secondary btn-sm" onClick={() => navigate("/dashboard")}>Go Home</button></div>
    </div>
  );

  const risk = RISK_CONFIG[data?.risk_tier] || RISK_CONFIG.medium;
  const RiskIcon = risk.icon;
  const traj = data?.trajectory_label ? TRAJECTORY_CONFIG[data.trajectory_label] : null;
  const TrajIcon = traj?.icon;

  return (
    <div className="page-container" style={{ maxWidth: 780 }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>

        {/* View Mode Toggle */}
        <div style={{ display: "flex", justifyContent: "center", marginBottom: "1.5rem" }}>
          <div style={{ display: "inline-flex", background: "var(--bg-subtle)", borderRadius: "100px", padding: 4, border: "1px solid var(--border-color)" }}>
            <button 
              onClick={() => setViewMode("patient")}
              style={{ padding: "8px 16px", borderRadius: "100px", border: "none", background: viewMode === "patient" ? "var(--text-primary)" : "transparent", color: viewMode === "patient" ? "var(--bg-base)" : "var(--text-muted)", cursor: "pointer", fontWeight: 600, fontSize: "0.85rem", transition: "all 0.2s" }}
            >
              Patient Overview
            </button>
            <button 
              onClick={() => setViewMode("doctor")}
              style={{ padding: "8px 16px", borderRadius: "100px", border: "none", background: viewMode === "doctor" ? "var(--text-primary)" : "transparent", color: viewMode === "doctor" ? "var(--bg-base)" : "var(--text-muted)", cursor: "pointer", fontWeight: 600, fontSize: "0.85rem", transition: "all 0.2s" }}
            >
              Doctor Detailed View
            </button>
          </div>
        </div>

        {/* Risk tier hero */}
        <motion.div className="card" 
          initial={{ scale: 0.97 }} 
          animate={data?.risk_tier === "critical" ? { scale: [1, 1.02, 1], boxShadow: ["0px 0px 0px rgba(239,68,68,0)", "0px 0px 40px rgba(239,68,68,0.5)", "0px 0px 0px rgba(239,68,68,0)"] } : { scale: 1 }}
          transition={data?.risk_tier === "critical" ? { repeat: Infinity, duration: 1.5 } : {}}
          style={{ padding: "2rem", marginBottom: "1.5rem", textAlign: "center",
            background: risk.bg, borderColor: data?.risk_tier === "critical" ? "rgba(239,68,68,0.6)" : risk.border }}>
          <RiskIcon size={48} color={risk.color} style={{ marginBottom: 12 }} />
          <div style={{ fontSize: "0.75rem", letterSpacing: "0.15em", fontWeight: 700, color: risk.color, marginBottom: 8 }}>
            RISK ASSESSMENT
          </div>
          <div style={{ fontFamily: "'Plus Jakarta Sans',sans-serif", fontSize: "2.5rem", fontWeight: 900, color: risk.color, letterSpacing: "-0.03em", lineHeight: 1 }}>
            {risk.label}
          </div>
          <div style={{ marginTop: 12, color: "var(--text-secondary)", fontSize: "0.9rem" }}>
            Confidence: <strong style={{ color: "var(--text-primary)" }}>{((data?.risk_score || 0.5) * 100).toFixed(0)}%</strong>
          </div>

          {traj && (
            <div style={{ marginTop: 14, display: "inline-flex", alignItems: "center", gap: 6 }}>
              <span className={`badge ${traj.cls}`}>
                <TrajIcon size={11} /> {traj.label}
              </span>
              {data.trajectory_score != null && (
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  escalation score: {(data.trajectory_score * 100).toFixed(0)}%
                </span>
              )}
            </div>
          )}
        </motion.div>

        <div className="grid-2" style={{ marginBottom: "1.5rem" }}>
          {/* Top conditions */}
          {viewMode === "doctor" && (
            <div className="card" style={{ padding: "1.5rem" }}>
              <h3 style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: "1rem", display: "flex", alignItems: "center", gap: 6 }}>
                <Activity size={13} /> Differential Diagnosis
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {(data?.top_conditions || []).map((cond, i) => (
                  <div key={i}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                      <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>{cond.name}</span>
                      <span style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--accent-blue-light)" }}>
                        {((cond.confidence || 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="progress-bar-track" style={{ background: "var(--bg-subtle)" }}>
                      <motion.div className="progress-bar-fill"
                        initial={{ width: 0 }}
                        animate={{ width: `${(cond.confidence || 0) * 100}%` }}
                        transition={{ duration: 0.8, delay: i * 0.15 }}
                        style={{ background: i === 0 ? "var(--text-primary)" : "var(--text-muted)" }}
                      />
                    </div>
                    {cond.icd10 && (
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: 2 }}>ICD-10: {cond.icd10}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Reasoning & action */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem", gridColumn: viewMode === "patient" ? "1 / -1" : "auto" }}>
            <div className="card" style={{ padding: "1.5rem", flex: 1, border: data?.risk_tier === "critical" ? "1px solid rgba(239,68,68,0.5)" : "1px solid var(--border-color)" }}>
              <h3 style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "0.08em", color: data?.risk_tier === "critical" ? "var(--risk-critical)" : "var(--text-muted)", marginBottom: "1rem", display: "flex", alignItems: "center", gap: 6 }}>
                <Shield size={13} /> {viewMode === "patient" ? "Assessment & Advice" : "Clinical Action Plan"}
              </h3>
              
              {data?.risk_tier === "low" && viewMode === "patient" && (
                <div style={{ padding: "12px", background: "rgba(16,185,129,0.1)", borderRadius: "8px", marginBottom: "1rem", color: "var(--risk-low)", fontWeight: "bold" }}>
                  🌿 Chill out! The AI sees no alarming red flags. You can relax and take it easy.
                </div>
              )}

              <p style={{ fontSize: viewMode === "patient" ? "1.05rem" : "0.95rem", lineHeight: 1.6, color: "var(--text-primary)", fontWeight: 500, whiteSpace: "pre-line" }}>
                {viewMode === "patient" ? (data?.patient_explanation || data?.recommended_action) : (data?.doctor_explanation || data?.recommended_action)}
              </p>
            </div>

            {viewMode === "doctor" && (data?.behavioral_flags || []).length > 0 && (
              <div className="card" style={{ padding: "1.5rem" }}>
                <h3 style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: "1rem", display: "flex", alignItems: "center", gap: 6 }}>
                  <MessageSquare size={13} /> Behavioral Signals
                </h3>
                <ul style={{ display: "flex", flexDirection: "column", gap: 6, listStyle: "none" }}>
                  {data.behavioral_flags.map((flag, i) => (
                    <li key={i} style={{ fontSize: "0.85rem", color: "var(--text-secondary)", paddingLeft: 14, position: "relative" }}>
                      <span style={{ position: "absolute", left: 0, top: "50%", transform: "translateY(-50%)", width: 5, height: 5, borderRadius: "50%", background: "var(--accent-cyan)", display: "block" }} />
                      {flag}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Reasoning chain */}
        {viewMode === "doctor" && (data?.reasoning_chain || []).length > 0 && (
          <div className="card" style={{ padding: "1.5rem", marginBottom: "1.5rem" }}>
            <h3 style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: "1rem" }}>
              Clinical Reasoning
            </h3>
            <ol style={{ display: "flex", flexDirection: "column", gap: 8, paddingLeft: 20 }}>
              {data.reasoning_chain.map((step, i) => (
                <li key={i} style={{ fontSize: "0.88rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                  {step}
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Actions */}
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <button className="btn btn-primary" onClick={() => navigate("/interview")} style={{ gap: 8 }}>
            <RotateCcw size={16} /> New Assessment
          </button>
          <button className="btn btn-secondary" onClick={() => navigate("/history")} style={{ gap: 8 }}>
            <Activity size={16} /> View History
          </button>
        </div>

        {/* Disclaimer */}
        <div style={{ marginTop: "2.5rem", padding: "1.25rem", borderTop: "1px solid var(--border-color)", fontSize: "0.8rem", color: "var(--text-muted)", lineHeight: 1.6, textAlign: "center" }}>
          Meowmeow is an informational probabilistic engine. Always consult a qualified healthcare provider for final medical diagnostics.
        </div>
      </motion.div>
    </div>
  );
}
