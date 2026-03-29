import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuthStore } from "../store/authStore";
import { useQuery } from "@tanstack/react-query";
import { authApi, sessionApi } from "../api/endpoints";
import { User, Activity, Clock, Shield, ChevronRight, Edit3, Check, Thermometer, ShieldAlert, HeartPulse } from "lucide-react";
import { format } from "date-fns";

export default function ProfilePage() {
  const { user, token, setAuth } = useAuthStore();
  const navigate = useNavigate();

  // Queries
  const { data: historyData, isLoading: historyLoading } = useQuery({ 
    queryKey: ["history"], 
    queryFn: () => sessionApi.getHistory().then(r => r.data) 
  });
  
  // Local state for health editable form
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [healthForm, setHealthForm] = useState({
    photo_url: user?.photo_url || "",
    weight: user?.weight || "",
    height: user?.height || "",
    blood_group: user?.blood_group || "",
    allergies: user?.allergies || "",
    medical_conditions: user?.medical_conditions || "",
  });

  const history = historyData || [];
  const initials = user?.full_name
    ? user.full_name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : user?.email?.[0]?.toUpperCase() || "?";

  const handleUpdate = async () => {
    setLoading(true);
    try {
      const res = await authApi.updateMe(healthForm);
      setAuth(res.data, token); // Update global Zustand state
      setEditing(false);
    } catch (err) {
      console.error("Failed to update health info:", err);
      alert("Failed to update profile.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container" style={{ paddingBottom: "4rem" }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        
        {/* Header Profile Card */}
        <div className="card" style={{ padding: "2.5rem", marginBottom: "3rem", display: "flex", alignItems: "center", gap: "2rem", flexWrap: "wrap", border: "none", background: "var(--bg-subtle)" }}>
          <div style={{ width: 90, height: 90, borderRadius: "50%", background: "var(--bg-base)", border: "1px solid var(--border-color)", display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden", fontSize: "1.75rem", fontWeight: 800, color: "var(--text-primary)" }}>
            {user?.photo_url 
              ? <img src={user.photo_url} alt="Profile" style={{ width: "100%", height: "100%", objectFit: "cover" }} referrerPolicy="no-referrer" />
              : initials}
          </div>
          <div>
            <h1 style={{ fontFamily: "'Plus Jakarta Sans',sans-serif", fontSize: "2rem", fontWeight: 800, margin: 0, color: "var(--text-primary)", letterSpacing: "-0.04em" }}>
              {user?.full_name || "Patient Profile"}
            </h1>
            <p style={{ color: "var(--text-secondary)", marginTop: 6, display: "flex", alignItems: "center", gap: 8, fontSize: "0.95rem" }}>
              <User size={16} /> {user?.email}
            </p>
          </div>
          <div style={{ marginLeft: "auto", display: "flex", gap: "1rem" }}>
             <div style={{ textAlign: "right" }}>
                <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", margin: 0 }}>Account Status</p>
                <div style={{ display: "inline-flex", alignItems: "center", gap: 4, color: "var(--risk-low)", fontSize: "0.85rem", fontWeight: 600, marginTop: 4 }}>
                  <Shield size={14} /> Verified
                </div>
             </div>
          </div>
        </div>

        <div className="grid-2-col" style={{ gap: "2rem" }}>
          
          {/* Health Stats Panel */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <h2 style={{ fontFamily: "'Plus Jakarta Sans',sans-serif", fontSize: "1.25rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
                <Activity size={20} color="var(--accent-blue)" /> Basic Health Metrics
              </h2>
              <button onClick={() => editing ? handleUpdate() : setEditing(true)} className={`btn ${editing ? 'btn-primary' : 'btn-secondary'} btn-sm`} disabled={loading} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                {editing ? <><Check size={14}/> Save Changes {loading && <div className="spinner" style={{ width: 12, height: 12 }}/>}</> : <><Edit3 size={14}/> Edit Profile</>}
              </button>
            </div>
            
            <div className="card" style={{ padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              {editing && (
                <>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label" style={{ display: "flex", alignItems: "center", gap: 6 }}>Profile Picture URL</label>
                    <input type="url" className="form-input" placeholder="https://example.com/my-photo.jpg" value={healthForm.photo_url} onChange={e => setHealthForm({...healthForm, photo_url: e.target.value})} />
                  </div>
                  <div className="form-divider" style={{ margin: "0.25rem 0" }}></div>
                </>
              )}
                
              <div className="grid-2" style={{ gap: "1rem", display: "grid", gridTemplateColumns: "1fr 1fr" }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Blood Group</label>
                  <input type="text" className="form-input" placeholder="e.g. O+" value={healthForm.blood_group} onChange={e => setHealthForm({...healthForm, blood_group: e.target.value})} disabled={!editing} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Weight (kg)</label>
                  <input type="text" className="form-input" placeholder="e.g. 72" value={healthForm.weight} onChange={e => setHealthForm({...healthForm, weight: e.target.value})} disabled={!editing} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Height (cm)</label>
                  <input type="text" className="form-input" placeholder="e.g. 175" value={healthForm.height} onChange={e => setHealthForm({...healthForm, height: e.target.value})} disabled={!editing} />
                </div>
              </div>

              <div className="form-divider" style={{ margin: "0.5rem 0" }}></div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ display: "flex", alignItems: "center", gap: 6 }}><ShieldAlert size={14} color="var(--risk-medium)" /> Known Allergies</label>
                <input type="text" className="form-input" placeholder="e.g. Penicillin, Peanuts (or 'None')" value={healthForm.allergies} onChange={e => setHealthForm({...healthForm, allergies: e.target.value})} disabled={!editing} />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ display: "flex", alignItems: "center", gap: 6 }}><HeartPulse size={14} color="var(--risk-critical)" /> Pre-existing Medical Conditions</label>
                <textarea className="form-input" rows={2} placeholder="e.g. Type 2 Diabetes, Hypertension (or 'None')" value={healthForm.medical_conditions} onChange={e => setHealthForm({...healthForm, medical_conditions: e.target.value})} disabled={!editing} style={{ resize: "vertical" }} />
              </div>
            </div>
          </div>

          {/* Assessment History Mini-Panel */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <h2 style={{ fontFamily: "'Plus Jakarta Sans',sans-serif", fontSize: "1.25rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
                <Clock size={20} color="var(--accent-purple)" /> Recent Assessments
              </h2>
              <Link to="/history" className="btn btn-secondary btn-sm" style={{ display: "flex", alignItems: "center", gap: 4 }}>
                View All <ChevronRight size={14} />
              </Link>
            </div>

            <div className="card" style={{ padding: "0.5rem" }}>
              {historyLoading ? (
                <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>Loading history...</div>
              ) : history.length === 0 ? (
                <div style={{ padding: "2rem", textAlign: "center" }}>
                  <p style={{ color: "var(--text-secondary)", marginBottom: "1rem" }}>No assessments found.</p>
                  <button className="btn btn-primary" onClick={() => navigate("/interview")}>Take Assessment</button>
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column" }}>
                  {history.slice(0, 4).map((record, i) => (
                    <motion.div key={record.session_id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
                      onClick={() => navigate(`/result/${record.session_id}`)}
                      style={{ padding: "1rem 1.25rem", display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: i < 3 ? "1px solid var(--border-color)" : "none", cursor: "pointer", borderRadius: "var(--radius-md)" }}
                      whileHover={{ background: "rgba(255,255,255,0.02)" }}
                    >
                      <div>
                        <div style={{ fontWeight: 600, fontSize: "0.95rem", color: "var(--text-primary)" }}>{record.top_condition || "Assessment"}</div>
                        <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: 4 }}>
                          {format(new Date(record.created_at), "MMM d, yyyy • h:mm a")}
                        </div>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                        <div style={{ padding: "4px 10px", borderRadius: 20, fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", background: `color-mix(in srgb, var(--risk-${record.risk_tier}) 15%, transparent)`, color: `var(--risk-${record.risk_tier})` }}>
                          {record.risk_tier}
                        </div>
                        <ChevronRight size={16} color="var(--text-muted)" />
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>

        </div>
      </motion.div>
    </div>
  );
}
