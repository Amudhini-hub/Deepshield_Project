"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2, ShieldCheck, CheckCircle2, Clock, Cpu, Shield } from "lucide-react";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import WebcamCapture from "@/components/WebcamCapture";
import DetectionResultCard from "@/components/DetectionResult";
import { api } from "@/lib/api";
import { isAuthenticated, setToken } from "@/lib/auth";
import type { DetectionResult } from "@/types/detection";

const C = {
  blue: "#003580",
  blueLight: "#004aad",
  blueDark: "#002460",
  gold: "#C8922A",
  goldLight: "#FDF3E1",
  bg: "#f0f4f8",
  card: "#ffffff",
  heading: "#1a2332",
  body: "#4a5568",
  muted: "#718096",
  border: "#d1dce8",
  danger: "#dc2626",
  success: "#16a34a",
};

// ── Quick demo: one-call demo token, no registration needed ───────────
function QuickDemoBanner({ onReady }: { onReady: () => void }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleQuickDemo() {
    setLoading(true);
    setError("");
    try {
      const r = await api.post<{ access_token: string }>("/users/demo-token");
      setToken(r.data.access_token);
      onReady();
    } catch {
      setError("Demo setup failed. Ensure the backend is running on port 8000.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        background: C.blue,
        borderRadius: 10,
        padding: "1.25rem 1.5rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "1rem",
        flexWrap: "wrap",
        marginBottom: "1rem",
        borderLeft: `4px solid ${C.gold}`,
      }}
    >
      <div>
        <div style={{ fontSize: 14, fontWeight: 700, color: "#fff", marginBottom: 3 }}>
          Instant access — no sign-up required
        </div>
        <div style={{ fontSize: 12, color: "rgba(255,255,255,0.68)" }}>
          We&apos;ll create a temporary demo session for you automatically.
        </div>
        {error && (
          <div style={{ fontSize: 12, color: "#fca5a5", marginTop: 6 }}>{error}</div>
        )}
      </div>
      <button
        onClick={handleQuickDemo}
        disabled={loading}
        style={{
          background: C.gold,
          color: "#fff",
          border: "none",
          padding: "0.625rem 1.25rem",
          borderRadius: 8,
          fontSize: 13,
          fontWeight: 700,
          cursor: loading ? "not-allowed" : "pointer",
          opacity: loading ? 0.75 : 1,
          display: "flex",
          alignItems: "center",
          gap: 6,
          whiteSpace: "nowrap",
          flexShrink: 0,
        }}
      >
        {loading && <Loader2 size={13} className="animate-spin" />}
        {loading ? "Setting up…" : "Start Demo →"}
      </button>
    </div>
  );
}

