"use client";

import { useRef, useState, useCallback } from "react";
import Webcam from "react-webcam";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import { login, register, detectDeepfake, detectLiveness } from "@/lib/api";
import type { DeepfakeResult, LivenessResult } from "@/lib/api";
import { ShieldCheck, AlertTriangle, XCircle, Loader2 } from "lucide-react";

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
  success: "#16a34a",
  danger: "#dc2626",
  amber: "#d97706",
};

type Phase = "auth" | "ready" | "recording" | "analyzing" | "results" | "error" | "ml_unavailable";

interface Results {
  deepfake: DeepfakeResult | null;
  liveness: LivenessResult | null;
}

export default function DemoPage() {
  // Auth state
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState<string | null>(null);
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);

  // Demo state
  const [phase, setPhase] = useState<Phase>("auth");
  const [countdown, setCountdown] = useState(5);
  const [results, setResults] = useState<Results>({ deepfake: null, liveness: null });
  const [error, setError] = useState("");

  const webcamRef = useRef<Webcam>(null);
  const chunksRef = useRef<Blob[]>([]);

  // ── Auth ──────────────────────────────────────────────────────────────

  async function handleQuickDemo() {
    setAuthLoading(true);
    setAuthError("");
    const uid = Date.now();
    const demoEmail = `demo.${uid}@deepshield.demo`;
    const demoPass = `Demo${uid}!`;
    try {
      await register(demoEmail, demoPass);
      const res = await login(demoEmail, demoPass);
      setToken(res.access_token);
      setPhase("ready");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Quick demo setup failed. Please register manually below.";
      setAuthError(msg);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleAuth(e: React.SyntheticEvent) {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError("");
    try {
      if (isRegister) {
        await register(email, password);
      }
      const res = await login(email, password);
      setToken(res.access_token);
      setPhase("ready");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Authentication failed. Check your credentials.";
      setAuthError(msg);
    } finally {
      setAuthLoading(false);
    }
  }

  // ── Recording ─────────────────────────────────────────────────────────

  const startAnalysis = useCallback(() => {
    const video = webcamRef.current?.video;
    if (!video || !video.srcObject) return;

    const stream = video.srcObject as MediaStream;
    chunksRef.current = [];

    let mimeType = "video/webm;codecs=vp8";
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = "video/webm";
    }

    const recorder = new MediaRecorder(stream, { mimeType });

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: "video/webm" });
      setPhase("analyzing");
      try {
        const [deepfake, liveness] = await Promise.all([
          detectDeepfake(blob, token!),
          detectLiveness(blob, token!),
        ]);
        setResults({ deepfake, liveness });
        setPhase("results");
      } catch (err: unknown) {
        const status = (err as { response?: { status?: number } })?.response?.status;
        if (status === 503) {
          setPhase("ml_unavailable");
        } else {
          const msg =
            (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
            "Analysis failed. Please try again.";
          setError(msg);
          setPhase("error");
        }
      }
    };

    setPhase("recording");
    let count = 5;
    setCountdown(count);
    recorder.start(100);

    const interval = setInterval(() => {
      count -= 1;
      setCountdown(count);
      if (count <= 0) {
        clearInterval(interval);
        recorder.stop();
      }
    }, 1000);
  }, [token]);

  // ── Helpers ───────────────────────────────────────────────────────────

  function getDecision(): { label: string; color: string; bg: string; Icon: typeof ShieldCheck } {
    const { deepfake, liveness } = results;
    if (!deepfake || !liveness)
      return { label: "UNKNOWN", color: C.muted, bg: "#f3f4f6", Icon: ShieldCheck };

    if (deepfake.is_deepfake || !liveness.is_alive) {
      return { label: "BLOCK — Deepfake detected", color: C.danger, bg: "#fee2e2", Icon: XCircle };
    }
    if (deepfake.confidence > 0.3 || liveness.confidence < 0.7) {
      return { label: "CHALLENGE — Suspicious", color: C.amber, bg: "#fef3c7", Icon: AlertTriangle };
    }
    return { label: "ALLOW — Verified real", color: C.success, bg: "#dcfce7", Icon: ShieldCheck };
  }

  const inputStyle: React.CSSProperties = {
    width: "100%",
    padding: "0.625rem 0.875rem",
    border: `1px solid ${C.border}`,
    borderRadius: 8,
    fontSize: 14,
    color: C.heading,
    background: C.pageBg,
    outline: "none",
  };

  // ── Render ────────────────────────────────────────────────────────────

  return (
    <div style={{ background: C.pageBg, color: C.heading, minHeight: "100vh" }}>
      <Nav />

      <div className="px-4 md:px-12 py-8 md:py-12" style={{ maxWidth: 900, margin: "0 auto" }}>
        {/* Header */}
        <div style={{ marginBottom: "2rem" }}>
          <div style={{ fontSize: 12, color: C.primary, fontWeight: 600, letterSpacing: 1, textTransform: "uppercase", marginBottom: 8 }}>
            Live detection
          </div>
          <h1 style={{ fontSize: 36, fontWeight: 700, color: C.heading, marginBottom: 8 }}>
            DeepShield Live Demo
          </h1>
          <p style={{ fontSize: 15, color: C.body }}>
            Record 5 seconds of video — DeepShield analyses it through the full
            detection pipeline in real time.
          </p>
        </div>

        {/* ── Auth phase ── */}
        {phase === "auth" && (
          <div style={{ maxWidth: 440 }}>
            {/* Quick demo card */}
            <div
              style={{
                background: C.primary,
                borderRadius: 14,
                padding: "1.5rem",
                marginBottom: "1rem",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "1rem",
                flexWrap: "wrap",
              }}
            >
              <div>
                <div style={{ fontSize: 15, fontWeight: 700, color: "#fff", marginBottom: 4 }}>
                  🚀 Try it instantly — no sign-up needed
                </div>
                <div style={{ fontSize: 13, color: C.borderAccent }}>
                  We&apos;ll create a temporary demo account for you automatically.
                </div>
              </div>
              <button
                onClick={handleQuickDemo}
                disabled={authLoading}
                style={{
                  background: "#fff",
                  color: C.primary,
                  border: "none",
                  padding: "0.625rem 1.25rem",
                  borderRadius: 8,
                  fontSize: 14,
                  fontWeight: 700,
                  cursor: authLoading ? "not-allowed" : "pointer",
                  opacity: authLoading ? 0.7 : 1,
                  whiteSpace: "nowrap",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                {authLoading ? <Loader2 size={14} className="animate-spin" /> : null}
                {authLoading ? "Setting up…" : "Quick demo →"}
              </button>
            </div>

            {/* Divider */}
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}>
              <div style={{ flex: 1, height: "0.5px", background: C.border }} />
              <span style={{ fontSize: 12, color: C.muted }}>or sign in with your account</span>
              <div style={{ flex: 1, height: "0.5px", background: C.border }} />
            </div>

            {/* Login form */}
            <div
              style={{
                background: C.card,
                border: `0.5px solid ${C.border}`,
                borderRadius: 16,
                padding: "2rem",
              }}
            >
            <h2 style={{ fontSize: 20, fontWeight: 700, color: C.heading, marginBottom: 4 }}>
              {isRegister ? "Create account" : "Sign in to continue"}
            </h2>
            <p style={{ fontSize: 14, color: C.body, marginBottom: "1.5rem" }}>
              {isRegister
                ? "Register a new account to access the live demo."
                : "Sign in with your DeepShield account to run the detector."}
            </p>

            <form onSubmit={handleAuth} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: C.heading, display: "block", marginBottom: 6 }}>
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="you@bank.com"
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: C.heading, display: "block", marginBottom: 6 }}>
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  style={inputStyle}
                />
              </div>

              {authError && (
                <div style={{ fontSize: 13, color: C.danger, background: "#fee2e2", padding: "0.5rem 0.875rem", borderRadius: 8 }}>
                  {authError}
                </div>
              )}

              <button
                type="submit"
                disabled={authLoading}
                style={{
                  background: C.primary,
                  color: "#fff",
                  border: "none",
                  padding: "0.75rem",
                  borderRadius: 10,
                  fontSize: 15,
                  fontWeight: 600,
                  cursor: authLoading ? "not-allowed" : "pointer",
                  opacity: authLoading ? 0.7 : 1,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 8,
                }}
              >
                {authLoading && <Loader2 size={16} className="animate-spin" />}
                {isRegister ? "Register & continue" : "Sign in"}
              </button>
            </form>

            <p style={{ fontSize: 13, color: C.body, marginTop: "1.25rem", textAlign: "center" }}>
              {isRegister ? "Already have an account? " : "No account yet? "}
              <button
                onClick={() => { setIsRegister(!isRegister); setAuthError(""); }}
                style={{ color: C.primary, background: "none", border: "none", cursor: "pointer", fontWeight: 500 }}
              >
                {isRegister ? "Sign in" : "Register"}
              </button>
            </p>
            </div>
          </div>
        )}

        {/* ── Webcam + controls ── */}
        {(phase === "ready" || phase === "recording") && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
            <div>
              <div
                style={{
                  borderRadius: 12,
                  overflow: "hidden",
                  border: `2px solid ${phase === "recording" ? C.danger : C.border}`,
                  position: "relative",
                }}
              >
                <Webcam
                  ref={webcamRef}
                  audio={false}
                  width="100%"
                  videoConstraints={{ facingMode: "user", width: 640, height: 480 }}
                  style={{ display: "block" }}
                />
                {phase === "recording" && (
                  <div
                    style={{
                      position: "absolute",
                      top: 12,
                      right: 12,
                      background: C.danger,
                      color: "#fff",
                      borderRadius: 8,
                      padding: "4px 12px",
                      fontSize: 13,
                      fontWeight: 600,
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#fff", display: "inline-block" }} />
                    REC {countdown}s
                  </div>
                )}
              </div>

              <button
                onClick={startAnalysis}
                disabled={phase === "recording"}
                style={{
                  marginTop: "1rem",
                  width: "100%",
                  background: phase === "recording" ? "#9ca3af" : C.primary,
                  color: "#fff",
                  border: "none",
                  padding: "0.875rem",
                  borderRadius: 10,
                  fontSize: 16,
                  fontWeight: 600,
                  cursor: phase === "recording" ? "not-allowed" : "pointer",
                }}
              >
                {phase === "recording" ? `Recording… ${countdown}s remaining` : "▶ Start 5-second analysis"}
              </button>
            </div>

            {/* Instructions panel */}
            <div
              style={{
                background: C.card,
                border: `0.5px solid ${C.border}`,
                borderRadius: 12,
                padding: "1.5rem",
              }}
            >
              <h3 style={{ fontSize: 16, fontWeight: 700, color: C.heading, marginBottom: "1rem" }}>
                How it works
              </h3>
              {[
                { n: "1", t: "Allow webcam access", b: "Click 'Allow' when your browser prompts for camera permission." },
                { n: "2", t: "Face the camera", b: "Position your face clearly in the frame with good lighting." },
                { n: "3", t: "Click Analyse", b: "DeepShield records 5 seconds and runs the full detection pipeline." },
                { n: "4", t: "Get your result", b: "See your deepfake score, liveness confidence, and risk decision." },
              ].map((step) => (
                <div key={step.n} style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem" }}>
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: 8,
                      background: C.primaryLight,
                      color: C.primary,
                      fontSize: 13,
                      fontWeight: 600,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    {step.n}
                  </div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: C.heading }}>{step.t}</div>
                    <div style={{ fontSize: 12, color: C.body, lineHeight: 1.5 }}>{step.b}</div>
                  </div>
                </div>
              ))}

              <div
                style={{
                  background: C.primaryLight,
                  border: `1px solid ${C.borderAccent}`,
                  borderRadius: 8,
                  padding: "0.75rem",
                  fontSize: 12,
                  color: C.primaryDark,
                  marginTop: "0.5rem",
                }}
              >
                🔒 Video is processed locally and sent directly to your DeepShield
                instance. No footage is stored.
              </div>
            </div>
          </div>
        )}

        {/* ── Analyzing ── */}
        {phase === "analyzing" && (
          <div
            style={{
              background: C.card,
              border: `0.5px solid ${C.border}`,
              borderRadius: 16,
              padding: "4rem 2rem",
              textAlign: "center",
            }}
          >
            <Loader2 size={48} color={C.primary} className="animate-spin mx-auto" />
            <h2 style={{ fontSize: 22, fontWeight: 700, color: C.heading, marginTop: "1.5rem", marginBottom: 8 }}>
              Analysing video…
            </h2>
            <p style={{ color: C.body, fontSize: 14 }}>
              Running deepfake detection + liveness verification in parallel.
            </p>
            <div style={{ display: "flex", gap: "1rem", justifyContent: "center", marginTop: "1.5rem", flexWrap: "wrap" }}>
              {["Frame extraction", "Neural network ensemble", "Liveness signals", "Risk scoring"].map((s) => (
                <span
                  key={s}
                  style={{
                    background: C.primaryLight,
                    color: C.primaryDark,
                    fontSize: 12,
                    padding: "4px 12px",
                    borderRadius: 20,
                    border: `1px solid ${C.borderAccent}`,
                  }}
                >
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ── Results ── */}
        {phase === "results" && results.deepfake && results.liveness && (() => {
          const decision = getDecision();
          const { Icon } = decision;
          const df = results.deepfake;
          const lv = results.liveness;
          const dfScore = ((df.is_deepfake ? df.confidence : 1 - df.confidence) * 100).toFixed(1);
          const lvScore = (lv.confidence * 100).toFixed(1);

          return (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Decision card */}
              <div
                style={{
                  background: decision.bg,
                  border: `1.5px solid ${decision.color}`,
                  borderRadius: 16,
                  padding: "2rem",
                  textAlign: "center",
                  gridColumn: "span 2",
                }}
              >
                <Icon size={48} color={decision.color} style={{ margin: "0 auto 1rem" }} />
                <div style={{ fontSize: 28, fontWeight: 700, color: decision.color }}>
                  {decision.label}
                </div>
                <div style={{ fontSize: 14, color: C.body, marginTop: 6 }}>
                  Analysis complete · {df.frame_count} frames processed
                </div>
              </div>

              {/* Deepfake card */}
              <div style={{ background: C.card, border: `0.5px solid ${C.border}`, borderRadius: 12, padding: "1.5rem" }}>
                <div style={{ fontSize: 12, color: C.muted, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1, marginBottom: "1rem" }}>
                  Deepfake Detection
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.75rem" }}>
                  <span style={{ fontSize: 13, color: C.body }}>Verdict</span>
                  <span style={{ fontSize: 13, fontWeight: 700, color: df.is_deepfake ? C.danger : C.success }}>
                    {df.is_deepfake ? "FAKE" : "REAL"}
                  </span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.75rem" }}>
                  <span style={{ fontSize: 13, color: C.body }}>Fake probability</span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: C.heading }}>{dfScore}%</span>
                </div>
                <div style={{ height: 6, background: "#f3f4f6", borderRadius: 3, overflow: "hidden", marginBottom: "0.75rem" }}>
                  <div
                    style={{
                      height: "100%",
                      width: `${dfScore}%`,
                      background: df.is_deepfake ? C.danger : C.success,
                      borderRadius: 3,
                    }}
                  />
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.75rem" }}>
                  <span style={{ fontSize: 13, color: C.body }}>Method</span>
                  <span style={{ fontSize: 13, color: C.heading }}>{df.detection_method}</span>
                </div>
                {df.anomalies.length > 0 && (
                  <div>
                    <div style={{ fontSize: 12, color: C.muted, marginBottom: 6 }}>Anomalies detected:</div>
                    {df.anomalies.map((a) => (
                      <div key={a} style={{ fontSize: 11, color: C.danger, background: "#fee2e2", padding: "2px 8px", borderRadius: 4, display: "inline-block", marginRight: 4, marginBottom: 4 }}>
                        {a}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Liveness card */}
              <div style={{ background: C.card, border: `0.5px solid ${C.border}`, borderRadius: 12, padding: "1.5rem" }}>
                <div style={{ fontSize: 12, color: C.muted, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1, marginBottom: "1rem" }}>
                  Liveness Verification
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.75rem" }}>
                  <span style={{ fontSize: 13, color: C.body }}>Verdict</span>
                  <span style={{ fontSize: 13, fontWeight: 700, color: lv.is_alive ? C.success : C.danger }}>
                    {lv.is_alive ? "LIVE" : "SPOOF"}
                  </span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.75rem" }}>
                  <span style={{ fontSize: 13, color: C.body }}>Confidence</span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: C.heading }}>{lvScore}%</span>
                </div>
                <div style={{ height: 6, background: "#f3f4f6", borderRadius: 3, overflow: "hidden", marginBottom: "0.75rem" }}>
                  <div
                    style={{
                      height: "100%",
                      width: `${lvScore}%`,
                      background: lv.is_alive ? C.success : C.danger,
                      borderRadius: 3,
                    }}
                  />
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ fontSize: 13, color: C.body }}>Challenge type</span>
                  <span style={{ fontSize: 13, color: C.heading }}>{lv.challenge_type}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", marginTop: "0.5rem" }}>
                  <span style={{ fontSize: 13, color: C.body }}>Frames analysed</span>
                  <span style={{ fontSize: 13, color: C.heading }}>{lv.frame_count}</span>
                </div>
              </div>

              <button
                onClick={() => { setPhase("ready"); setResults({ deepfake: null, liveness: null }); }}
                style={{
                  gridColumn: "span 2",
                  background: C.primary,
                  color: "#fff",
                  border: "none",
                  padding: "0.875rem",
                  borderRadius: 10,
                  fontSize: 15,
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                ↺ Run another analysis
              </button>
            </div>
          );
        })()}

        {/* ── ML unavailable ── */}
        {phase === "ml_unavailable" && (
          <div
            style={{
              background: C.card,
              border: `1px solid ${C.border}`,
              borderRadius: 16,
              padding: "2.5rem",
              textAlign: "center",
              maxWidth: 520,
            }}
          >
            <div style={{ fontSize: 48, marginBottom: "1rem" }}>🔧</div>
            <h2 style={{ fontSize: 22, fontWeight: 700, color: C.heading, marginBottom: 10 }}>
              ML services are warming up
            </h2>
            <p style={{ color: C.body, fontSize: 14, lineHeight: 1.7, marginBottom: "1.5rem" }}>
              The deepfake detection and liveness models are not yet loaded on
              this instance. This happens when TensorFlow or OpenCV dependencies
              are missing, or the backend is in lightweight mode.
            </p>
            <div
              style={{
                background: C.primaryLight,
                border: `1px solid ${C.borderAccent}`,
                borderRadius: 10,
                padding: "1rem",
                fontSize: 13,
                color: C.heading,
                textAlign: "left",
                marginBottom: "1.5rem",
                lineHeight: 1.8,
              }}
            >
              <strong>To enable ML detection:</strong>
              <br />1. Install dependencies: <code>pip install tensorflow opencv-python-headless</code>
              <br />2. Run model initialiser: <code>python initialize_ml_models.py</code>
              <br />3. Restart the backend server
            </div>
            <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center", flexWrap: "wrap" }}>
              <button
                onClick={() => setPhase("ready")}
                style={{
                  background: C.primary,
                  color: "#fff",
                  border: "none",
                  padding: "0.75rem 1.5rem",
                  borderRadius: 10,
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                ↺ Try again
              </button>
              <a
                href="/integration"
                style={{
                  background: C.card,
                  color: C.primary,
                  border: `1px solid ${C.borderAccent}`,
                  padding: "0.75rem 1.5rem",
                  borderRadius: 10,
                  fontSize: 14,
                  fontWeight: 600,
                  textDecoration: "none",
                }}
              >
                View API docs →
              </a>
            </div>
          </div>
        )}

        {/* ── Error ── */}
        {phase === "error" && (
          <div
            style={{
              background: "#fee2e2",
              border: `1px solid ${C.danger}`,
              borderRadius: 12,
              padding: "2rem",
              textAlign: "center",
            }}
          >
            <XCircle size={40} color={C.danger} style={{ margin: "0 auto 1rem" }} />
            <h2 style={{ fontSize: 20, fontWeight: 700, color: C.danger, marginBottom: 8 }}>
              Analysis failed
            </h2>
            <p style={{ color: C.body, marginBottom: "1.5rem" }}>{error}</p>
            <button
              onClick={() => setPhase("ready")}
              style={{
                background: C.danger,
                color: "#fff",
                border: "none",
                padding: "0.75rem 2rem",
                borderRadius: 10,
                fontSize: 14,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Try again
            </button>
          </div>
        )}
      </div>

      <Footer />
    </div>
  );
}
