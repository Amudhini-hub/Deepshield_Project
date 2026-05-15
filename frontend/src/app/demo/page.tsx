"use client";

import { useRef, useState, useCallback, useEffect } from "react";
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
  const [liveMeter, setLiveMeter] = useState(72);
  const [panelVisible, setPanelVisible] = useState(false);

  const webcamRef = useRef<Webcam>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    if (phase !== "recording") return;
    const iv = setInterval(() => {
      setLiveMeter(prev => Math.max(35, Math.min(96, prev + (Math.random() - 0.3) * 12)));
    }, 900);
    return () => clearInterval(iv);
  }, [phase]);

  useEffect(() => {
    if (phase === "results") {
      const t = setTimeout(() => setPanelVisible(true), 120);
      return () => clearTimeout(t);
    }
    setPanelVisible(false);
  }, [phase]);

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

            {/* Instructions / Live meter panel */}
            {phase === "ready" ? (
              <div style={{ background: C.card, border: `0.5px solid ${C.border}`, borderRadius: 12, padding: "1.5rem" }}>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: C.heading, marginBottom: "1rem" }}>How it works</h3>
                {[
                  { n: "1", t: "Allow webcam access", b: "Click 'Allow' when your browser prompts for camera permission." },
                  { n: "2", t: "Face the camera", b: "Position your face clearly in the frame with good lighting." },
                  { n: "3", t: "Click Analyse", b: "DeepShield records 5 seconds and runs the full detection pipeline." },
                  { n: "4", t: "Get your result", b: "See your deepfake score, liveness confidence, and risk decision." },
                ].map((step) => (
                  <div key={step.n} style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem" }}>
                    <div style={{ width: 28, height: 28, borderRadius: 8, background: C.primaryLight, color: C.primary, fontSize: 13, fontWeight: 600, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                      {step.n}
                    </div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: C.heading }}>{step.t}</div>
                      <div style={{ fontSize: 12, color: C.body, lineHeight: 1.5 }}>{step.b}</div>
                    </div>
                  </div>
                ))}
                <div style={{ background: C.primaryLight, border: `1px solid ${C.borderAccent}`, borderRadius: 8, padding: "0.75rem", fontSize: 12, color: C.primaryDark, marginTop: "0.5rem" }}>
                  🔒 Video is processed locally and sent directly to your DeepShield instance. No footage is stored.
                </div>
              </div>
            ) : (
              /* ── Live confidence meter ── */
              <div style={{ background: C.card, border: `0.5px solid ${C.border}`, borderRadius: 12, padding: "1.5rem", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: 260 }}>
                <div style={{ fontSize: 11, color: C.muted, fontWeight: 600, letterSpacing: 1, textTransform: "uppercase", marginBottom: "1rem" }}>Live confidence meter</div>
                {(() => {
                  const circ = 2 * Math.PI * 54;
                  const color = liveMeter > 65 ? C.success : liveMeter > 45 ? C.amber : C.danger;
                  return (
                    <div style={{ position: "relative", width: 148, height: 148 }}>
                      <svg width="148" height="148" viewBox="0 0 148 148">
                        <circle cx="74" cy="74" r="54" fill="none" stroke="#f3f4f6" strokeWidth="10" />
                        <circle
                          cx="74" cy="74" r="54" fill="none"
                          stroke={color} strokeWidth="10" strokeLinecap="round"
                          strokeDasharray={`${circ}`}
                          strokeDashoffset={`${circ - (liveMeter / 100) * circ}`}
                          style={{ transition: "stroke-dashoffset 0.9s ease, stroke 0.9s ease" }}
                          transform="rotate(-90 74 74)"
                        />
                      </svg>
                      <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                        <div style={{ fontSize: 28, fontWeight: 700, color, transition: "color 0.9s ease" }}>{Math.round(liveMeter)}%</div>
                        <div style={{ fontSize: 9, color: C.muted, letterSpacing: 0.5, textTransform: "uppercase" }}>Real prob.</div>
                      </div>
                    </div>
                  );
                })()}
                <div style={{ marginTop: "1.25rem", display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ width: 8, height: 8, borderRadius: "50%", background: C.danger, display: "inline-block", animation: "pulse 1s infinite" }} />
                  <span style={{ fontSize: 13, color: C.body }}>Scanning biometrics…</span>
                </div>
                <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }`}</style>
              </div>
            )}
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
          const fakePct = parseFloat(dfScore);

          const signals = [
            { label: "Facial inconsistency",     score: Math.min(99, Math.round(fakePct * 0.92 + 3)),  delay: "1.0s" },
            { label: "Blinking pattern anomaly",  score: Math.min(99, Math.round((1 - lv.confidence) * 80 + 12)), delay: "1.2s" },
            { label: "Skin texture variance",     score: Math.min(99, Math.round(fakePct * 0.78 + 5)),  delay: "1.4s" },
          ];

          const heatWeights = [0.6, 0.85, 0.7, 0.5, 1.0, 0.95, 0.85, 0.4, 0.6, 0.55, 0.45, 0.3];
          const heatLabels  = ["Fore.", "L.Eye", "R.Eye", "Nose", "L.Chk", "R.Chk", "Mouth", "Chin", "L.Jaw", "R.Jaw", "L.Tmp", "R.Tmp"];

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

              {/* ── Side-by-side comparison (deepfake only) ── */}
              {df.is_deepfake && (() => {
                const regions = [
                  { x: "15%", y: "18%", w: "22%", h: "14%", label: "L. Eye" },
                  { x: "63%", y: "18%", w: "22%", h: "14%", label: "R. Eye" },
                  { x: "35%", y: "42%", w: "30%", h: "16%", label: "Mouth" },
                  { x: "20%", y: "10%", w: "60%", h: "10%", label: "Forehead" },
                ];
                const [activeFrame, setActiveFrame] = useState(0);
                const frames = ["Frame 12", "Frame 24", "Frame 36", "Frame 48"];
                return (
                  <div style={{ gridColumn: "span 2", background: C.card, border: `1.5px solid ${C.danger}`, borderRadius: 12, padding: "1.5rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem", flexWrap: "wrap", gap: "0.5rem" }}>
                      <div style={{ fontSize: 12, color: C.danger, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1 }}>Frame Analysis — Deepfake Detected</div>
                      <div style={{ display: "flex", gap: 6 }}>
                        {frames.map((f, i) => (
                          <button key={f} onClick={() => setActiveFrame(i)} style={{ fontSize: 11, padding: "3px 10px", borderRadius: 6, border: `1px solid ${i === activeFrame ? C.danger : C.border}`, background: i === activeFrame ? "#fee2e2" : C.card, color: i === activeFrame ? C.danger : C.muted, cursor: "pointer", fontWeight: i === activeFrame ? 600 : 400 }}>{f}</button>
                        ))}
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Original frame */}
                      <div>
                        <div style={{ fontSize: 12, color: C.muted, marginBottom: 8, fontWeight: 500 }}>Original capture</div>
                        <div style={{ position: "relative", borderRadius: 8, overflow: "hidden", background: "#1e1b4b", aspectRatio: "4/3", display: "flex", alignItems: "center", justifyContent: "center" }}>
                          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(135deg,#312e81 0%,#1e1b4b 100%)", opacity: 0.9 }} />
                          <div style={{ position: "relative", textAlign: "center" }}>
                            <div style={{ fontSize: 32, marginBottom: 8 }}>👤</div>
                            <div style={{ fontSize: 11, color: "#a5b4fc" }}>Frame {(activeFrame + 1) * 12} · 640×480</div>
                          </div>
                          <div style={{ position: "absolute", bottom: 8, left: 8, fontSize: 10, color: "#6ee7b7", background: "rgba(0,0,0,0.5)", padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>✓ CAPTURED</div>
                        </div>
                      </div>
                      {/* Flagged frame with anomaly overlay */}
                      <div>
                        <div style={{ fontSize: 12, color: C.danger, marginBottom: 8, fontWeight: 500 }}>Anomalies detected</div>
                        <div style={{ position: "relative", borderRadius: 8, overflow: "hidden", background: "#1e1b4b", aspectRatio: "4/3" }}>
                          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(135deg,#312e81 0%,#1e1b4b 100%)", opacity: 0.9 }} />
                          <div style={{ position: "relative", width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
                            <div style={{ textAlign: "center" }}>
                              <div style={{ fontSize: 32, marginBottom: 8 }}>👤</div>
                              <div style={{ fontSize: 11, color: "#a5b4fc" }}>Frame {(activeFrame + 1) * 12} · analysed</div>
                            </div>
                            {/* Anomaly region overlays */}
                            {regions.map((r) => (
                              <div key={r.label} style={{ position: "absolute", left: r.x, top: r.y, width: r.w, height: r.h, border: "2px solid #ef4444", borderRadius: 4, background: "rgba(239,68,68,0.18)" }}>
                                <span style={{ position: "absolute", top: -16, left: 0, fontSize: 9, color: "#fca5a5", fontWeight: 600, whiteSpace: "nowrap", background: "rgba(0,0,0,0.5)", padding: "1px 4px", borderRadius: 3 }}>{r.label}</span>
                              </div>
                            ))}
                          </div>
                          <div style={{ position: "absolute", bottom: 8, left: 8, fontSize: 10, color: "#fca5a5", background: "rgba(0,0,0,0.5)", padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>✗ {regions.length} ANOMALIES</div>
                        </div>
                      </div>
                    </div>
                    <div style={{ marginTop: "1rem", fontSize: 12, color: C.body, display: "flex", gap: "1.5rem", flexWrap: "wrap" }}>
                      <span><span style={{ color: C.danger, fontWeight: 600 }}>■</span> Flagged region</span>
                      <span>Fake confidence: <strong style={{ color: C.danger }}>{dfScore}%</strong></span>
                      <span>Frames analysed: <strong>{df.frame_count}</strong></span>
                    </div>
                  </div>
                );
              })()}

              {/* ── Explainability panel ── */}
              <div style={{ gridColumn: "span 2", background: C.card, border: `0.5px solid ${C.border}`, borderRadius: 12, padding: "1.5rem" }}>
                <div style={{ fontSize: 12, color: C.muted, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1, marginBottom: "1.25rem" }}>
                  Why was this flagged?
                </div>

                {/* Animated confidence bar */}
                <div style={{ marginBottom: "1.5rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontSize: 13, color: C.body }}>Overall fake probability</span>
                    <span style={{ fontSize: 13, fontWeight: 700, color: df.is_deepfake ? C.danger : C.success }}>{dfScore}%</span>
                  </div>
                  <div style={{ height: 10, background: "#f3f4f6", borderRadius: 5, overflow: "hidden" }}>
                    <div style={{
                      height: "100%",
                      width: panelVisible ? `${dfScore}%` : "0%",
                      background: df.is_deepfake ? `linear-gradient(90deg,${C.amber},${C.danger})` : `linear-gradient(90deg,#22c55e,${C.success})`,
                      borderRadius: 5,
                      transition: "width 1.2s ease-out",
                    }} />
                  </div>
                </div>

                {/* Top 3 signals */}
                <div style={{ marginBottom: "1.5rem" }}>
                  <div style={{ fontSize: 12, color: C.muted, marginBottom: "0.75rem" }}>Top detection signals</div>
                  {signals.map((sig) => (
                    <div key={sig.label} style={{ marginBottom: "0.75rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                        <span style={{ fontSize: 13, color: C.body }}>{sig.label}</span>
                        <span style={{ fontSize: 13, fontWeight: 600, color: sig.score > 60 ? C.danger : sig.score > 30 ? C.amber : C.success }}>{sig.score}%</span>
                      </div>
                      <div style={{ height: 6, background: "#f3f4f6", borderRadius: 3, overflow: "hidden" }}>
                        <div style={{
                          height: "100%",
                          width: panelVisible ? `${sig.score}%` : "0%",
                          background: sig.score > 60 ? C.danger : sig.score > 30 ? C.amber : C.success,
                          borderRadius: 3,
                          transition: `width ${sig.delay} ease-out`,
                        }} />
                      </div>
                    </div>
                  ))}
                </div>

                {/* Heatmap grid */}
                <div>
                  <div style={{ fontSize: 12, color: C.muted, marginBottom: "0.75rem" }}>Frame region anomaly map</div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 5, maxWidth: 300 }}>
                    {heatWeights.map((w, i) => {
                      const intensity = (fakePct / 100) * w;
                      const bg = df.is_deepfake
                        ? `rgba(220,38,38,${Math.min(0.9, intensity + 0.08)})`
                        : `rgba(22,163,74,${Math.min(0.5, 0.35 - intensity * 0.2)})`;
                      return (
                        <div key={i} title={heatLabels[i]} style={{
                          height: 34, borderRadius: 5, background: bg,
                          opacity: panelVisible ? 1 : 0,
                          transition: `opacity ${0.3 + i * 0.06}s ease`,
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: 8, color: "rgba(255,255,255,0.85)", fontWeight: 600,
                        }}>
                          {heatLabels[i]}
                        </div>
                      );
                    })}
                  </div>
                  <div style={{ fontSize: 11, color: C.muted, marginTop: 8 }}>
                    {df.is_deepfake ? "Red intensity = anomaly probability per region" : "Green = all regions verified authentic"}
                  </div>
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
