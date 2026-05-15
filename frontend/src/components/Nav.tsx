"use client";

import { useState } from "react";
import Link from "next/link";
import { Shield, Menu, X } from "lucide-react";

const links = [
  { href: "/#how", label: "How it works" },
  { href: "/#features", label: "Features" },
  { href: "/integration", label: "Integration" },
  { href: "/dashboard", label: "Dashboard" },
];

export default function Nav() {
  const [open, setOpen] = useState(false);

  return (
    <nav
      className="sticky top-0 z-50"
      style={{ background: "#fff", borderBottom: "0.5px solid #e0e7ff" }}
    >
      <div className="flex justify-between items-center px-6 md:px-12 py-4">
        <Link
          href="/"
          className="flex items-center gap-2.5 text-lg font-semibold no-underline"
          style={{ color: "#1e1b4b" }}
        >
          <div
            className="w-[34px] h-[34px] rounded-lg flex items-center justify-center text-white flex-shrink-0"
            style={{ background: "#4f46e5" }}
          >
            <Shield size={17} />
          </div>
          DeepShield
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex gap-8 items-center">
          {links.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className="text-sm transition-colors"
              style={{ color: "#6b7280" }}
              onMouseOver={(e) => (e.currentTarget.style.color = "#4f46e5")}
              onMouseOut={(e) => (e.currentTarget.style.color = "#6b7280")}
            >
              {label}
            </Link>
          ))}
          <Link href="/demo">
            <button
              className="text-white border-0 px-5 py-2 rounded-lg text-sm cursor-pointer font-medium"
              style={{ background: "#4f46e5" }}
              onMouseOver={(e) => (e.currentTarget.style.background = "#4338ca")}
              onMouseOut={(e) => (e.currentTarget.style.background = "#4f46e5")}
            >
              Live demo →
            </button>
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden"
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
          style={{ background: "none", border: "none", cursor: "pointer", color: "#1e1b4b", padding: 4 }}
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
          {links.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              style={{ fontSize: 15, color: "#1e1b4b", textDecoration: "none", fontWeight: 500 }}
            >
              {label}
            </Link>
          ))}
          <Link href="/demo" onClick={() => setOpen(false)}>
            <button
              style={{
                background: "#4f46e5",
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
              Live demo →
            </button>
          </Link>
        </div>
      )}
    </nav>
  );
}
