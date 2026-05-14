"use client";

import Link from "next/link";
import { Shield } from "lucide-react";

export default function Nav() {
  return (
    <nav
      className="flex justify-between items-center px-12 py-4 sticky top-0 z-50"
      style={{ background: "#fff", borderBottom: "0.5px solid #e0e7ff" }}
    >
      <Link
        href="/"
        className="flex items-center gap-2.5 text-lg font-semibold no-underline"
        style={{ color: "#1e1b4b" }}
      >
        <div
          className="w-[34px] h-[34px] rounded-lg flex items-center justify-center text-white"
          style={{ background: "#4f46e5" }}
        >
          <Shield size={17} />
        </div>
        DeepShield
      </Link>

      <div className="flex gap-8 items-center">
        <Link
          href="/#how"
          className="text-sm transition-colors"
          style={{ color: "#6b7280" }}
          onMouseOver={(e) => (e.currentTarget.style.color = "#4f46e5")}
          onMouseOut={(e) => (e.currentTarget.style.color = "#6b7280")}
        >
          How it works
        </Link>
        <Link
          href="/#features"
          className="text-sm transition-colors"
          style={{ color: "#6b7280" }}
          onMouseOver={(e) => (e.currentTarget.style.color = "#4f46e5")}
          onMouseOut={(e) => (e.currentTarget.style.color = "#6b7280")}
        >
          Features
        </Link>
        <Link
          href="/integration"
          className="text-sm transition-colors"
          style={{ color: "#6b7280" }}
          onMouseOver={(e) => (e.currentTarget.style.color = "#4f46e5")}
          onMouseOut={(e) => (e.currentTarget.style.color = "#6b7280")}
        >
          Integration
        </Link>
        <Link
          href="/dashboard"
          className="text-sm transition-colors"
          style={{ color: "#6b7280" }}
          onMouseOver={(e) => (e.currentTarget.style.color = "#4f46e5")}
          onMouseOut={(e) => (e.currentTarget.style.color = "#6b7280")}
        >
          Dashboard
        </Link>
        <Link href="/demo">
          <button
            className="text-white border-0 px-5 py-2 rounded-lg text-sm cursor-pointer font-medium transition-colors"
            style={{ background: "#4f46e5" }}
            onMouseOver={(e) =>
              (e.currentTarget.style.background = "#4338ca")
            }
            onMouseOut={(e) =>
              (e.currentTarget.style.background = "#4f46e5")
            }
          >
            Live demo →
          </button>
        </Link>
      </div>
    </nav>
  );
}
