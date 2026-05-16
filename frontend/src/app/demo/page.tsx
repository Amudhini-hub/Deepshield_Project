"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import WebcamCapture from "@/components/WebcamCapture";
import DetectionResultCard from "@/components/DetectionResult";
import { login, register } from "@/lib/api";
import { isAuthenticated, setToken } from "@/lib/auth";
import type { DetectionResult } from "@/types/detection";

const C = {
  primary: "#4f46e5",
  primaryDark: "#4338ca",
  primaryLight: "#eef2ff",
  borderAccent: "#c7d2fe",
  heading: "#1e1b4b",
  body: "#6b7280",
  muted: "#9ca3af",
  pageBg: "#f8faff",
  card: "#ffffff",
  border: "#e0e7ff",
  danger: "#dc2626",
};

// ── Quick demo: auto-register an ephemeral account ─────────────────────
function QuickDemoBanner({ onReady }: { onReady: () => void }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleQuickDemo() {
    setLoading(true);
    setError("");
    const uid = Date.now();
    const demoEmail = `demo.${uid}@deepshield.demo`;
    const demoPass = `Demo${uid}!`;
    try {
      await register(demoEmail, demoPass);
      const res = await login(demoEmail, demoPass);
      setToken(res.access_token);
      onReady();
    } catch {
      setError("Quick demo setup failed. Please sign in with an existing account.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        background: C.primary,
        borderRadius: 12,
        padding: "1.25rem 1.5rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "1rem",
        flexWrap: "wrap",
        marginBottom: "1rem",
      }}
    >
      <div>
        <div style={{ fontSize: 15, fontWeight: 700, color: "#fff", marginBottom: 3 }}>
          🚀 Try instantly — no sign-up needed
        </div>
        <div style={{ fontSize: 13, color: C.borderAccent }}>
          We&apos;ll create a temporary demo account for you automatically.
        </div>
        {error && (
          <div style={{ fontSize: 12, color: "#fca5a5", marginTop: 6 }}>{error}</div>
        )}
      </div>
      <button
        onClick={handleQuickDemo}
        disabled={loading}
        style={{
          background: "#fff",
          color: C.primary,
          border: "none",
          padding: "0.625rem 1.25rem",
          borderRadius: 8,
          fontSize: 14,
          fontWeight: 700,
          cursor: loading ? "not-allowed" : "pointer",
          opacity: loading ? 0.7 : 1,
          display: "flex",
          alignItems: "center",
          gap: 6,
          whiteSpace: "nowrap",
          flexShrink: 0,
        }}
      >
        {loading && <Loader2 size={13} className="animate-spin" />}
        {loading ? "Setting up…" : "Quick demo →"}
      </button>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────
export default function DemoPage() {
  const router = useRouter();
  const [authed, setAuthed] = useState(false);
  const [checking, setChecking] = useState(true);
  const [result, setResult] = useState<DetectionResult | null>(null);

  useEffect(() => {
    setAuthed(isAuthenticated());
    setChecking(false);
  }, []);

  if (checking) {
    return (
      <div style={{ background: C.pageBg, minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <Nav />
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Loader2 size={32} color={C.primary} className="animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div style={{ background: C.pageBg, minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Nav />

      <div
        className="px-4 md:px-12 py-8 md:py-12"
        style={{ maxWidth: 980, margin: "0 auto", width: "100%", flex: 1 }}
      >
        {/* ── Header ── */}
        <div style={{ marginBottom: "2rem" }}>
          <div
            style={{
              fontSize: 12,
              color: C.primary,
              fontWeight: 600,
              letterSpacing: 1,
              textTransform: "uppercase",
              marginBottom: 8,
            }}
          >
            Live detection
          </div>
          <h1 style={{ fontSize: 32, fontWeight: 700, color: C.heading, marginBottom: 8 }}>
            DeepShield Live Demo
          </h1>
          <p style={{ fontSize: 15, color: C.body }}>
            Allow camera access, face the lens, and click <strong>Capture &amp; Analyse</strong> — DeepShield runs the full detection pipeline in under a second.
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
              <span style={{ fontSize: 12, color: C.muted }}>or</span>
              <div style={{ flex: 1, height: "0.5px", background: C.border }} />
            </div>

            <div style={{ display: "flex", gap: "0.625rem" }}>
              <button
                onClick={() => router.push("/login")}
                style={{
                  flex: 1,
                  background: C.card,
                  border: `1px solid ${C.border}`,
                  borderRadius: 8,
                  padding: "0.625rem",
                  fontSize: 13,
                  fontWeight: 500,
                  color: C.heading,
                  cursor: "pointer",
                }}
              >
                Sign in
              </button>
              <button
                onClick={() => router.push("/register")}
                style={{
                  flex: 1,
                  background: C.primary,
                  border: "none",
                  borderRadius: 8,
                  padding: "0.625rem",
                  fontSize: 13,
                  fontWeight: 600,
                  color: "#fff",
                  cursor: "pointer",
                }}
              >
                Create account →
              </button>
            </div>
          </div>
        )}

        {/* ── Two-column detection layout ── */}
        {authed && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
            {/* Left: camera capture */}
            <div>
              <div
                style={{
                  fontSize: 11,
                  color: C.muted,
                  fontWeight: 600,
                  letterSpacing: 1,
                  textTransform: "uppercase",
                  marginBottom: "0.75rem",
                }}
              >
                Camera capture
              </div>
              <WebcamCapture onResult={setResult} />
              <div
                style={{
                  marginTop: "0.875rem",
                  background: C.primaryLight,
                  border: `1px solid ${C.borderAccent}`,
                  borderRadius: 8,
                  padding: "0.625rem 0.875rem",
                  fontSize: 12,
                  color: "#4338ca",
                }}
              >
                🔒 Video is processed directly by your DeepShield instance. No footage is retained.
              </div>
            </div>

            {/* Right: results */}
            <div>
              <div
                style={{
                  fontSize: 11,
                  color: C.muted,
                  fontWeight: 600,
                  letterSpacing: 1,
                  textTransform: "uppercase",
                  marginBottom: "0.75rem",
                }}
              >
                Analysis results
              </div>
              <DetectionResultCard result={result} />
            </div>
          </div>
        )}

        {/* ── Info strip (always visible) ── */}
        <div
          className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-10"
          style={{
            background: C.card,
            border: `0.5px solid ${C.border}`,
            borderRadius: 14,
            overflow: "hidden",
          }}
        >
          {[
            { num: "< 800ms", label: "End-to-end detection time" },
            { num: "99.2%",   label: "Deepfake detection accuracy" },
            { num: "5 min",   label: "Average integration time" },
          ].map((s) => (
            <div
              key={s.label}
              style={{
                padding: "1.25rem",
                textAlign: "center",
                borderRight: `0.5px solid ${C.border}`,
              }}
            >
              <div style={{ fontSize: 22, fontWeight: 700, color: C.primary }}>{s.num}</div>
              <div style={{ fontSize: 12, color: C.muted, marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      <Footer />
    </div>
  );
}
