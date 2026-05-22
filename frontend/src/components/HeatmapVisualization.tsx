"use client";

import { useState } from "react";
import { Download, ZoomIn, X } from "lucide-react";

interface Props {
  heatmapBase64: string | null;
  isDeepfake: boolean;
  confidence: number;   // 0–1
}

export default function HeatmapVisualization({ heatmapBase64, isDeepfake, confidence }: Props) {
  const [modalOpen, setModalOpen] = useState(false);

  const pct = Math.round(confidence * 100);
  const src = heatmapBase64 ? `data:image/jpeg;base64,${heatmapBase64}` : null;

  // ── Placeholder when heatmap is unavailable ──────────────────────────
  if (!src) {
    return (
      <div
        style={{
          border: "1px dashed #e0e7ff",
          borderRadius: 12,
          padding: "1.5rem",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
          minHeight: 120,
          background: "#fafbff",
        }}
      >
        <div style={{ fontSize: 13, color: "#9ca3af" }}>Visualization unavailable</div>
        <div style={{ fontSize: 11, color: "#c4c9d4" }}>
          Heatmap is generated when Celery worker is running
        </div>
      </div>
    );
  }

  // ── Heatmap card ─────────────────────────────────────────────────────
  return (
    <>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem" }}>

        {/* Image with overlaid badges */}
        <div
          onClick={() => setModalOpen(true)}
          style={{
            position: "relative",
            borderRadius: 12,
            overflow: "hidden",
            boxShadow: "0 2px 12px rgba(0,0,0,0.10)",
            cursor: "zoom-in",
            lineHeight: 0,
          }}
        >
          <img
            src={src}
            alt="Grad-CAM manipulation heatmap"
            style={{ width: "100%", display: "block" }}
          />

          {/* Top-left verdict badge */}
          <div
            style={{
              position: "absolute",
              top: 10,
              left: 10,
              background: isDeepfake ? "#dc2626" : "#16a34a",
              color: "#fff",
              fontSize: 10,
              fontWeight: 700,
              padding: "3px 10px",
              borderRadius: 20,
              letterSpacing: 0.6,
            }}
          >
            {isDeepfake ? "MANIPULATION DETECTED" : "AUTHENTIC"}
          </div>

          {/* Bottom-right confidence */}
          <div
            style={{
              position: "absolute",
              bottom: 10,
              right: 10,
              background: "rgba(0,0,0,0.58)",
              backdropFilter: "blur(4px)",
              color: "#fff",
              fontSize: 12,
              fontWeight: 700,
              padding: "3px 10px",
              borderRadius: 8,
            }}
          >
            {pct}% confidence
          </div>

          {/* Zoom icon hint */}
          <div
            style={{
              position: "absolute",
              top: 10,
              right: 10,
              background: "rgba(0,0,0,0.42)",
              borderRadius: 7,
              padding: 5,
              display: "flex",
              alignItems: "center",
            }}
          >
            <ZoomIn size={13} color="#fff" />
          </div>
        </div>

        {/* Caption + download row */}
        <div style={{ display: "flex", alignItems: "flex-start", gap: "0.75rem" }}>
          <p style={{ flex: 1, fontSize: 11, color: "#9ca3af", lineHeight: 1.65, margin: 0 }}>
            Highlighted regions show where the AI detected manipulation artifacts.{" "}
            <span style={{ color: "#ef4444", fontWeight: 500 }}>Red/orange</span> = high
            suspicion, <span style={{ color: "#3b82f6", fontWeight: 500 }}>blue/green</span>{" "}
            = authentic.
          </p>
          <a
            href={src}
            download="deepshield_analysis.jpg"
            onClick={(e) => e.stopPropagation()}
            style={{
              flexShrink: 0,
              display: "flex",
              alignItems: "center",
              gap: 5,
              fontSize: 11,
              color: "#4f46e5",
              fontWeight: 600,
              textDecoration: "none",
              padding: "4px 9px",
              border: "1px solid #e0e7ff",
              borderRadius: 6,
              background: "#f8faff",
              whiteSpace: "nowrap",
            }}
          >
            <Download size={11} />
            Download
          </a>
        </div>
      </div>

      {/* ── Full-size modal ──────────────────────────────────────────── */}
      {modalOpen && (
        <div
          onClick={() => setModalOpen(false)}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 1000,
            background: "rgba(0,0,0,0.82)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "1rem",
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{ position: "relative", maxWidth: "90vw", maxHeight: "90vh" }}
          >
            <img
              src={src}
              alt="Grad-CAM full size"
              style={{
                maxWidth: "100%",
                maxHeight: "85vh",
                borderRadius: 10,
                display: "block",
                boxShadow: "0 8px 40px rgba(0,0,0,0.5)",
              }}
            />
            <button
              onClick={() => setModalOpen(false)}
              style={{
                position: "absolute",
                top: -14,
                right: -14,
                background: "#fff",
                border: "none",
                borderRadius: "50%",
                width: 32,
                height: 32,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                boxShadow: "0 2px 10px rgba(0,0,0,0.28)",
              }}
            >
              <X size={15} />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
