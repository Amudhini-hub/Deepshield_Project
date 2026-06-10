"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { Shield, Menu, X, LogOut, UserCircle } from "lucide-react";
import { isAuthenticated, clearToken } from "@/lib/auth";

const C = {
  blue: "#003580",
  blueLight: "#004aad",
  gold: "#C8922A",
  goldLight: "#FDF3E1",
  white: "#ffffff",
  whiteAlpha: "rgba(255,255,255,0.75)",
  whiteAlpha2: "rgba(255,255,255,0.15)",
};

const NAV_LINKS = [
  { href: "/#how", label: "How it works" },
  { href: "/#features", label: "Features" },
  { href: "/integration", label: "Integration" },
];

export default function Nav() {
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    setAuthed(isAuthenticated());
  }, [pathname]);

  function handleLogout() {
    clearToken();
    setAuthed(false);
    setOpen(false);
    router.push("/");
  }

  return (
    <nav
      className="sticky top-0 z-50"
      style={{
        background: C.blue,
        borderBottom: `3px solid ${C.gold}`,
        boxShadow: "0 2px 12px rgba(0,0,0,0.18)",
      }}
    >
      <div className="flex justify-between items-center px-6 md:px-12 py-3">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-3 no-underline"
          style={{ color: C.white }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              background: C.gold,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <Shield size={18} color="#fff" />
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.gold, lineHeight: 1.1 }}>
              Indian Overseas Bank
            </div>
            <div style={{ fontSize: 10, color: C.whiteAlpha, letterSpacing: 0.5 }}>
              DeepShield · Secure Authentication
            </div>
          </div>
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex gap-7 items-center">
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className="text-sm transition-colors no-underline"
              style={{ color: C.whiteAlpha, fontWeight: 500 }}
              onMouseOver={(e) => (e.currentTarget.style.color = C.gold)}
              onMouseOut={(e) => (e.currentTarget.style.color = C.whiteAlpha)}
            >
              {label}
            </Link>
          ))}

          {authed ? (
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 5,
                  background: C.whiteAlpha2,
                  border: `1px solid ${C.gold}`,
                  borderRadius: 20,
                  padding: "3px 10px 3px 7px",
                  fontSize: 12,
                  color: C.gold,
                  fontWeight: 600,
                }}
              >
                <UserCircle size={13} />
                Authenticated
              </div>
              <button
                onClick={handleLogout}
                title="Sign out"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 5,
                  background: "none",
                  border: `1px solid rgba(255,255,255,0.3)`,
                  borderRadius: 8,
                  padding: "5px 10px",
                  fontSize: 12,
                  color: C.whiteAlpha,
                  cursor: "pointer",
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.borderColor = C.gold;
                  e.currentTarget.style.color = C.gold;
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.3)";
                  e.currentTarget.style.color = C.whiteAlpha;
                }}
              >
                <LogOut size={12} />
                Sign out
              </button>
            </div>
          ) : (
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Link href="/login">
                <button
                  style={{
                    background: "none",
                    border: `1px solid rgba(255,255,255,0.3)`,
                    borderRadius: 8,
                    padding: "5px 14px",
                    fontSize: 13,
                    fontWeight: 500,
                    color: C.whiteAlpha,
                    cursor: "pointer",
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.borderColor = C.gold;
                    e.currentTarget.style.color = C.gold;
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.borderColor = "rgba(255,255,255,0.3)";
                    e.currentTarget.style.color = C.whiteAlpha;
                  }}
                >
                  Customer Login
                </button>
              </Link>
              <Link href="/demo">
                <button
                  style={{
                    background: C.gold,
                    color: "#fff",
                    border: "none",
                    padding: "6px 16px",
                    borderRadius: 8,
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                  onMouseOver={(e) => (e.currentTarget.style.background = "#b07e24")}
                  onMouseOut={(e) => (e.currentTarget.style.background = C.gold)}
                >
                  Try Demo →
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
          style={{ background: "none", border: "none", cursor: "pointer", color: C.white, padding: 4 }}
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile dropdown */}
      {open && (
        <div
          className="md:hidden"
          style={{
            borderTop: `1px solid rgba(255,255,255,0.12)`,
            padding: "1rem 1.5rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.875rem",
            background: "#002460",
          }}
        >
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              style={{ fontSize: 15, color: C.white, textDecoration: "none", fontWeight: 500 }}
            >
              {label}
            </Link>
          ))}

          <div style={{ height: "0.5px", background: "rgba(255,255,255,0.15)" }} />

          {authed ? (
            <button
              onClick={handleLogout}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 7,
                background: "none",
                border: `1px solid rgba(255,255,255,0.3)`,
                borderRadius: 8,
                padding: "0.625rem 1rem",
                fontSize: 14,
                fontWeight: 500,
                color: C.white,
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
                    border: `1px solid rgba(255,255,255,0.3)`,
                    borderRadius: 8,
                    padding: "0.625rem 1.25rem",
                    fontSize: 14,
                    fontWeight: 500,
                    color: C.white,
                    cursor: "pointer",
                    width: "100%",
                  }}
                >
                  Customer Login
                </button>
              </Link>
              <Link href="/demo" onClick={() => setOpen(false)}>
                <button
                  style={{
                    background: C.gold,
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
                  Try Demo →
                </button>
              </Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
