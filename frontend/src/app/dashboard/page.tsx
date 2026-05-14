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
  Cell,
  Legend,
} from "recharts";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import { api } from "@/lib/api";
import { ShieldCheck, Zap, Target, Clock } from "lucide-react";

interface DetailedHealth {
  timestamp: string;
  service: string;
  version: string;
  components: {
    api: { status: string };
    database: { status: string };
    redis: { connected?: boolean; status?: string };
    ml_services: string;
  };
  environment: string;
}

const C = {
  primary: "#4f46e5",
  primaryLight: "#eef2ff",
  borderAccent: "#c7d2fe",
  heading: "#1e1b4b",
  body: "#6b7280",
  muted: "#9ca3af",
  pageBg: "#f8faff",
  card: "#ffffff",
  border: "#e0e7ff",
  success: "#16a34a",
  danger: "#dc2626",
  amber: "#d97706",
};

const weekData = [
  { day: "Mon", scans: 145, threats: 12 },
  { day: "Tue", scans: 189, threats: 23 },
  { day: "Wed", scans: 234, threats: 8 },
  { day: "Thu", scans: 178, threats: 34 },
  { day: "Fri", scans: 312, threats: 19 },
  { day: "Sat", scans: 98, threats: 6 },
  { day: "Sun", scans: 156, threats: 15 },
];

const distributionData = [
  { name: "Real", value: 1195 },
  { name: "Deepfake", value: 117 },
  { name: "Suspicious", value: 43 },
];
const DIST_COLORS = [C.success, C.danger, C.amber];

const recentScans = [
  { id: "DS-0291", time: "2 min ago", verdict: "REAL", confidence: 98.4, method: "Ensemble" },
  { id: "DS-0290", time: "7 min ago", verdict: "BLOCK", confidence: 91.2, method: "FFT artifact" },
  { id: "DS-0289", time: "14 min ago", verdict: "REAL", confidence: 97.8, method: "Ensemble" },
  { id: "DS-0288", time: "21 min ago", verdict: "CHALLENGE", confidence: 62.1, method: "Frequency" },
  { id: "DS-0287", time: "31 min ago", verdict: "REAL", confidence: 99.1, method: "Ensemble" },
];

const verdictStyle = (v: string): React.CSSProperties => {
  if (v === "REAL") return { background: "#dcfce7", color: "#15803d" };
  if (v === "BLOCK") return { background: "#fee2e2", color: C.danger };
  return { background: "#fef3c7", color: "#92400e" };
};

