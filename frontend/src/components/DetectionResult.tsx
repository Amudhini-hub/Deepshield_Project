"use client";

import { ShieldCheck, ShieldX, AlertTriangle, Clock, Cpu, Eye, Activity } from "lucide-react";
import type { DetectionResult } from "@/types/detection";
import { fakePct, riskDecision } from "@/types/detection";

// ── Design tokens ─────────────────────────────────────────────────────
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
  successBg: "#dcfce7",
  danger: "#dc2626",
  dangerBg: "#fee2e2",
  amber: "#d97706",
  amberBg: "#fef3c7",
};

// ── Helpers ───────────────────────────────────────────────────────────
function confColor(pct: number): string {
  if (pct < 30) return C.success;
  if (pct < 70) return C.amber;
  return C.danger;
}

function MiniBar({ value, color }: { value: number; color: string }) {
  return (
    <div style={{ flex: 1, height: 4, background: "#f3f4f6", borderRadius: 2, overflow: "hidden" }}>
      <div
        style={{
          height: "100%",
          width: `${Math.min(100, value * 100).toFixed(1)}%`,
          background: color,
          borderRadius: 2,
          transition: "width 0.6s ease",
        }}
      />
    </div>
  );
}

function Row({
  label,
  value,
  color,
  bar,
}: {
  label: string;
  value: string;
  color?: string;
  bar?: number;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 12, color: C.muted }}>{label}</span>
        <span style={{ fontSize: 13, fontWeight: 600, color: color ?? C.heading }}>{value}</span>
      </div>
      {bar !== undefined && (
        <MiniBar value={bar} color={color ?? C.primary} />
      )}
    </div>
  );
}

