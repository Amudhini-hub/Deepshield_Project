"use client";

import Link from "next/link";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import { Brain, Eye, Lock, Plug, BarChart2, ShieldCheck } from "lucide-react";

const C = {
  blue: "#003580",
  blueLight: "#004aad",
  blueDark: "#002460",
  gold: "#C8922A",
  goldLight: "#FDF3E1",
  goldHover: "#b07e24",
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

const card: React.CSSProperties = {
  background: C.card,
  border: `1px solid ${C.border}`,
  borderRadius: 12,
  padding: "1.5rem",
};

function BtnGold({ children, href, size = "md" }: { children: React.ReactNode; href: string; size?: "md" | "lg" }) {
  const px = size === "lg" ? "2rem" : "1.5rem";
  const py = size === "lg" ? "0.875rem" : "0.65rem";
  const fs = size === "lg" ? "15px" : "14px";
  return (
    <Link href={href}>
      <button
        style={{ background: C.gold, color: "#fff", border: "none", padding: `${py} ${px}`, borderRadius: 8, fontSize: fs, fontWeight: 600, cursor: "pointer", minHeight: 44 }}
        onMouseOver={(e) => (e.currentTarget.style.background = C.goldHover)}
        onMouseOut={(e) => (e.currentTarget.style.background = C.gold)}
      >
        {children}
      </button>
    </Link>
  );
}

function BtnOutline({ children, href, size = "md" }: { children: React.ReactNode; href: string; size?: "md" | "lg" }) {
  const px = size === "lg" ? "2rem" : "1.5rem";
  const py = size === "lg" ? "0.875rem" : "0.65rem";
  const fs = size === "lg" ? "15px" : "14px";
  return (
    <Link href={href}>
      <button
        style={{ background: "transparent", color: C.blue, border: `1.5px solid ${C.blue}`, padding: `${py} ${px}`, borderRadius: 8, fontSize: fs, fontWeight: 600, cursor: "pointer", minHeight: 44 }}
        onMouseOver={(e) => (e.currentTarget.style.background = "#e8f0fe")}
        onMouseOut={(e) => (e.currentTarget.style.background = "transparent")}
      >
        {children}
      </button>
    </Link>
  );
}

export default function HomePage() {
  return (
    <div style={{ background: C.bg, color: C.heading }}>
      <Nav />

      {/* ── Hero ── */}
      <div
        style={{
          background: `linear-gradient(135deg, ${C.blueDark} 0%, ${C.blue} 60%, ${C.blueLight} 100%)`,
          padding: "4rem 2rem 5rem",
          textAlign: "center",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Subtle grid overlay */}
        <div style={{ position: "absolute", inset: 0, backgroundImage: "radial-gradient(rgba(200,146,42,0.06) 1px, transparent 1px)", backgroundSize: "28px 28px", pointerEvents: "none" }} />

        <div style={{ maxWidth: 780, margin: "0 auto", position: "relative" }}>
          {/* IOB badge */}
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              background: "rgba(200,146,42,0.15)",
              border: `1px solid rgba(200,146,42,0.5)`,
              color: C.gold,
              fontSize: 12,
              fontWeight: 600,
              padding: "5px 16px",
              borderRadius: 20,
              marginBottom: "1.75rem",
              letterSpacing: 0.5,
            }}
          >
            <ShieldCheck size={13} />
            IOB Cybernova Hackathon 2026 · Team Innovate X
          </div>

          <h1
            style={{
              fontSize: "clamp(28px, 6vw, 50px)",
              fontWeight: 700,
              lineHeight: 1.15,
              color: "#ffffff",
              marginBottom: "1.25rem",
            }}
          >
            AI-Powered Deepfake Detection
            <br />
            <span style={{ color: C.gold }}>for Indian Overseas Bank</span>
          </h1>

          <p
            style={{
              fontSize: 16,
              color: "rgba(255,255,255,0.78)",
              lineHeight: 1.75,
              maxWidth: 560,
              margin: "0 auto 2.5rem",
            }}
          >
            DeepShield protects IOB customers from identity fraud, deepfake video attacks, and
            presentation spoofing — in real-time, at every authentication checkpoint.
          </p>

          <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
            <BtnGold href="/demo" size="lg">▶ Launch Identity Verification Demo</BtnGold>
            <Link href="/integration">
              <button
                style={{ background: "transparent", color: "rgba(255,255,255,0.85)", border: "1.5px solid rgba(255,255,255,0.35)", padding: "0.875rem 2rem", borderRadius: 8, fontSize: 15, fontWeight: 600, cursor: "pointer" }}
                onMouseOver={(e) => (e.currentTarget.style.borderColor = C.gold)}
                onMouseOut={(e) => (e.currentTarget.style.borderColor = "rgba(255,255,255,0.35)")}
              >
                View Integration Docs
              </button>
            </Link>
          </div>
        </div>
      </div>

      {/* ── Stats bar ── */}
      <div
        className="grid grid-cols-2 md:grid-cols-4"
        style={{ background: C.card, borderBottom: `1px solid ${C.border}`, borderTop: `3px solid ${C.gold}` }}
      >
        {[
          { num: "AI Ensemble", label: "Deepfake detection method" },
          { num: "Real-Time", label: "On-device parallel analysis" },
          { num: "3-Layer", label: "Anti-spoofing defence" },
          { num: "REST API", label: "Simple bank integration" },
        ].map((s, i) => (
          <div
            key={s.label}
            style={{
              padding: "1.5rem",
              textAlign: "center",
              borderRight: i < 3 ? `1px solid ${C.border}` : "none",
            }}
          >
            <div style={{ fontSize: 26, fontWeight: 700, color: C.blue }}>{s.num}</div>
            <div style={{ fontSize: 12, color: C.muted, marginTop: 4 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* ── Compliance bar ── */}
      <div
        style={{
          padding: "1.5rem 2rem",
          textAlign: "center",
          background: C.goldLight,
          borderBottom: `1px solid #e8d5a8`,
        }}
      >
        <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase", marginBottom: "0.875rem" }}>
          Compliance &amp; Standards
        </div>
        <div style={{ display: "flex", gap: "0.625rem", justifyContent: "center", flexWrap: "wrap" }}>
          {["RBI Guidelines", "DPDP Act 2023", "ISO 27001 Framework", "IBA Standards", "PCI-DSS Aligned"].map((name) => (
            <div
              key={name}
              style={{
                fontSize: 12,
                fontWeight: 600,
                color: C.blue,
                padding: "5px 14px",
                border: `1px solid #c0b07a`,
                borderRadius: 20,
                background: "#fff",
              }}
            >
              {name}
            </div>
          ))}
        </div>
      </div>

      {/* ── How it works ── */}
      <div id="how" style={{ padding: "4rem 2rem", maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase", marginBottom: 8 }}>
          How it works
        </div>
        <div style={{ fontSize: 28, fontWeight: 700, color: C.heading, marginBottom: 10 }}>
          Three-layer defence against identity fraud
        </div>
        <div style={{ fontSize: 15, color: C.body, maxWidth: 520, lineHeight: 1.7 }}>
          Every IOB authentication passes through DeepShield&apos;s full detection pipeline before access is granted.
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-8">
          {[
            {
              num: "01",
              title: "Deepfake Detection",
              body: "Neural network ensemble analyses video frames for GAN artifacts, frequency anomalies, face blending inconsistencies, and compression signatures — all in parallel.",
            },
            {
              num: "02",
              title: "Liveness Verification",
              body: "Passive and active challenges detect blink patterns, micro-motion, rPPG signals, and frequency cues to confirm a real person — not a photo or replay attack.",
            },
            {
              num: "03",
              title: "Risk Assessment",
              body: "Behavioural biometrics, device context, and session history combine into a single risk score. Returns ALLOW / CHALLENGE / BLOCK for instant decision-making.",
            },
          ].map((step) => (
            <div key={step.num} style={{ ...card, borderTop: `3px solid ${C.gold}` }}>
              <div
                style={{
                  width: 34,
                  height: 34,
                  background: C.goldLight,
                  border: `1px solid #e8d5a8`,
                  borderRadius: 8,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: C.gold,
                  fontSize: 13,
                  fontWeight: 700,
                  marginBottom: 14,
                }}
              >
                {step.num}
              </div>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: C.heading, marginBottom: 8 }}>{step.title}</h3>
              <p style={{ fontSize: 13, color: C.body, lineHeight: 1.65 }}>{step.body}</p>
            </div>
          ))}
        </div>
      </div>

      <div style={{ height: "1px", background: C.border, margin: "0 2rem" }} />

      {/* ── Demo preview ── */}
      <div
        style={{ margin: "2rem", padding: "2.5rem", background: C.card, border: `1px solid ${C.border}`, borderRadius: 16 }}
      >
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase", marginBottom: 8 }}>
            Live verification portal
          </div>
          <div style={{ fontSize: 28, fontWeight: 700, color: C.heading }}>
            See DeepShield in action
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
          <div>
            <h3 style={{ fontSize: 20, fontWeight: 700, color: C.heading, marginBottom: 10 }}>
              Real-time identity analysis
            </h3>
            <p style={{ fontSize: 14, color: C.body, lineHeight: 1.75, marginBottom: "1.5rem" }}>
              Use the live demo to experience IOB&apos;s deepfake detection pipeline. Allow camera access,
              position your face, and get a verification decision in under a second.
            </p>
            <BtnGold href="/demo" size="lg">Launch Identity Verification →</BtnGold>
          </div>

          {/* Terminal preview */}
          <div style={{ background: C.bg, border: `1px solid ${C.border}`, borderRadius: 12, padding: "1.25rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, paddingBottom: 12, marginBottom: 12, borderBottom: `1px solid ${C.border}` }}>
              {["#ef4444", "#f59e0b", "#22c55e"].map((c) => (
                <div key={c} style={{ width: 8, height: 8, borderRadius: "50%", background: c }} />
              ))}
              <span style={{ fontSize: 11, color: C.muted, marginLeft: 8 }}>IOB DeepShield — live scan</span>
            </div>

            <div
              style={{
                background: "#e8f0fe",
                border: `1px dashed ${C.border}`,
                borderRadius: 8,
                height: 110,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: 6,
                marginBottom: 12,
              }}
            >
              <div style={{ fontSize: 26, color: C.blue }}>▣</div>
              <div style={{ fontSize: 11, color: C.blue, fontWeight: 600 }}>Scanning biometrics...</div>
              <div style={{ fontSize: 10, color: C.muted }}>Frame analysis: 24fps</div>
            </div>

            {[
              { label: "Deepfake score", val: "2.4%", pill: "REAL", pillBg: "#dcfce7", pillColor: "#15803d", bar: "2.4%", barColor: "#22c55e" },
              { label: "Liveness confidence", val: "97.8%", pill: "LIVE", pillBg: "#dcfce7", pillColor: "#15803d", bar: "97.8%", barColor: "#22c55e" },
              { label: "Authentication status", val: "VERIFIED", pill: "ALLOW", pillBg: "#dcfce7", pillColor: "#15803d", bar: null, barColor: "" },
            ].map((r) => (
              <div key={r.label} style={{ marginTop: 6 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "7px 0", borderBottom: `0.5px solid #f3f4f6` }}>
                  <span style={{ fontSize: 12, color: C.muted }}>{r.label}</span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: C.success }}>
                    {r.val}{" "}
                    <span style={{ fontSize: 10, padding: "1px 7px", borderRadius: 4, fontWeight: 600, background: r.pillBg, color: r.pillColor, marginLeft: 4 }}>
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
              <span style={{ fontSize: 12, fontWeight: 600, color: C.blue }}>sample output</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Features ── */}
      <div id="features" style={{ padding: "4rem 2rem", maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase", marginBottom: 8 }}>
          Platform capabilities
        </div>
        <div style={{ fontSize: 28, fontWeight: 700, color: C.heading, marginBottom: "2.5rem" }}>
          Everything IOB needs to stop fraud
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {[
            {
              Icon: Brain,
              iconBg: "#e8f0fe",
              iconColor: C.blue,
              title: "ML Ensemble Detection",
              body: "Neural network + FFT frequency analysis + artifact detection + face consistency — all running in parallel for maximum accuracy.",
            },
            {
              Icon: Eye,
              iconBg: "#f0fdf4",
              iconColor: C.success,
              title: "Behavioural Biometrics",
              body: "Passively tracks keystroke dynamics, mouse patterns, and interaction rhythms to build a unique customer baseline — invisible to the user.",
            },
            {
              Icon: Lock,
              iconBg: C.goldLight,
              iconColor: C.gold,
              title: "Zero-Trust Architecture",
              body: "Every request independently verified. JWT + Redis session management with token blacklisting, rate limiting, and full audit logging.",
            },
            {
              Icon: Plug,
              iconBg: "#f5f3ff",
              iconColor: "#7c3aed",
              title: "API-First Integration",
              body: "Banks call one endpoint. DeepShield returns a decision. No PII stored. Designed for alignment with RBI, DPDP Act, and ISO 27001 guidelines.",
            },
            {
              Icon: BarChart2,
              iconBg: "#e8f0fe",
              iconColor: C.blue,
              title: "Real-Time Risk Scoring",
              body: "Weighted ensemble scoring across 7 risk factors: device trust, location, behaviour, liveness, deepfake probability, session history, and context.",
            },
            {
              Icon: ShieldCheck,
              iconBg: "#f0fdf4",
              iconColor: C.success,
              title: "Production-Grade Infrastructure",
              body: "FastAPI backend with async Celery workers, Redis-backed JWT sessions with token blacklisting, full audit logging, and container-based deployment.",
            },
          ].map(({ Icon, iconBg, iconColor, title, body }) => (
            <div key={title} style={{ ...card, display: "flex", gap: "1rem" }}>
              <div style={{ width: 42, height: 42, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, background: iconBg }}>
                <Icon size={20} color={iconColor} />
              </div>
              <div>
                <h3 style={{ fontSize: 14, fontWeight: 700, color: C.heading, marginBottom: 6 }}>{title}</h3>
                <p style={{ fontSize: 13, color: C.body, lineHeight: 1.65 }}>{body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ height: "1px", background: C.border, margin: "0 2rem" }} />

      {/* ── Integration ── */}
      <div id="integration" style={{ padding: "4rem 2rem", maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase", marginBottom: 8 }}>
          Integration
        </div>
        <div style={{ fontSize: 28, fontWeight: 700, color: C.heading, marginBottom: 10 }}>
          Banks integrate with a REST API
        </div>
        <div style={{ fontSize: 15, color: C.body, maxWidth: 520, lineHeight: 1.7 }}>
          No SDK to install. No data to migrate. Call the API and get a decision instantly.
        </div>

        <pre
          style={{
            background: "#0f1923",
            borderRadius: 12,
            padding: "1.5rem 2rem",
            fontFamily: "'Fira Code', 'Courier New', monospace",
            fontSize: 13,
            lineHeight: 1.9,
            marginTop: "1.5rem",
            overflowX: "auto",
            color: "#e2e8f0",
            borderLeft: `4px solid ${C.gold}`,
          }}
        >
          <code>
            <span style={{ color: "#475569" }}># IOB integrates DeepShield in minutes{"\n"}</span>
            <span style={{ color: "#a5b4fc" }}>import</span>
            {" requests\n\n"}
            <span style={{ color: "#475569" }}># Send the video frame to DeepShield{"\n"}</span>
            {"response = requests."}
            <span style={{ color: "#fbbf24" }}>post</span>
            {"("}
            <span style={{ color: "#86efac" }}>&quot;https://api.deepshield.io/v1/verify&quot;</span>
            {", json={\n"}
            {"  "}<span style={{ color: "#86efac" }}>&quot;video_frame&quot;</span>{": base64_frame,\n"}
            {"  "}<span style={{ color: "#86efac" }}>&quot;session_id&quot;</span>{": session_id,\n"}
            {"  "}<span style={{ color: "#86efac" }}>&quot;user_id&quot;</span>{": user_id\n"}
            {"}, headers={"}
            <span style={{ color: "#86efac" }}>&quot;Authorization&quot;</span>
            {": "}
            <span style={{ color: "#86efac" }}>f&quot;Bearer {"{API_KEY}"}&quot;</span>
            {"})\n\n"}
            <span style={{ color: "#475569" }}># Grant or deny access{"\n"}</span>
            {"result = response."}<span style={{ color: "#fbbf24" }}>json</span>{"()\n"}
            <span style={{ color: "#a5b4fc" }}>if</span>{" result["}<span style={{ color: "#86efac" }}>&quot;decision&quot;</span>{"] == "}<span style={{ color: "#86efac" }}>&quot;ALLOW&quot;</span>{"    : "}<span style={{ color: "#fbbf24" }}>grant_access</span>{"(user_id)   "}<span style={{ color: "#475569" }}># Real person{"\n"}</span>
            <span style={{ color: "#a5b4fc" }}>elif</span>{" result["}<span style={{ color: "#86efac" }}>&quot;decision&quot;</span>{"] == "}<span style={{ color: "#86efac" }}>&quot;CHALLENGE&quot;</span>{" : "}<span style={{ color: "#fbbf24" }}>trigger_mfa</span>{"(user_id)   "}<span style={{ color: "#475569" }}># Suspicious{"\n"}</span>
            <span style={{ color: "#a5b4fc" }}>else</span>{"                           : "}<span style={{ color: "#fbbf24" }}>block_attempt</span>{"(user_id)  "}<span style={{ color: "#475569" }}># Deepfake</span>
          </code>
        </pre>
      </div>

      {/* ── CTA ── */}
      <div style={{ margin: "0 2rem 3rem" }}>
        <div
          style={{
            background: `linear-gradient(135deg, ${C.blueDark} 0%, ${C.blue} 100%)`,
            borderRadius: 16,
            padding: "3.5rem 2rem",
            textAlign: "center",
            borderTop: `4px solid ${C.gold}`,
          }}
        >
          <h2 style={{ fontSize: 32, fontWeight: 700, color: "#fff", marginBottom: 10 }}>
            Ready to protect IOB customers?
          </h2>
          <p style={{ color: "rgba(255,255,255,0.72)", fontSize: 15, marginBottom: "2rem", maxWidth: 480, margin: "0 auto 2rem" }}>
            DeepShield shields your customers from deepfake attacks, replay attacks, and presentation fraud in real-time.
          </p>
          <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
            <Link href="/dashboard">
              <button
                style={{ background: C.gold, color: "#fff", border: "none", padding: "0.875rem 2rem", borderRadius: 10, fontSize: 15, fontWeight: 600, cursor: "pointer" }}
                onMouseOver={(e) => (e.currentTarget.style.background = C.goldHover)}
                onMouseOut={(e) => (e.currentTarget.style.background = C.gold)}
              >
                View Security Dashboard →
              </button>
            </Link>
            <Link href="/integration">
              <button
                style={{ background: "transparent", color: "#fff", border: "1px solid rgba(255,255,255,0.35)", padding: "0.875rem 2rem", borderRadius: 10, fontSize: 15, fontWeight: 500, cursor: "pointer" }}
              >
                Technical Architecture
              </button>
            </Link>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}