// ── Authentication progress steps ─────────────────────────────────────
function AuthProgressBar({ hasResult }: { hasResult: boolean }) {
  const steps = [
    { id: 1, label: "Face Scan", icon: Cpu },
    { id: 2, label: "Liveness", icon: Eye2 },
    { id: 3, label: "Analysis", icon: ShieldCheck },
    { id: 4, label: "Decision", icon: CheckCircle2 },
  ];
  const active = hasResult ? 4 : 1;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 0,
        background: C.card,
        border: `1px solid ${C.border}`,
        borderRadius: 10,
        padding: "0.875rem 1.25rem",
        marginBottom: "1.5rem",
        overflow: "hidden",
      }}
    >
      {steps.map((step, i) => {
        const done = step.id < active;
        const curr = step.id === active;
        const Icon = step.icon;
        return (
          <div key={step.id} style={{ display: "flex", alignItems: "center", flex: 1 }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4, minWidth: 0 }}>
              <div
                style={{
                  width: 30,
                  height: 30,
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: done ? C.success : curr ? C.gold : C.border,
                  color: done || curr ? "#fff" : C.muted,
                  flexShrink: 0,
                  transition: "background 0.3s",
                }}
              >
                {done ? <CheckCircle2 size={14} /> : <Icon size={13} />}
              </div>
              <div style={{ fontSize: 10, fontWeight: 600, color: done ? C.success : curr ? C.gold : C.muted, whiteSpace: "nowrap" }}>
                {step.label}
              </div>
            </div>
            {i < steps.length - 1 && (
              <div
                style={{
                  flex: 1,
                  height: 2,
                  background: done ? C.success : C.border,
                  margin: "0 6px",
                  marginBottom: 18,
                  transition: "background 0.3s",
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

// Eye icon inline (avoids import collision)
function Eye2({ size }: { size: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

// ── Page ──────────────────────────────────────────────────────────────
export default function DemoPage() {
  const router = useRouter();
  const [authed, setAuthed] = useState(false);
  const [result, setResult] = useState<DetectionResult | null>(null);

  useEffect(() => {
    setAuthed(isAuthenticated());
  }, []);

  return (
    <div style={{ background: C.bg, minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Nav />

      {/* IOB portal header strip */}
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
          Indian Overseas Bank &nbsp;·&nbsp; Identity Verification Portal
        </span>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 5, fontSize: 11, color: C.muted }}>
          <Clock size={11} />
          Secure session
        </div>
      </div>

      <div
        className="px-4 md:px-12 py-8 md:py-10"
        style={{ maxWidth: 980, margin: "0 auto", width: "100%", flex: 1 }}
      >
        {/* ── Header ── */}
        <div style={{ marginBottom: "1.5rem" }}>
          <div
            style={{
              fontSize: 11,
              color: C.gold,
              fontWeight: 700,
              letterSpacing: 1.2,
              textTransform: "uppercase",
              marginBottom: 8,
            }}
          >
            Customer Authentication
          </div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: C.heading, marginBottom: 8 }}>
            Identity Verification
          </h1>
          <p style={{ fontSize: 14, color: C.body }}>
            Allow camera access, face the lens, and click <strong>Capture &amp; Analyse</strong> — DeepShield completes the full biometric verification in seconds.
          </p>
        </div>

        {/* ── Auth gate ── */}
        {!authed && (
          <div style={{ maxWidth: 480, marginBottom: "2rem" }}>
            <QuickDemoBanner onReady={() => setAuthed(true)} />

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
                marginBottom: "0.875rem",
              }}
            >
              <div style={{ flex: 1, height: "0.5px", background: C.border }} />
              <span style={{ fontSize: 12, color: C.muted }}>or sign in with your account</span>
              <div style={{ flex: 1, height: "0.5px", background: C.border }} />
            </div>

            <div style={{ display: "flex", gap: "0.625rem" }}>
              <button
                onClick={() => router.push("/login")}
                style={{
                  flex: 1,
                  background: C.card,
                  border: `1.5px solid ${C.blue}`,
                  borderRadius: 8,
                  padding: "0.625rem",
                  fontSize: 13,
                  fontWeight: 600,
                  color: C.blue,
                  cursor: "pointer",
                }}
              >
                Customer Login
              </button>
              <button
                onClick={() => router.push("/register")}
                style={{
                  flex: 1,
                  background: C.gold,
                  border: "none",
                  borderRadius: 8,
                  padding: "0.625rem",
                  fontSize: 13,
                  fontWeight: 600,
                  color: "#fff",
                  cursor: "pointer",
                }}
              >
                Create Account →
              </button>
            </div>
          </div>
        )}

        {/* ── Two-column detection layout ── */}
        {authed && (
          <>
            <AuthProgressBar hasResult={!!result} />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
              {/* Left: camera capture */}
              <div>
                <div
                  style={{
                    fontSize: 10,
                    color: C.muted,
                    fontWeight: 700,
                    letterSpacing: 1.2,
                    textTransform: "uppercase",
                    marginBottom: "0.75rem",
                  }}
                >
                  Biometric Capture
                </div>
                <WebcamCapture onResult={setResult} />
                <div
                  style={{
                    marginTop: "0.875rem",
                    background: "#e8f0fe",
                    border: `1px solid #c0d0ea`,
                    borderRadius: 8,
                    padding: "0.625rem 0.875rem",
                    fontSize: 12,
                    color: C.blue,
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                  }}
                >
                  <ShieldCheck size={13} />
                  Video is processed by your DeepShield instance. No footage is stored or transmitted.
                </div>
              </div>

              {/* Right: results */}
              <div>
                <div
                  style={{
                    fontSize: 10,
                    color: C.muted,
                    fontWeight: 700,
                    letterSpacing: 1.2,
                    textTransform: "uppercase",
                    marginBottom: "0.75rem",
                  }}
                >
                  Verification Results
                </div>
                <DetectionResultCard result={result} />
                <p className="text-xs text-center mt-2" style={{ color: C.muted }}>
                  AI heatmap shows per-region manipulation confidence across the detected face area.
                </p>
              </div>
            </div>
          </>
        )}

        {/* ── Info strip ── */}
        <div
          className="grid grid-cols-1 md:grid-cols-3 mt-10"
          style={{
            background: C.blue,
            borderRadius: 12,
            overflow: "hidden",
            borderTop: `3px solid ${C.gold}`,
          }}
        >
          {[
            { num: "AI-Powered", label: "End-to-end verification" },
            { num: "AI Ensemble", label: "Deepfake detection method" },
            { num: "3-Layer", label: "Anti-spoofing defence" },
          ].map((s, i) => (
            <div
              key={s.label}
              style={{
                padding: "1.5rem",
                textAlign: "center",
                borderRight: i < 2 ? `1px solid rgba(255,255,255,0.12)` : "none",
              }}
            >
              <div style={{ fontSize: 24, fontWeight: 700, color: C.gold }}>{s.num}</div>
              <div style={{ fontSize: 12, color: "rgba(255,255,255,0.65)", marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      <Footer />
    </div>
  );
}
