import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { sessionApi } from "../api/endpoints";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Globe, TrendingUp, AlertTriangle } from "lucide-react";

const CAT_COLORS = {
  fatigue: "#60a5fa", pain: "#f87171", respiratory: "#34d399",
  digestive: "#fbbf24", neurological: "#a78bfa", mood: "#f472b6",
  general: "#94a3b8"
};

export default function PopulationPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["population"],
    queryFn: () => sessionApi.populationSummary().then((r) => r.data),
  });

  const rows = data || [];

  // Aggregate by category
  const catCounts = rows.reduce((acc, r) => {
    acc[r.symptom_category] = (acc[r.symptom_category] || 0) + 1;
    return acc;
  }, {});
  const chartData = Object.entries(catCounts).map(([cat, count]) => ({ cat, count })).sort((a, b) => b.count - a.count);

  // Aggregate by city
  const cityCounts = rows.reduce((acc, r) => {
    if (r.city) acc[r.city] = (acc[r.city] || 0) + 1;
    return acc;
  }, {});
  const topCities = Object.entries(cityCounts).sort((a, b) => b[1] - a[1]).slice(0, 8);

  // Simple spike detection: avg + 2 stddev
  const values = chartData.map((d) => d.count);
  const avg = values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0;
  const stddev = values.length ? Math.sqrt(values.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / values.length) : 0;
  const spikeThreshold = avg + 2 * stddev;
  const spikes = chartData.filter((d) => d.count > spikeThreshold);

  return (
    <div className="page-container" style={{ maxWidth: 900 }}>
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>

        {/* Header */}
        <div style={{ marginBottom: "2rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
            <Globe size={22} color="var(--accent-blue)" />
            <h1 style={{ fontFamily: "'Plus Jakarta Sans',sans-serif", fontSize: "1.75rem", fontWeight: 800, letterSpacing: "-0.03em" }}>
              PopulationWatch
            </h1>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
            Anonymized aggregate symptom signals across Meowmeow users. No personal data is included.
          </p>
        </div>

        {/* Spike alert */}
        {spikes.length > 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            style={{ padding: "1rem 1.25rem", borderRadius: "var(--radius-md)", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.3)", marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: 10 }}>
            <AlertTriangle size={18} color="var(--risk-critical)" />
            <div>
              <strong style={{ color: "var(--risk-critical)", fontSize: "0.9rem" }}>Outbreak Alert</strong>
              <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginLeft: 8 }}>
                Elevated reports detected in: {spikes.map(s => s.cat).join(", ")}
              </span>
            </div>
          </motion.div>
        )}

        {isLoading && (
          <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}>
            <div className="spinner spinner-lg" />
          </div>
        )}

        {!isLoading && rows.length === 0 && (
          <div className="card" style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
            <Globe size={48} style={{ opacity: 0.3, marginBottom: 16 }} />
            <p>No population data yet. Complete assessments to contribute anonymized signals.</p>
          </div>
        )}

        {chartData.length > 0 && (
          <div className="grid-2" style={{ marginBottom: "1.5rem" }}>
            {/* Bar chart */}
            <div className="card" style={{ padding: "1.5rem" }}>
              <h3 style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: "1.25rem", display: "flex", alignItems: "center", gap: 6 }}>
                <TrendingUp size={13} /> Report Volume by Category
              </h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <XAxis dataKey="cat" tick={{ fill: "var(--text-muted)", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "var(--text-muted)", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: "#0f172a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: "0.8rem" }}
                    labelStyle={{ color: "var(--text-secondary)" }}
                    itemStyle={{ color: "var(--text-primary)" }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry) => (
                      <Cell key={entry.cat} fill={CAT_COLORS[entry.cat] || "#60a5fa"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Top cities */}
            <div className="card" style={{ padding: "1.5rem" }}>
              <h3 style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: "1.25rem", display: "flex", alignItems: "center", gap: 6 }}>
                <Globe size={13} /> Top Reporting Cities
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {topCities.map(([city, count], i) => {
                  const maxVal = topCities[0][1];
                  return (
                    <div key={city}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                        <span style={{ fontSize: "0.85rem", fontWeight: 500 }}>{city}</span>
                        <span style={{ fontSize: "0.85rem", color: "var(--accent-blue-light)", fontWeight: 700 }}>{count}</span>
                      </div>
                      <div className="progress-bar-track">
                        <motion.div className="progress-bar-fill"
                          initial={{ width: 0 }}
                          animate={{ width: `${(count / maxVal) * 100}%` }}
                          transition={{ duration: 0.8, delay: i * 0.1 }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Category breakdown cards */}
        {chartData.length > 0 && (
          <div>
            <h3 style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: "1rem" }}>
              Category Breakdown
            </h3>
            <div className="grid-3">
              {chartData.map((d, i) => (
                <motion.div key={d.cat} className="card" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
                  style={{ padding: "1rem 1.25rem", borderLeft: `3px solid ${CAT_COLORS[d.cat] || "#60a5fa"}` }}>
                  <div style={{ textTransform: "capitalize", fontWeight: 600, fontSize: "0.9rem", marginBottom: 4 }}>{d.cat}</div>
                  <div style={{ fontSize: "1.5rem", fontWeight: 800, color: CAT_COLORS[d.cat] || "#60a5fa", fontFamily: "'Plus Jakarta Sans',sans-serif" }}>
                    {d.count}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>reports</div>
                  {d.count > spikeThreshold && spikeThreshold > 0 && (
                    <div style={{ marginTop: 6, fontSize: "0.72rem", color: "var(--risk-critical)", display: "flex", alignItems: "center", gap: 4 }}>
                      <AlertTriangle size={10} /> Spike detected
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </div>
        )}

        <div style={{ marginTop: "2rem", fontSize: "0.78rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
          🔒 All data shown is fully anonymized. No personally identifiable information is stored or displayed. Location data is self-reported and city-level only.
        </div>
      </motion.div>
    </div>
  );
}