export default function DashboardPage() {
  const [health, setHealth] = useState<DetailedHealth | null>(null);
  const [healthError, setHealthError] = useState(false);

  useEffect(() => {
    api
      .get<DetailedHealth>("/health/status")
      .then((r) => setHealth(r.data))
      .catch(() => setHealthError(true));
  }, []);

  const mlStatus = health?.components.ml_services ?? (healthError ? "unavailable" : "checking…");
  const apiVersion = health?.version ?? "-";
  const dbStatus = health?.components.database.status ?? "unknown";
  const redisOk = health?.components.redis?.connected ?? (health?.components.redis?.status === "connected");
  const environment = health?.environment ?? "-";

  const card: React.CSSProperties = {
    background: C.card,
    border: `0.5px solid ${C.border}`,
    borderRadius: 12,
    padding: "1.5rem",
  };

  return (
    <div style={{ background: C.pageBg, color: C.heading, minHeight: "100vh" }}>
      <Nav />

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "3rem" }}>
        {/* Header */}
        <div style={{ marginBottom: "2rem" }}>
          <div style={{ fontSize: 12, color: C.primary, fontWeight: 600, letterSpacing: 1, textTransform: "uppercase", marginBottom: 8 }}>
            Analytics
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "1rem" }}>
            <h1 style={{ fontSize: 30, fontWeight: 700, color: C.heading }}>
              Detection Dashboard
            </h1>
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
              {[
                {
                  label: `API v${apiVersion}`,
                  ok: !healthError,
                  dot: !healthError,
                },
                {
                  label: `DB ${dbStatus}`,
                  ok: dbStatus === "healthy",
                  dot: true,
                },
                {
                  label: `Redis ${redisOk ? "connected" : "offline"}`,
                  ok: redisOk,
                  dot: true,
                },
                {
                  label: `ML ${mlStatus}`,
                  ok: mlStatus === "available",
                  dot: true,
                },
                {
                  label: environment,
                  ok: true,
                  dot: false,
                },
              ].map(({ label, ok, dot }) => (
                <div
                  key={label}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 5,
                    fontSize: 12,
                    color: C.body,
                    background: C.card,
                    border: `0.5px solid ${C.border}`,
                    borderRadius: 8,
                    padding: "5px 10px",
                  }}
                >
                  {dot && (
                    <span
                      style={{
                        width: 7,
                        height: 7,
                        borderRadius: "50%",
                        background: ok ? C.success : C.danger,
                        display: "inline-block",
                        flexShrink: 0,
                      }}
                    />
                  )}
                  {label}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Stat cards */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: "1rem",
            marginBottom: "1.5rem",
          }}
        >
          {[
            { Icon: ShieldCheck, label: "Total scans (7 days)", value: "1,312", sub: "+18% vs last week", color: C.primary, bg: C.primaryLight },
            { Icon: Zap, label: "Threats blocked", value: "117", sub: "8.9% threat rate", color: C.danger, bg: "#fee2e2" },
            { Icon: Target, label: "Detection accuracy", value: "99.2%", sub: "Ensemble model", color: C.success, bg: "#dcfce7" },
            { Icon: Clock, label: "Avg response time", value: "743ms", sub: "p95: 1.1s", color: C.amber, bg: "#fef3c7" },
          ].map(({ Icon, label, value, sub, color, bg }) => (
            <div key={label} style={card}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
                <div style={{ fontSize: 13, color: C.body }}>{label}</div>
                <div style={{ width: 36, height: 36, borderRadius: 8, background: bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <Icon size={18} color={color} />
                </div>
              </div>
              <div style={{ fontSize: 28, fontWeight: 700, color: C.heading }}>{value}</div>
              <div style={{ fontSize: 12, color: C.muted, marginTop: 4 }}>{sub}</div>
            </div>
          ))}
        </div>

        {/* Charts row */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "2fr 1fr",
            gap: "1rem",
            marginBottom: "1.5rem",
          }}
        >
          {/* Area chart */}
          <div style={card}>
            <div style={{ fontSize: 14, fontWeight: 600, color: C.heading, marginBottom: "1.25rem" }}>
              Scans & threats — last 7 days
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={weekData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={C.primary} stopOpacity={0.15} />
                    <stop offset="95%" stopColor={C.primary} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="threatGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={C.danger} stopOpacity={0.15} />
                    <stop offset="95%" stopColor={C.danger} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                <XAxis dataKey="day" tick={{ fontSize: 12, fill: C.muted }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: C.muted }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    background: C.card,
                    border: `0.5px solid ${C.border}`,
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Area type="monotone" dataKey="scans" stroke={C.primary} strokeWidth={2} fill="url(#scanGrad)" name="Total scans" />
                <Area type="monotone" dataKey="threats" stroke={C.danger} strokeWidth={2} fill="url(#threatGrad)" name="Threats" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Pie chart */}
          <div style={card}>
            <div style={{ fontSize: 14, fontWeight: 600, color: C.heading, marginBottom: "1.25rem" }}>
              Result distribution
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={distributionData}
                  cx="50%"
                  cy="45%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {distributionData.map((_, i) => (
                    <Cell key={i} fill={DIST_COLORS[i]} />
                  ))}
                </Pie>
                <Legend
                  iconType="circle"
                  iconSize={8}
                  wrapperStyle={{ fontSize: 12, color: C.body }}
                />
                <Tooltip
                  contentStyle={{
                    background: C.card,
                    border: `0.5px solid ${C.border}`,
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent scans table */}
        <div style={card}>
          <div style={{ fontSize: 14, fontWeight: 600, color: C.heading, marginBottom: "1.25rem" }}>
            Recent detections
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {["Scan ID", "Time", "Verdict", "Confidence", "Method"].map((h) => (
                  <th
                    key={h}
                    style={{
                      textAlign: "left",
                      fontSize: 11,
                      fontWeight: 600,
                      color: C.muted,
                      textTransform: "uppercase",
                      letterSpacing: 1,
                      paddingBottom: 10,
                      borderBottom: `0.5px solid ${C.border}`,
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {recentScans.map((scan, i) => (
                <tr key={scan.id} style={{ borderBottom: i < recentScans.length - 1 ? `0.5px solid ${C.border}` : "none" }}>
                  <td style={{ padding: "12px 0", fontSize: 13, color: C.heading, fontFamily: "monospace", fontWeight: 600 }}>
                    {scan.id}
                  </td>
                  <td style={{ padding: "12px 0", fontSize: 13, color: C.muted }}>{scan.time}</td>
                  <td style={{ padding: "12px 0" }}>
                    <span
                      style={{
                        fontSize: 11,
                        fontWeight: 600,
                        padding: "2px 10px",
                        borderRadius: 4,
                        ...verdictStyle(scan.verdict),
                      }}
                    >
                      {scan.verdict}
                    </span>
                  </td>
                  <td style={{ padding: "12px 0" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <div style={{ height: 4, width: 80, background: "#f3f4f6", borderRadius: 2, overflow: "hidden" }}>
                        <div
                          style={{
                            height: "100%",
                            width: `${scan.confidence}%`,
                            background: scan.confidence > 80 ? C.success : C.amber,
                            borderRadius: 2,
                          }}
                        />
                      </div>
                      <span style={{ fontSize: 12, color: C.body }}>{scan.confidence}%</span>
                    </div>
                  </td>
                  <td style={{ padding: "12px 0", fontSize: 13, color: C.body }}>{scan.method}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Footer />
    </div>
  );
}
