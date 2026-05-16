"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Shield, Mail, Lock, AlertCircle, Loader2, Eye, EyeOff } from "lucide-react";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import { login } from "@/lib/api";
import { setToken, isAuthenticated } from "@/lib/auth";

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
  dangerBg: "#fee2e2",
};

function InputField({
  label,
  id,
  type,
  value,
  onChange,
  placeholder,
  icon: Icon,
  rightSlot,
  autoComplete,
}: {
  label: string;
  id: string;
  type: string;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  icon: React.ElementType;
  rightSlot?: React.ReactNode;
  autoComplete?: string;
}) {
  const [focused, setFocused] = useState(false);
  return (
    <div>
      <label
        htmlFor={id}
        style={{ display: "block", fontSize: 13, fontWeight: 500, color: C.heading, marginBottom: 6 }}
      >
        {label}
      </label>
      <div style={{ position: "relative" }}>
        <div
          style={{
            position: "absolute",
            left: 12,
            top: "50%",
            transform: "translateY(-50%)",
            color: focused ? C.primary : C.muted,
            pointerEvents: "none",
            display: "flex",
          }}
        >
          <Icon size={15} />
        </div>
        <input
          id={id}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={placeholder}
          autoComplete={autoComplete}
          required
          style={{
            width: "100%",
            padding: "0.65rem 2.5rem 0.65rem 2.25rem",
            border: `1px solid ${focused ? C.primary : C.border}`,
            borderRadius: 8,
            fontSize: 14,
            color: C.heading,
            background: C.pageBg,
            outline: "none",
            boxSizing: "border-box",
            transition: "border-color 0.15s",
          }}
        />
        {rightSlot && (
          <div style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)" }}>
            {rightSlot}
          </div>
        )}
      </div>
    </div>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated()) router.replace("/dashboard");
  }, [router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await login(email, password);
      setToken(res.access_token);
      router.push("/dashboard");
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? "Invalid email or password. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const toggleBtn = (
    <button
      type="button"
      onClick={() => setShowPw((p) => !p)}
      style={{ background: "none", border: "none", cursor: "pointer", color: C.muted, display: "flex", padding: 2 }}
      aria-label={showPw ? "Hide password" : "Show password"}
    >
      {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
    </button>
  );

  return (
    <div style={{ background: C.pageBg, minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Nav />

      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "3rem 1rem",
        }}
      >
        <div style={{ width: "100%", maxWidth: 400 }}>

          {/* Logo + heading */}
          <div style={{ textAlign: "center", marginBottom: "2rem" }}>
            <div
              style={{
                width: 48,
                height: 48,
                background: C.primary,
                borderRadius: 14,
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: "1rem",
              }}
            >
              <Shield size={24} color="#fff" />
            </div>
            <h1 style={{ fontSize: 24, fontWeight: 700, color: C.heading, margin: "0 0 6px" }}>
              Welcome back
            </h1>
            <p style={{ fontSize: 14, color: C.body, margin: 0 }}>
              Sign in to your DeepShield account
            </p>
          </div>

          {/* Card */}
          <div
            style={{
              background: C.card,
              border: `0.5px solid ${C.border}`,
              borderRadius: 16,
              padding: "2rem",
            }}
          >
            {/* Error banner */}
            {error && (
              <div
                role="alert"
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 8,
                  background: C.dangerBg,
                  border: `1px solid #fecaca`,
                  borderRadius: 8,
                  padding: "0.75rem 0.875rem",
                  marginBottom: "1.25rem",
                }}
              >
                <AlertCircle size={15} color={C.danger} style={{ flexShrink: 0, marginTop: 1 }} />
                <span style={{ fontSize: 13, color: C.danger, lineHeight: 1.5 }}>{error}</span>
              </div>
            )}

            <form
              onSubmit={handleSubmit}
              style={{ display: "flex", flexDirection: "column", gap: "1rem" }}
            >
              <InputField
                label="Email address"
                id="email"
                type="email"
                value={email}
                onChange={setEmail}
                placeholder="you@example.com"
                icon={Mail}
                autoComplete="email"
              />

              <InputField
                label="Password"
                id="password"
                type={showPw ? "text" : "password"}
                value={password}
                onChange={setPassword}
                placeholder="Enter your password"
                icon={Lock}
                rightSlot={toggleBtn}
                autoComplete="current-password"
              />

              <button
                type="submit"
                disabled={loading}
                style={{
                  width: "100%",
                  background: loading ? C.borderAccent : C.primary,
                  color: "#fff",
                  border: "none",
                  padding: "0.75rem",
                  borderRadius: 8,
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: loading ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 8,
                  transition: "background 0.15s",
                  marginTop: 4,
                }}
                onMouseOver={(e) => {
                  if (!loading) e.currentTarget.style.background = C.primaryDark;
                }}
                onMouseOut={(e) => {
                  if (!loading) e.currentTarget.style.background = C.primary;
                }}
              >
                {loading && <Loader2 size={15} className="animate-spin" />}
                {loading ? "Signing in…" : "Sign in →"}
              </button>
            </form>
          </div>

          {/* Footer link */}
          <p style={{ textAlign: "center", fontSize: 13, color: C.body, marginTop: "1.25rem" }}>
            Don&apos;t have an account?{" "}
            <Link
              href="/register"
              style={{ color: C.primary, fontWeight: 500, textDecoration: "none" }}
              onMouseOver={(e) => (e.currentTarget.style.textDecoration = "underline")}
              onMouseOut={(e) => (e.currentTarget.style.textDecoration = "none")}
            >
              Create one →
            </Link>
          </p>
        </div>
      </div>

      <Footer />
    </div>
  );
}
