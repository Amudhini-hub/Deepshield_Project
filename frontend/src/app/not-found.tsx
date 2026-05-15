import Link from "next/link";
import { Shield } from "lucide-react";

const C = {
  primary: "#4f46e5",
  primaryLight: "#eef2ff",
  borderAccent: "#c7d2fe",
  primaryDark: "#4338ca",
  heading: "#1e1b4b",
  body: "#6b7280",
  muted: "#9ca3af",
  pageBg: "#f8faff",
  card: "#ffffff",
  border: "#e0e7ff",
};

export default function NotFound() {
  return (
    <div
      style={{
        background: C.pageBg,
        color: C.heading,
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        textAlign: "center",
      }}
    >
      {/* Logo mark */}
      <div
        style={{
          width: 60,
          height: 60,
          background: C.primaryLight,
          borderRadius: 16,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: "1.5rem",
          border: `1px solid ${C.borderAccent}`,
        }}
      >
        <Shield size={30} color={C.primary} />
      </div>

      {/* 404 number */}
      <div
        style={{
          fontSize: "clamp(72px, 15vw, 96px)",
          fontWeight: 700,
          color: C.primary,
          lineHeight: 1,
          marginBottom: "0.5rem",
          letterSpacing: -2,
        }}
      >
        404
      </div>

      <h1 style={{ fontSize: 24, fontWeight: 700, color: C.heading, marginBottom: 10 }}>
        Page not found
      </h1>
      <p
        style={{
          fontSize: 15,
          color: C.body,
          maxWidth: 400,
          lineHeight: 1.7,
          marginBottom: "2.5rem",
        }}
      >
        This page doesn&apos;t exist or has been moved. DeepShield is still
        protecting your authentications — head back home to continue.
      </p>

      {/* CTAs */}
      <div
        style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", justifyContent: "center" }}
      >
        <Link href="/">
          <button
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
            ← Back to home
          </button>
        </Link>
        <Link href="/demo">
          <button
            style={{
              background: C.card,
              color: C.primary,
              border: `1px solid ${C.borderAccent}`,
              padding: "0.75rem 1.5rem",
              borderRadius: 10,
              fontSize: 14,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Try live demo →
          </button>
        </Link>
      </div>

      {/* Divider + footer hint */}
      <div
        style={{
          marginTop: "3rem",
          paddingTop: "1.5rem",
          borderTop: `0.5px solid ${C.border}`,
          width: "100%",
          maxWidth: 320,
        }}
      >
        <p style={{ fontSize: 12, color: C.muted }}>
          DeepShield · IOB Cybernova Hackathon 2026 · Team Innovate X
        </p>
      </div>
    </div>
  );
}
