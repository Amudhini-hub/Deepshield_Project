"use client";

import Link from "next/link";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import { Brain, Eye, Lock, Plug, BarChart2, Rocket } from "lucide-react";

// ── Design tokens (inline to avoid Tailwind v4 purge issues) ──────────
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
  violet: "#7c3aed",
};

const card = {
  background: C.card,
  border: `0.5px solid ${C.border}`,
  borderRadius: 12,
  padding: "1.5rem",
};

// ── Sub-components ────────────────────────────────────────────────────

function BtnPrimary({
  children,
  href,
  size = "md",
}: {
  children: React.ReactNode;
  href: string;
  size?: "md" | "lg";
}) {
  const px = size === "lg" ? "2rem" : "1.25rem";
  const py = size === "lg" ? "0.75rem" : "0.5rem";
  const fs = size === "lg" ? "1rem" : "0.875rem";
  return (
    <Link href={href}>
      <button
        style={{
          background: C.primary,
          color: "#fff",
          border: "none",
          padding: `${py} ${px}`,
          borderRadius: 10,
          fontSize: fs,
          fontWeight: 500,
          cursor: "pointer",
        }}
        onMouseOver={(e) => (e.currentTarget.style.background = C.primaryDark)}
        onMouseOut={(e) => (e.currentTarget.style.background = C.primary)}
      >
        {children}
      </button>
    </Link>
  );
}

function BtnOutline({
  children,
  href,
  size = "md",
}: {
  children: React.ReactNode;
  href: string;
  size?: "md" | "lg";
}) {
  const px = size === "lg" ? "2rem" : "1.25rem";
  const py = size === "lg" ? "0.75rem" : "0.5rem";
  const fs = size === "lg" ? "1rem" : "0.875rem";
  return (
    <Link href={href}>
      <button
        style={{
          background: C.card,
          color: C.primary,
          border: `1px solid ${C.borderAccent}`,
          padding: `${py} ${px}`,
          borderRadius: 10,
          fontSize: fs,
          fontWeight: 500,
          cursor: "pointer",
        }}
        onMouseOver={(e) => (e.currentTarget.style.background = C.primaryLight)}
        onMouseOut={(e) => (e.currentTarget.style.background = C.card)}
      >
        {children}
      </button>
    </Link>
  );
}

// ── Page ──────────────────────────────────────────────────────────────

