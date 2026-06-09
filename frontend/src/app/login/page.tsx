"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Shield, Mail, Lock, AlertCircle, Loader2, Eye, EyeOff, ShieldCheck } from "lucide-react";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import { login } from "@/lib/api";
import { setToken, isAuthenticated } from "@/lib/auth";

const C = {
  blue: "#003580",
  blueLight: "#004aad",
  gold: "#C8922A",
  goldLight: "#FDF3E1",
  bg: "#f0f4f8",
  card: "#ffffff",
  heading: "#1a2332",
  body: "#4a5568",
  muted: "#718096",
  border: "#d1dce8",
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
        style={{ display: "block", fontSize: 12, fontWeight: 600, color: C.heading, marginBottom: 6, textTransform: "uppercase", letterSpacing: 0.5 }}
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
            color: focused ? C.blue : C.muted,
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
            padding: "0.7rem 2.5rem 0.7rem 2.35rem",
            border: `1.5px solid ${focused ? C.blue : C.border}`,
            borderRadius: 8,
            fontSize: 14,
            color: C.heading,
            background: focused ? "#fff" : C.bg,
            outline: "none",
            boxSizing: "border-box",
            transition: "border-color 0.15s, background 0.15s",
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
      setError(detail ?? "Invalid credentials. Please verify your Customer ID and password.");
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
    <div style={{ background: C.bg, minHeight: "100vh", display: "flex", flexDirection: "column" }}>
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
        <div style={{ width: "100%", maxWidth: 420 }}>

          {/* IOB branding header */}
          <div
            style={{
              background: C.blue,
              borderRadius: "12px 12px 0 0",
              padding: "1.5rem",
              textAlign: "center",
              borderBottom: `3px solid ${C.gold}`,
            }}
          >
            <div
              style={{
                width: 50,
                height: 50,
                background: C.gold,
                borderRadius: 12,
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: "0.875rem",
              }}
            >
              <Shield size={24} color="#fff" />
            </div>
            <div style={{ fontSize: 14, fontWeight: 700, color: C.gold, marginBottom: 3 }}>
              Indian Overseas Bank
            </div>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.7)" }}>
              Secure Authentication Portal
            </div>
          </div>

          {/* Card */}
          <div
            style={{
              background: C.card,
              border: `1px solid ${C.border}`,
              borderTop: "none",
              borderRadius: "0 0 12px 12px",
              padding: "2rem",
            }}
          >
            <div style={{ fontSize: 16, fontWeight: 700, color: C.heading, marginBottom: 4 }}>
              Customer Login
            </div>
            <div style={{ fontSize: 13, color: C.muted, marginBottom: "1.5rem" }}>
              Enter your registered credentials to proceed.
            </div>

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

            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <InputField
                label="Customer ID / Email"
                id="email"
                type="email"
                value={email}
                onChange={setEmail}
                placeholder="registered@email.com"
                icon={Mail}
                autoComplete="email"
              />

              <InputField
                label="Password / MPIN"
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
                  background: loading ? "#e5c98a" : C.gold,
                  color: "#fff",
                  border: "none",
                  padding: "0.8rem",
                  borderRadius: 8,
                  fontSize: 14,
                  fontWeight: 700,
                  cursor: loading ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 8,
                  transition: "background 0.15s",
                  marginTop: 4,
                }}
                onMouseOver={(e) => { if (!loading) e.currentTarget.style.background = "#b07e24"; }}
                onMouseOut={(e) => { if (!loading) e.currentTarget.style.background = C.gold; }}
              >
                {loading && <Loader2 size={15} className="animate-spin" />}
                {loading ? "Authenticating…" : "Secure Login →"}
              </button>
            </form>

            {/* Security indicators */}
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", justifyContent: "center", marginTop: "1.5rem", paddingTop: "1.25rem", borderTop: `1px solid ${C.border}` }}>
              {[
                { icon: ShieldCheck, label: "TLS Encrypted" },
                { icon: Lock, label: "JWT Sessions" },
                { icon: Shield, label: "AI Fraud Detection" },
              ].map(({ icon: Icon, label }) => (
                <div
                  key={label}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 4,
                    fontSize: 10,
                    fontWeight: 600,
                    color: C.blue,
                    background: "#e8f0fe",
                    border: `1px solid #c0d0ea`,
                    borderRadius: 20,
                    padding: "3px 9px",
                  }}
                >
                  <Icon size={10} />
                  {label}
                </div>
              ))}
            </div>
          </div>

          {/* Footer link */}
          <p style={{ textAlign: "center", fontSize: 13, color: C.body, marginTop: "1.25rem" }}>
            Don&apos;t have an account?{" "}
            <Link
              href="/register"
              style={{ color: C.blue, fontWeight: 600, textDecoration: "none" }}
              onMouseOver={(e) => (e.currentTarget.style.color = C.gold)}
              onMouseOut={(e) => (e.currentTarget.style.color = C.blue)}
            >
              Register →
            </Link>
          </p>

          <p style={{ textAlign: "center", fontSize: 11, color: C.muted, marginTop: "0.75rem" }}>
            By logging in, you agree to IOB&apos;s Terms of Service and Privacy Policy.
          </p>
        </div>
      </div>

      <Footer />
    </div>
  );
}
