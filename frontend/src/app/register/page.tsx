"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Shield, Mail, Lock, AlertCircle, CheckCircle, Loader2, Eye, EyeOff } from "lucide-react";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import { register, login } from "@/lib/api";
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
  success: "#16a34a",
  successBg: "#dcfce7",
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
  hint,
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
  hint?: React.ReactNode;
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
      {hint && <div style={{ marginTop: 5 }}>{hint}</div>}
    </div>
  );
}

function PasswordStrength({ password }: { password: string }) {
  if (!password) return null;

  const checks = [
    { label: "8+ characters", pass: password.length >= 8 },
    { label: "uppercase", pass: /[A-Z]/.test(password) },
    { label: "number", pass: /[0-9]/.test(password) },
  ];
  const score = checks.filter((c) => c.pass).length;
  const barColor = score === 1 ? C.danger : score === 2 ? "#d97706" : C.success;

  return (
    <div>
      <div style={{ display: "flex", gap: 4, marginBottom: 5 }}>
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              flex: 1,
              height: 3,
              borderRadius: 2,
              background: i < score ? barColor : "#e5e7eb",
              transition: "background 0.2s",
            }}
          />
        ))}
      </div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        {checks.map(({ label, pass }) => (
          <span
            key={label}
            style={{ fontSize: 11, color: pass ? C.success : C.muted, display: "flex", alignItems: "center", gap: 3 }}
          >
            <span style={{ fontSize: 10 }}>{pass ? "✓" : "○"}</span>
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated()) router.replace("/demo");
  }, [router]);

  const passwordsMatch = confirm.length > 0 && password === confirm;
  const passwordsMismatch = confirm.length > 0 && password !== confirm;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (passwordsMismatch) {
      setError("Passwords do not match.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await register(email, password);
      // Auto-login immediately after registering
      const res = await login(email, password);
      setToken(res.access_token);
      router.push("/demo");
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? "Registration failed. That email may already be in use.");
    } finally {
      setLoading(false);
    }
  }

  const pwToggle = (show: boolean, setShow: (v: boolean) => void) => (
    <button
      type="button"
      onClick={() => setShow(!show)}
      style={{ background: "none", border: "none", cursor: "pointer", color: C.muted, display: "flex", padding: 2 }}
      aria-label={show ? "Hide password" : "Show password"}
    >
      {show ? <EyeOff size={15} /> : <Eye size={15} />}
    </button>
  );

  const confirmHint = confirm.length > 0 ? (
    <span
      style={{
        fontSize: 12,
        color: passwordsMatch ? C.success : C.danger,
        display: "flex",
        alignItems: "center",
        gap: 4,
      }}
    >
      {passwordsMatch ? (
        <><CheckCircle size={12} /> Passwords match</>
      ) : (
        <><AlertCircle size={12} /> Passwords do not match</>
      )}
    </span>
  ) : null;

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
              Create an account
            </h1>
            <p style={{ fontSize: 14, color: C.body, margin: 0 }}>
              Get started with DeepShield in seconds
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
                placeholder="Create a strong password"
                icon={Lock}
                rightSlot={pwToggle(showPw, setShowPw)}
                autoComplete="new-password"
                hint={<PasswordStrength password={password} />}
              />

              <InputField
                label="Confirm password"
                id="confirm"
                type={showConfirm ? "text" : "password"}
                value={confirm}
                onChange={setConfirm}
                placeholder="Re-enter your password"
                icon={Lock}
                rightSlot={pwToggle(showConfirm, setShowConfirm)}
                autoComplete="new-password"
                hint={confirmHint}
              />

              <button
                type="submit"
                disabled={loading || passwordsMismatch}
                style={{
                  width: "100%",
                  background: loading || passwordsMismatch ? C.borderAccent : C.primary,
                  color: "#fff",
                  border: "none",
                  padding: "0.75rem",
                  borderRadius: 8,
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: loading || passwordsMismatch ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 8,
                  transition: "background 0.15s",
                  marginTop: 4,
                }}
                onMouseOver={(e) => {
                  if (!loading && !passwordsMismatch) e.currentTarget.style.background = C.primaryDark;
                }}
                onMouseOut={(e) => {
                  if (!loading && !passwordsMismatch) e.currentTarget.style.background = C.primary;
                }}
              >
                {loading && <Loader2 size={15} className="animate-spin" />}
                {loading ? "Creating account…" : "Create account →"}
              </button>
            </form>

            {/* Compliance note */}
            <p style={{ fontSize: 11, color: C.muted, textAlign: "center", marginTop: "1.25rem", lineHeight: 1.5 }}>
              By creating an account you agree to DeepShield&apos;s terms. No biometric
              data is stored — compliant with DPDP Act &amp; RBI guidelines.
            </p>
          </div>

          {/* Footer link */}
          <p style={{ textAlign: "center", fontSize: 13, color: C.body, marginTop: "1.25rem" }}>
            Already have an account?{" "}
            <Link
              href="/login"
              style={{ color: C.primary, fontWeight: 500, textDecoration: "none" }}
              onMouseOver={(e) => (e.currentTarget.style.textDecoration = "underline")}
              onMouseOut={(e) => (e.currentTarget.style.textDecoration = "none")}
            >
              Sign in →
            </Link>
          </p>
        </div>
      </div>

      <Footer />
    </div>
  );
}