// ── Placeholder ───────────────────────────────────────────────────────
function EmptyState() {
  return (
    <div
      style={{
        background: C.card,
        border: `0.5px solid ${C.border}`,
        borderRadius: 14,
        padding: "3rem 2rem",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        minHeight: 320,
        gap: "1rem",
      }}
    >
      <div
        style={{
          width: 56,
          height: 56,
          background: C.primaryLight,
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <ShieldCheck size={26} color={C.primary} />
      </div>
      <div>
        <div style={{ fontSize: 16, fontWeight: 600, color: C.heading, marginBottom: 6 }}>
          No analysis yet
        </div>
        <div style={{ fontSize: 13, color: C.body, lineHeight: 1.6, maxWidth: 240 }}>
          Allow camera access, position your face, then click{" "}
          <strong>Capture &amp; Analyse</strong>.
        </div>
      </div>
      {/* Animated skeleton rows */}
      <div style={{ width: "100%", maxWidth: 260, display: "flex", flexDirection: "column", gap: 8 }}>
        {[80, 60, 70].map((w, i) => (
          <div
            key={i}
            style={{
              height: 10,
              background: "#f3f4f6",
              borderRadius: 5,
              width: `${w}%`,
              margin: "0 auto",
              animation: "shimmer 1.6s ease-in-out infinite",
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </div>
      <style>{`
        @keyframes shimmer {
          0%,100% { opacity: 0.5 }
          50%      { opacity: 1   }
        }
      `}</style>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────
export default function DetectionResultCard({ result }: { result: DetectionResult | null }) {
  if (!result) return <EmptyState />;

  const { deepfake: df, liveness: lv, capturedAt } = result;
  const fp = fakePct(df);                      // 0–100 fake probability
  const decision = riskDecision(result);

  const decisionMeta = {
    ALLOW: {
      Icon: ShieldCheck,
      label: "ALLOW — Verified real",
      color: C.success,
      bg: C.successBg,
      border: "#86efac",
    },
    CHALLENGE: {
      Icon: AlertTriangle,
      label: "CHALLENGE — Suspicious",
      color: C.amber,
      bg: C.amberBg,
      border: "#fcd34d",
    },
    BLOCK: {
      Icon: ShieldX,
      label: "BLOCK — Deepfake detected",
      color: C.danger,
      bg: C.dangerBg,
      border: "#fca5a5",
    },
  }[decision];

  const { Icon } = decisionMeta;

  // Per-check breakdown from liveness details (if backend includes them)
  const livenessChecks = Object.entries(lv.details ?? {}).filter(
    ([, v]) => typeof v === "number"
  ) as [string, number][];

  // Per-check breakdown from deepfake details
  const dfChecks = Object.entries(df.details ?? {}).filter(
    ([, v]) => typeof v === "number"
  ) as [string, number][];

  const ts = new Date(capturedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.875rem" }}>

      {/* ── Decision banner ── */}
      <div
        style={{
          background: decisionMeta.bg,
          border: `1.5px solid ${decisionMeta.border}`,
          borderRadius: 14,
          padding: "1.25rem 1.5rem",
          display: "flex",
          alignItems: "center",
          gap: "1rem",
        }}
      >
        <Icon size={32} color={decisionMeta.color} style={{ flexShrink: 0 }} />
        <div>
          <div style={{ fontSize: 18, fontWeight: 700, color: decisionMeta.color }}>
            {decisionMeta.label}
          </div>
          <div style={{ fontSize: 12, color: C.body, marginTop: 3 }}>
            {df.frame_count} frames analysed · {df.detection_method}
          </div>
        </div>
      </div>

      {/* ── Deepfake card ── */}
      <div
        style={{
          background: C.card,
          border: `0.5px solid ${C.border}`,
          borderRadius: 14,
          padding: "1.25rem 1.5rem",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 7,
            marginBottom: "1rem",
          }}
        >
          <Cpu size={14} color={C.primary} />
          <span style={{ fontSize: 12, fontWeight: 600, color: C.muted, letterSpacing: 1, textTransform: "uppercase" }}>
            Deepfake Detection
          </span>
        </div>

        {/* Big fake-probability number */}
        <div style={{ display: "flex", alignItems: "flex-end", gap: 12, marginBottom: "1rem" }}>
          <div
            style={{
              fontSize: 48,
              fontWeight: 800,
              lineHeight: 1,
              color: confColor(fp),
              letterSpacing: -1,
            }}
          >
            {fp.toFixed(1)}
            <span style={{ fontSize: 22, fontWeight: 600 }}>%</span>
          </div>
          <div style={{ paddingBottom: 6 }}>
            <div
              style={{
                display: "inline-block",
                background: df.is_deepfake ? C.dangerBg : C.successBg,
                color: df.is_deepfake ? C.danger : C.success,
                fontSize: 11,
                fontWeight: 700,
                padding: "2px 10px",
                borderRadius: 20,
                letterSpacing: 0.5,
              }}
            >
              {df.is_deepfake ? "FAKE" : "REAL"}
            </div>
            <div style={{ fontSize: 11, color: C.muted, marginTop: 3 }}>fake probability</div>
          </div>
        </div>

        {/* Fake-probability bar */}
        <div style={{ height: 6, background: "#f3f4f6", borderRadius: 3, overflow: "hidden", marginBottom: "1rem" }}>
          <div
            style={{
              height: "100%",
              width: `${fp.toFixed(1)}%`,
              background: confColor(fp),
              borderRadius: 3,
              transition: "width 0.7s ease",
            }}
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <Row label="Model confidence" value={`${(df.confidence * 100).toFixed(1)}%`} bar={df.confidence} color={C.primary} />
        </div>

        {/* Anomalies */}
        {df.anomalies.length > 0 && (
          <div style={{ marginTop: "0.875rem" }}>
            <div style={{ fontSize: 11, color: C.muted, fontWeight: 600, letterSpacing: 0.5, marginBottom: 5 }}>
              ANOMALIES DETECTED
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
              {df.anomalies.map((a) => (
                <span
                  key={a}
                  style={{
                    fontSize: 11,
                    background: C.dangerBg,
                    color: C.danger,
                    padding: "2px 8px",
                    borderRadius: 20,
                  }}
                >
                  {a}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Per-check breakdown if backend provides them */}
        {dfChecks.length > 0 && (
          <div style={{ marginTop: "0.875rem", display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ fontSize: 11, color: C.muted, fontWeight: 600, letterSpacing: 0.5 }}>
              SIGNAL BREAKDOWN
            </div>
            {dfChecks.map(([key, val]) => (
              <Row
                key={key}
                label={key.replace(/_/g, " ")}
                value={`${(val * 100).toFixed(0)}%`}
                bar={val}
                color={confColor(val * 100)}
              />
            ))}
          </div>
        )}
      </div>

      {/* ── Liveness card ── */}
      <div
        style={{
          background: C.card,
          border: `0.5px solid ${C.border}`,
          borderRadius: 14,
          padding: "1.25rem 1.5rem",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 7,
            marginBottom: "1rem",
          }}
        >
          <Eye size={14} color={C.primary} />
          <span style={{ fontSize: 12, fontWeight: 600, color: C.muted, letterSpacing: 1, textTransform: "uppercase" }}>
            Liveness Verification
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
          <div
            style={{
              background: lv.is_alive ? C.successBg : C.dangerBg,
              color: lv.is_alive ? C.success : C.danger,
              fontWeight: 700,
              fontSize: 14,
              padding: "0.375rem 1rem",
              borderRadius: 8,
              letterSpacing: 0.5,
            }}
          >
            {lv.is_alive ? "LIVE ✓" : "SPOOF ✗"}
          </div>
          <div>
            <div style={{ fontSize: 22, fontWeight: 700, color: lv.is_alive ? C.success : C.danger }}>
              {(lv.confidence * 100).toFixed(1)}%
            </div>
            <div style={{ fontSize: 11, color: C.muted }}>confidence</div>
          </div>
        </div>

        <div style={{ height: 6, background: "#f3f4f6", borderRadius: 3, overflow: "hidden", marginBottom: "1rem" }}>
          <div
            style={{
              height: "100%",
              width: `${(lv.confidence * 100).toFixed(1)}%`,
              background: lv.is_alive ? C.success : C.danger,
              borderRadius: 3,
              transition: "width 0.7s ease",
            }}
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <Row label="Challenge type" value={lv.challenge_type || "—"} />
          <Row label="Frames analysed" value={String(lv.frame_count)} />
        </div>

        {/* Per-check breakdown */}
        {livenessChecks.length > 0 && (
          <div style={{ marginTop: "0.875rem", display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ fontSize: 11, color: C.muted, fontWeight: 600, letterSpacing: 0.5 }}>
              CHECK BREAKDOWN
            </div>
            {livenessChecks.map(([key, val]) => (
              <Row
                key={key}
                label={key.replace(/_/g, " ")}
                value={`${(val * 100).toFixed(0)}%`}
                bar={val}
                color={val > 0.5 ? C.success : C.danger}
              />
            ))}
          </div>
        )}
      </div>

      {/* ── Timestamp ── */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          fontSize: 11,
          color: C.muted,
          justifyContent: "flex-end",
        }}
      >
        <Activity size={11} />
        <span>Last analysis:</span>
        <Clock size={11} />
        <span>{ts}</span>
      </div>
    </div>
  );
}
