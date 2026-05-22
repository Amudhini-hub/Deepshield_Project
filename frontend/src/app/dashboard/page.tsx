"use client";

import { useEffect, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Legend,
} from "recharts";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import { api, getAnalytics } from "@/lib/api";
import type { AnalyticsSummary, DetailedHealth } from "@/lib/api";
import { ShieldCheck, Zap, Target, Eye, Loader2, WifiOff, Shield } from "lucide-react";

const C = {
  blue: "#003580",
  blueLight: "#004aad",
  gold: "#C8922A",
  goldLight: "#FDF3E1",
  bg: "#f0f4f8",
  card: "#ffffff",
  heading: "#1a2332",
  body: "#4a5568",
  muted: "#718096",
  border: "#d1dce8",
  success: "#16a34a",
  danger: "#dc2626",
  amber: "#d97706",
};

function timeAgo(iso: string): string {
  if (!iso) return "—";
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

const verdictStyle = (v: string): React.CSSProperties => {
  if (v === "REAL") return { background: "#dcfce7", color: "#15803d" };
  if (v === "BLOCK") return { background: "#fee2e2", color: C.danger };
  return { background: "#fef3c7", color: "#92400e" };
};

function EmptyChart({ label }: { label: string }) {
  return (
    <div style={{ height: 220, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 8 }}>
      <div style={{ fontSize: 13, color: C.muted }}>{label}</div>
    </div>
  );
}

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [health, setHealth]       = useState<DetailedHealth | null>(null);
  const [loading, setLoading]     = useState(true);
  const [offline, setOffline]     = useState(false);

  useEffect(() => {
    api.get<DetailedHealth>("/health/status").then((r) => setHealth(r.data)).catch(() => {});
    getAnalytics()
      .then((data) => { setAnalytics(data); setOffline(false); })
      .catch(() => { setOffline(true); })
      .finally(() => setLoading(false));
  }, []);

  const mlStatus = health?.components.ml_services ?? "checking…";
  const dbStatus = health?.components.database.status ?? "unknown";
  const redisOk  = health?.components.redis?.connected ?? health?.components.redis?.status === "connected";
  const env      = health?.environment ?? "—";
  const apiVer   = health?.version ?? "—";

  const threatRate = analytics
    ? ((analytics.threats_blocked / Math.max(analytics.total_scans, 1)) * 100).toFixed(1)
    : null;

  const chartData = analytics?.last_7_days ?? [];
  const recentData = analytics?.recent_detections ?? [];

  const distributionData = analytics
    ? [
        { name: "Real",     value: analytics.total_scans - analytics.threats_blocked, fill: C.success },
        { name: "Deepfake", value: analytics.threats_blocked,                          fill: C.danger  },
      ]
    : [];

  const card: React.CSSProperties = {
    background: C.card,
    border: `1px solid ${C.border}`,
    borderRadius: 12,
    padding: "1.5rem",
  };

  if (loading) {
    return (
      <div style={{ background: C.bg, minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <Nav />
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 12 }}>
          <Loader2 size={24} color={C.blue} className="animate-spin" />
          <span style={{ fontSize: 14, color: C.body }}>Loading security dashboard…</span>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div style={{ background: C.bg, color: C.heading, minHeight: "100vh" }}>
      <Nav />

      {/* Portal header strip */}
      <div
        style={{
          background: C.goldLight,
          borderBottom: `1px solid #e8d5a8`,
          padding: "0.625rem 2rem",
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
        }}
      >
        <Shield size={13} color={C.gold} />
        <span style={{ fontSize: 12, fontWeight: 600, color: C.blue }}>
          Indian Overseas Bank &nbsp;·&nbsp; Security Operations Dashboard
        </span>
      </div>

      <div className="px-4 md:px-12 py-8 md:py-10" style={{ maxWidth: 1100, margin: "0 auto" }}>

        {/* ── Header ── */}
        <div style={{ marginBottom: "1.75rem" }}>
          <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase", marginBottom: 8 }}>
            Security Analytics
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "1rem" }}>
            <h1 style={{ fontSize: 26, fontWeight: 700, color: C.heading }}>Detection Dashboard</h1>

            {/* Component health pills */}
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              {[
                { label: `API v${apiVer}`,                   ok: !!health },
                { label: `DB ${dbStatus}`,                   ok: dbStatus === "healthy" },
                { label: `Redis ${redisOk ? "on" : "off"}`, ok: !!redisOk },
                { label: `ML ${mlStatus}`,                   ok: mlStatus === "available" },
                { label: env,                                 ok: true },
              ].map(({ label, ok }) => (
                <div
                  key={label}
                  style={{
                    display: "flex", alignItems: "center", gap: 5,
                    fontSize: 11, color: C.body, background: C.card,
                    border: `1px solid ${C.border}`, borderRadius: 8,
                    padding: "4px 10px",
                  }}
                >
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: ok ? C.success : C.danger, display: "inline-block", flexShrink: 0 }} />
                  {label}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Offline banner ── */}
        {offline && (
          <div
            style={{
              background: "#fef3c7",
              border: "1px solid #fcd34d",
              borderRadius: 10,
              padding: "0.875rem 1rem",
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginBottom: "1.5rem",
            }}
          >
            <WifiOff size={16} color={C.amber} style={{ flexShrink: 0 }} />
            <div style={{ fontSize: 13, color: "#78350f" }}>
              Backend unreachable — start the API server and Celery worker to see live data.
            </div>
          </div>
        )}

        {/* ── Stat cards ── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {[
            {
              Icon: ShieldCheck,
              label: "Total Scans",
              value: analytics ? analytics.total_scans.toLocaleString() : "—",
              sub: "All time",
              color: C.blue,
              bg: "#e8f0fe",
              borderColor: C.blue,
            },
            {
              Icon: Zap,
              label: "Threats Blocked",
              value: analytics ? analytics.threats_blocked.toLocaleString() : "—",
              sub: threatRate !== null ? `${threatRate}% threat rate` : "No data yet",
              color: C.danger,
              bg: "#fee2e2",
              borderColor: C.danger,
            },
            {
              Icon: Target,
              label: "Avg Confidence",
              value: analytics ? `${analytics.avg_confidence}%` : "—",
              sub: "Ensemble model",
              color: C.success,
              bg: "#dcfce7",
              borderColor: C.success,
            },
            {
              Icon: Eye,
              label: "Liveness Checks",
              value: analytics ? analytics.liveness_count.toLocaleString() : "—",
              sub: "Anti-spoofing scans",
              color: C.gold,
              bg: C.goldLight,
              borderColor: C.gold,
            },
          ].map(({ Icon, label, value, sub, color, bg, borderColor }) => (
            <div key={label} style={{ ...card, borderTop: `3px solid ${borderColor}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
                <div style={{ fontSize: 12, color: C.muted, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>{label}</div>
                <div style={{ width: 34, height: 34, borderRadius: 8, background: bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <Icon size={17} color={color} />
                </div>
              </div>
              <div style={{ fontSize: 28, fontWeight: 700, color: C.heading }}>{value}</div>
              <div style={{ fontSize: 11, color: C.muted, marginTop: 4 }}>{sub}</div>
            </div>
          ))}
        </div>

        {/* ── Charts ── */}
        <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-4 mb-6">

          {/* Area chart */}
          <div style={card}>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.heading, marginBottom: "1.25rem" }}>
              Authentication Attempts — Last 7 Days
            </div>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor={C.blue} stopOpacity={0.15} />
                      <stop offset="95%" stopColor={C.blue} stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="threatGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor={C.danger} stopOpacity={0.15} />
                      <stop offset="95%" stopColor={C.danger} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                  <XAxis dataKey="day" tick={{ fontSize: 12, fill: C.muted }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 12, fill: C.muted }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 12 }} />
                  <Area type="monotone" dataKey="scans"   stroke={C.blue}   strokeWidth={2} fill="url(#scanGrad)"   name="Total scans" />
                  <Area type="monotone" dataKey="threats" stroke={C.danger}  strokeWidth={2} fill="url(#threatGrad)" name="Threats" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChart label="No scan data yet — run some detections to populate this chart" />
            )}
          </div>

          {/* Pie chart */}
          <div style={card}>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.heading, marginBottom: "1.25rem" }}>
              Verdict Distribution
            </div>
            {distributionData.length > 0 && analytics && analytics.total_scans > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={distributionData} cx="50%" cy="45%" innerRadius={55} outerRadius={80} paddingAngle={3} dataKey="value" />
                  <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12, color: C.body }} />
                  <Tooltip contentStyle={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChart label="No detections yet" />
            )}
          </div>
        </div>

        {/* ── Recent detections ── */}
        <div style={card}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.heading, marginBottom: "1.25rem" }}>
            Recent Authentication Attempts
          </div>
          {recentData.length > 0 ? (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 460 }}>
                <thead>
                  <tr style={{ background: "#f8faff" }}>
                    {["Scan ID", "Time", "Verdict", "Confidence", "Method"].map((h) => (
                      <th key={h} style={{ textAlign: "left", fontSize: 10, fontWeight: 700, color: C.muted, textTransform: "uppercase", letterSpacing: 1, padding: "10px 12px", borderBottom: `2px solid ${C.gold}` }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {recentData.map((scan, i) => (
                    <tr key={scan.id} style={{ borderBottom: i < recentData.length - 1 ? `1px solid ${C.border}` : "none" }}>
                      <td style={{ padding: "12px 12px", fontSize: 12, color: C.heading, fontFamily: "monospace", fontWeight: 600 }}>{scan.id}</td>
                      <td style={{ padding: "12px 12px", fontSize: 12, color: C.muted }}>{timeAgo(scan.created_at)}</td>
                      <td style={{ padding: "12px 12px" }}>
                        <span style={{ fontSize: 10, fontWeight: 700, padding: "2px 10px", borderRadius: 4, ...verdictStyle(scan.verdict) }}>
                          {scan.verdict}
                        </span>
                      </td>
                      <td style={{ padding: "12px 12px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <div style={{ height: 4, width: 80, background: "#f3f4f6", borderRadius: 2, overflow: "hidden" }}>
                            <div style={{ height: "100%", width: `${scan.confidence}%`, background: scan.confidence > 80 ? C.success : C.amber, borderRadius: 2 }} />
                          </div>
                          <span style={{ fontSize: 12, color: C.body }}>{scan.confidence}%</span>
                        </div>
                      </td>
                      <td style={{ padding: "12px 12px", fontSize: 12, color: C.body }}>{scan.method}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{ padding: "2rem 0", textAlign: "center", color: C.muted, fontSize: 13 }}>
              No authentication attempts recorded yet — use the demo portal to run your first scan.
            </div>
          )}
        </div>

      </div>
      <Footer />
    </div>
  );
}
