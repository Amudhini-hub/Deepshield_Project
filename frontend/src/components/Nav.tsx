"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { Shield, Menu, X, LogOut, UserCircle } from "lucide-react";
import { isAuthenticated, clearToken } from "@/lib/auth";

const C = {
  primary: "#4f46e5",
  primaryDark: "#4338ca",
  primaryLight: "#eef2ff",
  borderAccent: "#c7d2fe",
  heading: "#1e1b4b",
  body: "#6b7280",
  border: "#e0e7ff",
};

const NAV_LINKS = [
  { href: "/#how", label: "How it works" },
  { href: "/#features", label: "Features" },
  { href: "/integration", label: "Integration" },
  { href: "/dashboard", label: "Dashboard" },
];

export default function Nav() {
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [authed, setAuthed] = useState(false);

  // Read localStorage only on the client to avoid SSR mismatch
  useEffect(() => {
    setAuthed(isAuthenticated());
  }, [pathname]); // re-check when route changes (after login/logout)

  function handleLogout() {
    clearToken();
    setAuthed(false);
    setOpen(false);
    router.push("/");
  }

  return (
    <nav
      className="sticky top-0 z-50"
      style={{ background: "#fff", borderBottom: "0.5px solid #e0e7ff" }}
    >
      <div className="flex justify-between items-center px-6 md:px-12 py-4">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2.5 text-lg font-semibold no-underline"
          style={{ color: C.heading }}
        >
          <div
            className="w-[34px] h-[34px] rounded-lg flex items-center justify-center text-white flex-shrink-0"
            style={{ background: C.primary }}
          >
            <Shield size={17} />
          </div>
          DeepShield
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex gap-8 items-center">
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className="text-sm transition-colors"
              style={{ color: C.body }}
              onMouseOver={(e) => (e.currentTarget.style.color = C.primary)}
              onMouseOut={(e) => (e.currentTarget.style.color = C.body)}
            >
              {label}
            </Link>
          ))}

          {authed ? (
            /* Authenticated: avatar chip + logout */
            <div style={{ display: "flex", alignItems: "center", gap: "0.625rem" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  background: C.primaryLight,
                  border: `1px solid ${C.borderAccent}`,
                  borderRadius: 20,
                  padding: "3px 10px 3px 6px",
                  fontSize: 12,
                  color: C.primary,
                  fontWeight: 500,
                }}
              >
                <UserCircle size={14} />
                Signed in
              </div>
              <button
                onClick={handleLogout}
                title="Sign out"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 5,
                  background: "none",
                  border: `1px solid ${C.border}`,
                  borderRadius: 8,
                  padding: "5px 10px",
                  fontSize: 13,
                  color: C.body,
                  cursor: "pointer",
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.borderColor = C.primary;
                  e.currentTarget.style.color = C.primary;
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.borderColor = C.border;
                  e.currentTarget.style.color = C.body;
                }}
              >
                <LogOut size={13} />
                Sign out
              </button>
            </div>
          ) : (
            /* Not authenticated: Log in + Sign up */
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Link href="/login">
                <button
                  style={{
                    background: "none",
                    border: `1px solid ${C.border}`,
                    borderRadius: 8,
                    padding: "5px 14px",
                    fontSize: 13,
                    fontWeight: 500,
                    color: C.body,
                    cursor: "pointer",
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.borderColor = C.primary;
                    e.currentTarget.style.color = C.primary;
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.borderColor = C.border;
                    e.currentTarget.style.color = C.body;
                  }}
                >
                  Log in
                </button>
              </Link>
              <Link href="/register">
                <button
                  className="text-white border-0 px-4 py-2 rounded-lg text-sm cursor-pointer font-medium"
                  style={{ background: C.primary, minHeight: 34, fontSize: 13 }}
                  onMouseOver={(e) => (e.currentTarget.style.background = C.primaryDark)}
                  onMouseOut={(e) => (e.currentTarget.style.background = C.primary)}
                >
                  Sign up →
                </button>
              </Link>
            </div>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden"
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
          style={{ background: "none", border: "none", cursor: "pointer", color: C.heading, padding: 4 }}
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile dropdown */}
      {open && (
        <div
          className="md:hidden"
          style={{
            borderTop: "0.5px solid #e0e7ff",
            padding: "1rem 1.5rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.875rem",
            background: "#fff",
          }}
        >
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              style={{ fontSize: 15, color: C.heading, textDecoration: "none", fontWeight: 500 }}
            >
              {label}
            </Link>
          ))}

          {/* Mobile divider */}
          <div style={{ height: "0.5px", background: C.border }} />

          {authed ? (
            <button
              onClick={handleLogout}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 7,
                background: "none",
                border: `1px solid ${C.border}`,
                borderRadius: 8,
                padding: "0.625rem 1rem",
                fontSize: 14,
                fontWeight: 500,
                color: C.body,
                cursor: "pointer",
                width: "100%",
              }}
            >
              <LogOut size={15} />
              Sign out
            </button>
          ) : (
            <>
              <Link href="/login" onClick={() => setOpen(false)}>
                <button
                  style={{
                    background: "none",
                    border: `1px solid ${C.border}`,
                    borderRadius: 8,
                    padding: "0.625rem 1.25rem",
                    fontSize: 14,
                    fontWeight: 500,
                    color: C.heading,
                    cursor: "pointer",
                    width: "100%",
                  }}
                >
                  Log in
                </button>
              </Link>
              <Link href="/register" onClick={() => setOpen(false)}>
                <button
                  style={{
                    background: C.primary,
                    color: "#fff",
                    border: "none",
                    padding: "0.625rem 1.25rem",
                    borderRadius: 8,
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: "pointer",
                    width: "100%",
                  }}
                >
                  Sign up →
                </button>
              </Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
