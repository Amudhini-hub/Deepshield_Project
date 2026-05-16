"use client";

import { useState } from "react";
import { useBehavioralContext } from "@/components/BehavioralProvider";

export default function BiometricStatus() {
  if (process.env.NODE_ENV !== "development") return null;

  return <BiometricStatusInner />;
}

function BiometricStatusInner() {
  const status = useBehavioralContext();
  const [expanded, setExpanded] = useState(false);

  const dotColor = status.isCollecting ? "#22c55e" : "#9ca3af";

  return (
    <div
      style={{
        position: "fixed",
        bottom: 16,
        right: 16,
        zIndex: 9999,
        fontFamily: "monospace",
        fontSize: 11,
      }}
    >
      {expanded && (
        <div
          style={{
            background: "#1e1b4b",
            color: "#e0e7ff",
            borderRadius: 10,
            padding: "0.75rem 1rem",
            marginBottom: 8,
            minWidth: 240,
            boxShadow: "0 4px 24px rgba(0,0,0,0.3)",
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: 8, color: "#a5b4fc" }}>
            Behavioral Engine
          </div>
          <Row label="Collecting" value={status.isCollecting ? "yes" : "no"} />
          <Row label="Events buffered" value={String(status.eventCount)} />
          <Row
            label="Last flush"
            value={status.lastFlush ? status.lastFlush.toLocaleTimeString() : "—"}
          />
          <Row
            label="Session ID"
            value={status.sessionId.slice(0, 8) + "…"}
          />
        </div>
      )}

      <button
        onClick={() => setExpanded((v) => !v)}
        title="Behavioral biometrics engine status"
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          background: "#1e1b4b",
          color: "#e0e7ff",
          border: "none",
          borderRadius: 20,
          padding: "0.375rem 0.75rem",
          cursor: "pointer",
          boxShadow: "0 2px 8px rgba(0,0,0,0.25)",
        }}
      >
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: dotColor,
            display: "inline-block",
            animation: status.isCollecting ? "blink 1.4s ease-in-out infinite" : "none",
          }}
        />
        behavioral
      </button>

      <style>{`
        @keyframes blink {
          0%, 100% { opacity: 1 }
          50%       { opacity: 0.3 }
        }
      `}</style>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 4 }}>
      <span style={{ color: "#9ca3af" }}>{label}</span>
      <span style={{ color: "#f0f0f0" }}>{value}</span>
    </div>
  );
}