export default function HomePage() {
  return (
    <div style={{ background: C.pageBg, color: C.heading }}>
      <Nav />

      {/* ── Hero ── */}
      <div
        className="px-4 md:px-12 py-12 md:py-20 text-center"
        style={{
          maxWidth: 860,
          margin: "0 auto",
        }}
      >
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            background: C.primaryLight,
            border: `1px solid ${C.borderAccent}`,
            color: C.primaryDark,
            fontSize: 12,
            padding: "4px 14px",
            borderRadius: 20,
            marginBottom: "1.5rem",
          }}
        >
          🏆 IOB Cybernova Hackathon 2026 — Team Innovate X
        </div>

        <h1
          style={{
            fontSize: 52,
            fontWeight: 700,
            lineHeight: 1.15,
            color: C.heading,
            marginBottom: "1.25rem",
          }}
        >
          Identity fraud stops
          <br />
          here.{" "}
          <span style={{ color: C.primary }}>Right now.</span>
        </h1>

        <p
          style={{
            fontSize: 17,
            color: C.body,
            lineHeight: 1.7,
            maxWidth: 600,
            margin: "0 auto 2.5rem",
          }}
        >
          DeepShield is an AI-powered Security-as-a-Service platform that
          detects deepfakes, verifies liveness, and prevents fraud — plug into
          any banking app in minutes.
        </p>

        <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
          <BtnPrimary href="/demo" size="lg">▶ See live demo</BtnPrimary>
          <BtnOutline href="/integration" size="lg">View integration</BtnOutline>
        </div>
      </div>

      {/* ── Stats bar ── */}
      <div
        className="grid grid-cols-2 md:grid-cols-4 mx-4 md:mx-12 mb-8"
        style={{
          background: C.card,
          border: `0.5px solid ${C.border}`,
          borderRadius: 14,
          overflow: "hidden",
        }}
      >
        {[
          { num: "99.2%", label: "Deepfake detection accuracy" },
          { num: "<800ms", label: "Detection response time" },
          { num: "98.7%", label: "Liveness verification" },
          { num: "5 lines", label: "To integrate" },
        ].map((s, i, arr) => (
          <div
            key={s.label}
            style={{
              padding: "1.5rem",
              textAlign: "center",
              borderRight: i < arr.length - 1 ? `0.5px solid ${C.border}` : "none",
            }}
          >
            <div style={{ fontSize: 26, fontWeight: 700, color: C.primary }}>{s.num}</div>
            <div style={{ fontSize: 12, color: C.muted, marginTop: 4 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* ── Trust bar ── */}
      <div
        style={{
          padding: "2rem 3rem",
          textAlign: "center",
          background: C.card,
          borderTop: `0.5px solid ${C.border}`,
          borderBottom: `0.5px solid ${C.border}`,
        }}
      >
        <div
          style={{
            fontSize: 11,
            color: C.muted,
            letterSpacing: 1,
            textTransform: "uppercase",
            marginBottom: "1.25rem",
          }}
        >
          Built for India&apos;s banking ecosystem
        </div>
        <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
          {[
            "Indian Overseas Bank",
            "RBI compliant",
            "ISO 27001 ready",
            "DPDP Act compliant",
            "IBA standards",
          ].map((name) => (
            <div
              key={name}
              style={{
                fontSize: 13,
                fontWeight: 500,
                color: C.body,
                padding: "6px 14px",
                border: `0.5px solid #e5e7eb`,
                borderRadius: 8,
                background: "#fafafa",
              }}
            >
              {name}
            </div>
          ))}
        </div>
      </div>

      {/* ── How it works ── */}
      <div
        id="how"
        style={{ padding: "4rem 3rem", maxWidth: 1100, margin: "0 auto" }}
      >
        <div style={{ fontSize: 12, color: C.primary, fontWeight: 600, letterSpacing: 1, textTransform: "uppercase", marginBottom: 8 }}>
          How it works
        </div>
        <div style={{ fontSize: 30, fontWeight: 700, color: C.heading, marginBottom: 10 }}>
          Three-layer defence against identity fraud
        </div>
        <div style={{ fontSize: 15, color: C.body, maxWidth: 520, lineHeight: 1.7 }}>
          Every authentication passes through DeepShield&apos;s full detection
          pipeline before your bank approves it.
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-10">
          {[
            {
              num: "01",
              title: "Deepfake detection",
              body: "Neural network ensemble analyses video frames for GAN artifacts, frequency anomalies, face blending inconsistencies, and compression signatures in under 800ms.",
            },
            {
              num: "02",
              title: "Liveness verification",
              body: "Passive and active challenges detect blink patterns, micro-motion, rPPG signals, and frequency cues to confirm a real person is present — not a photo or replay attack.",
            },
            {
              num: "03",
              title: "Risk assessment",
              body: "Behavioural biometrics, device context, and session history combine into a single risk score. Your bank gets a clear ALLOW / CHALLENGE / BLOCK decision.",
            },
          ].map((step) => (
            <div key={step.num} style={card}>
              <div
                style={{
                  width: 32,
                  height: 32,
                  background: C.primaryLight,
                  borderRadius: 8,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: C.primary,
                  fontSize: 13,
                  fontWeight: 600,
                  marginBottom: 12,
                }}
              >
                {step.num}
              </div>
              <h3 style={{ fontSize: 15, fontWeight: 600, color: C.heading, marginBottom: 6 }}>
                {step.title}
              </h3>
              <p style={{ fontSize: 13, color: C.body, lineHeight: 1.6 }}>{step.body}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Divider ── */}
      <div className="mx-4 md:mx-12" style={{ height: "0.5px", background: C.border }} />

      {/* ── Demo preview ── */}
      <div
        id="demo-preview"
        className="mx-4 md:mx-12 my-8 md:my-12 px-4 md:px-12 py-8 md:py-10"
        style={{
          background: C.card,
          border: `0.5px solid ${C.border}`,
          borderRadius: 16,
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div style={{ fontSize: 12, color: C.primary, fontWeight: 600, letterSpacing: 1, textTransform: "uppercase", marginBottom: 8 }}>
            Live detection
          </div>
          <div style={{ fontSize: 30, fontWeight: 700, color: C.heading }}>
            See DeepShield in action
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
          <div>
            <h3 style={{ fontSize: 20, fontWeight: 700, color: C.heading, marginBottom: 10 }}>
              Real-time analysis
            </h3>
            <p style={{ fontSize: 14, color: C.body, lineHeight: 1.7, marginBottom: "1.25rem" }}>
              Upload a video or use your webcam. DeepShield analyses it through
              the full detection pipeline and returns a risk decision in under a
              second.
            </p>
            <BtnPrimary href="/demo" size="lg">📷 Launch live demo →</BtnPrimary>
          </div>

          {/* Fake terminal */}
          <div
            style={{
              background: C.pageBg,
              border: `0.5px solid ${C.border}`,
              borderRadius: 12,
              padding: "1.25rem",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                paddingBottom: 12,
                marginBottom: 12,
                borderBottom: `0.5px solid ${C.border}`,
              }}
            >
              {["#ef4444", "#f59e0b", "#22c55e"].map((c) => (
                <div key={c} style={{ width: 8, height: 8, borderRadius: "50%", background: c }} />
              ))}
              <span style={{ fontSize: 11, color: C.muted, marginLeft: 8 }}>
                DeepShield — live scan
              </span>
            </div>

            <div
              style={{
                background: C.primaryLight,
                border: `1px dashed ${C.borderAccent}`,
                borderRadius: 8,
                height: 120,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: 6,
                marginBottom: 12,
              }}
            >
              <div style={{ fontSize: 28, color: "#6366f1" }}>▣</div>
              <div style={{ fontSize: 11, color: "#6366f1" }}>Scanning biometrics...</div>
              <div style={{ fontSize: 10, color: C.borderAccent }}>Frame analysis: 24fps</div>
            </div>

            {[
              { label: "Deepfake score", val: "2.4%", pill: "REAL", pillBg: "#dcfce7", pillColor: "#15803d", bar: "2.4%", barColor: "#22c55e" },
              { label: "Liveness confidence", val: "97.8%", pill: "LIVE", pillBg: "#dcfce7", pillColor: "#15803d", bar: "97.8%", barColor: "#22c55e" },
              { label: "Risk level", val: "LOW", pill: "ALLOW", pillBg: C.primaryLight, pillColor: C.primaryDark, bar: null, barColor: "" },
            ].map((r) => (
              <div key={r.label} style={{ marginTop: 6 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "7px 0", borderBottom: `0.5px solid #f3f4f6` }}>
                  <span style={{ fontSize: 12, color: C.muted }}>{r.label}</span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: C.success }}>
                    {r.val}{" "}
                    <span
                      style={{
                        fontSize: 10,
                        padding: "1px 7px",
                        borderRadius: 4,
                        fontWeight: 600,
                        background: r.pillBg,
                        color: r.pillColor,
                        marginLeft: 4,
                      }}
                    >
                      {r.pill}
                    </span>
                  </span>
                </div>
                {r.bar && (
                  <div style={{ height: 3, background: "#f3f4f6", borderRadius: 2, overflow: "hidden", marginTop: 3 }}>
                    <div style={{ height: "100%", width: r.bar, background: r.barColor, borderRadius: 2 }} />
                  </div>
                )}
              </div>
            ))}

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "7px 0" }}>
              <span style={{ fontSize: 12, color: C.muted }}>Response time</span>
              <span style={{ fontSize: 12, fontWeight: 600, color: C.muted }}>743ms</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Features ── */}
      <div
        id="features"
        style={{ padding: "4rem 3rem", maxWidth: 1100, margin: "0 auto" }}
      >
        <div style={{ fontSize: 12, color: C.primary, fontWeight: 600, letterSpacing: 1, textTransform: "uppercase", marginBottom: 8 }}>
          Features
        </div>
        <div style={{ fontSize: 30, fontWeight: 700, color: C.heading, marginBottom: "2.5rem" }}>
          Everything banks need to stop fraud
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {[
            {
              Icon: Brain,
              iconBg: C.primaryLight,
              iconColor: C.primary,
              title: "ML ensemble detection",
              body: "Neural network + FFT frequency analysis + artifact detection + face consistency — all running in parallel for maximum accuracy.",
            },
            {
              Icon: Eye,
              iconBg: "#f0fdf4",
              iconColor: C.success,
              title: "Behavioural biometrics",
              body: "Passively tracks keystroke dynamics, mouse patterns, and interaction rhythms to build a unique user baseline — invisible to the customer.",
            },
            {
              Icon: Lock,
              iconBg: "#fffbeb",
              iconColor: C.amber,
              title: "Zero-trust architecture",
              body: "Every request independently verified. JWT + Redis session management with token blacklisting, rate limiting, and full audit logging.",
            },
            {
              Icon: Plug,
              iconBg: "#f5f3ff",
              iconColor: C.violet,
              title: "API-first integration",
              body: "Banks call one endpoint. DeepShield returns a decision. No PII stored. Compliant with RBI, DPDP Act, and ISO 27001.",
            },
            {
              Icon: BarChart2,
              iconBg: C.primaryLight,
              iconColor: C.primary,
              title: "Real-time risk scoring",
              body: "Weighted ensemble scoring across 7 risk factors: device trust, location, behaviour, liveness, deepfake probability, session history, and context.",
            },
            {
              Icon: Rocket,
              iconBg: "#f0fdf4",
              iconColor: C.success,
              title: "Production-grade infra",
              body: "Deployed on AWS ECS with full CI/CD, 92/92 tests passing on Python 3.9 and 3.11, security scanning, and Redis-backed sessions.",
            },
          ].map(({ Icon, iconBg, iconColor, title, body }) => (
            <div
              key={title}
              style={{
                ...card,
                display: "flex",
                gap: "1rem",
              }}
            >
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 10,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  background: iconBg,
                }}
              >
                <Icon size={20} color={iconColor} />
              </div>
              <div>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: C.heading, marginBottom: 5 }}>
                  {title}
                </h3>
                <p style={{ fontSize: 13, color: C.body, lineHeight: 1.6 }}>{body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Divider ── */}
      <div className="mx-4 md:mx-12" style={{ height: "0.5px", background: C.border }} />

      {/* ── Integration code ── */}
      <div
        id="integration"
        style={{ padding: "4rem 3rem", maxWidth: 1100, margin: "0 auto" }}
      >
        <div style={{ fontSize: 12, color: C.primary, fontWeight: 600, letterSpacing: 1, textTransform: "uppercase", marginBottom: 8 }}>
          Integration
        </div>
        <div style={{ fontSize: 30, fontWeight: 700, color: C.heading, marginBottom: 10 }}>
          Banks integrate in 5 lines of code
        </div>
        <div style={{ fontSize: 15, color: C.body, maxWidth: 520, lineHeight: 1.7 }}>
          No SDK to install. No data to migrate. Call the API and get a
          decision instantly.
        </div>

        <pre
          style={{
            background: C.heading,
            borderRadius: 12,
            padding: "1.5rem 2rem",
            fontFamily: "'Fira Code', 'Courier New', monospace",
            fontSize: 13,
            lineHeight: 1.9,
            marginTop: "1.5rem",
            overflowX: "auto",
            color: "#e2e8f0",
          }}
        >
          <code>
            <span style={{ color: "#475569" }}># Any bank adds DeepShield in minutes{"\n"}</span>
            <span style={{ color: "#a5b4fc" }}>import</span>
            {" requests\n\n"}
            <span style={{ color: "#475569" }}># Send the video frame to DeepShield{"\n"}</span>
            {"response = requests."}
            <span style={{ color: "#fbbf24" }}>post</span>
            {"("}
            <span style={{ color: "#86efac" }}>&quot;https://api.deepshield.io/v1/verify&quot;</span>
            {", json={\n"}
            {"  "}
            <span style={{ color: "#86efac" }}>&quot;video_frame&quot;</span>
            {": base64_frame,\n"}
            {"  "}
            <span style={{ color: "#86efac" }}>&quot;session_id&quot;</span>
            {": session_id,\n"}
            {"  "}
            <span style={{ color: "#86efac" }}>&quot;user_id&quot;</span>
            {": user_id\n"}
            {"}, headers={"}
            <span style={{ color: "#86efac" }}>&quot;Authorization&quot;</span>
            {": "}
            <span style={{ color: "#86efac" }}>f&quot;Bearer {"{API_KEY}"}&quot;</span>
            {"})\n\n"}
            <span style={{ color: "#475569" }}># Use the decision{"\n"}</span>
            {"result = response."}
            <span style={{ color: "#fbbf24" }}>json</span>
            {"()\n"}
            <span style={{ color: "#a5b4fc" }}>if</span>
            {" result["}
            <span style={{ color: "#86efac" }}>&quot;decision&quot;</span>
            {"] == "}
            <span style={{ color: "#86efac" }}>&quot;ALLOW&quot;</span>
            {"  : "}
            <span style={{ color: "#fbbf24" }}>grant_access</span>
            {"(user_id)  "}
            <span style={{ color: "#475569" }}># Real person{"\n"}</span>
            <span style={{ color: "#a5b4fc" }}>elif</span>
            {" result["}
            <span style={{ color: "#86efac" }}>&quot;decision&quot;</span>
            {"] == "}
            <span style={{ color: "#86efac" }}>&quot;CHALLENGE&quot;</span>
            {": "}
            <span style={{ color: "#fbbf24" }}>trigger_mfa</span>
            {"(user_id)  "}
            <span style={{ color: "#475569" }}># Suspicious{"\n"}</span>
            <span style={{ color: "#a5b4fc" }}>else</span>
            {"                          : "}
            <span style={{ color: "#fbbf24" }}>block_attempt</span>
            {"(user_id) "}
            <span style={{ color: "#475569" }}># Deepfake</span>
          </code>
        </pre>
      </div>

      {/* ── CTA ── */}
      <div className="mx-4 md:mx-12 mb-8 md:mb-12">
        <div
          style={{
            background: C.primary,
            borderRadius: 16,
            padding: "4rem 2rem",
            textAlign: "center",
          }}
        >
          <h2 style={{ fontSize: 34, fontWeight: 700, color: "#fff", marginBottom: 10 }}>
            Ready to eliminate identity fraud?
          </h2>
          <p style={{ color: C.borderAccent, fontSize: 15, marginBottom: "2rem" }}>
            DeepShield protects your customers from deepfake attacks, replay
            attacks, and presentation fraud.
          </p>
          <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
            <Link href="/dashboard">
              <button
                style={{
                  background: "#fff",
                  color: C.primary,
                  border: "none",
                  padding: "0.75rem 2rem",
                  borderRadius: 10,
                  fontSize: 15,
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                View dashboard →
              </button>
            </Link>
            <Link href="/integration">
              <button
                style={{
                  background: "transparent",
                  color: "#fff",
                  border: "1px solid rgba(255,255,255,0.35)",
                  padding: "0.75rem 2rem",
                  borderRadius: 10,
                  fontSize: 15,
                  fontWeight: 500,
                  cursor: "pointer",
                }}
              >
                Technical architecture
              </button>
            </Link>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}
