"use client";

import { useRef, useState, useEffect, useCallback } from "react";
import { Camera, CameraOff, Loader2, AlertTriangle, CheckCircle, XCircle, ScanFace } from "lucide-react";
import { detectDeepfake, detectLiveness } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { DetectionResult } from "@/types/detection";

// ── Design tokens ─────────────────────────────────────────────────────
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
  success: "#16a34a",
  danger: "#dc2626",
  amber: "#d97706",
};

// ── Types ─────────────────────────────────────────────────────────────
type CamStatus = "idle" | "requesting" | "active" | "denied" | "unsupported" | "error";
type Phase = "idle" | "ready" | "recording" | "analysing" | "done" | "error";

interface Props {
  onResult: (result: DetectionResult) => void;
}

// ── Face-api.js types (subset we need, loaded dynamically) ────────────
type FaceApiModule = typeof import("face-api.js");

// How long to record before sending (must produce > 5 frames at ≥24 fps)
const RECORD_SECONDS = 3;

// ── Component ─────────────────────────────────────────────────────────
export default function WebcamCapture({ onResult }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);   // face-detection overlay
  const streamRef = useRef<MediaStream | null>(null);
  const faaRef = useRef<FaceApiModule | null>(null);    // face-api.js module
  const loopRef = useRef<number>(0);
  const runLoopRef = useRef(false);                     // ref so the async loop can see it
  const cancelRefs = useRef<{ deepfake: (() => void) | null; liveness: (() => void) | null }>({
    deepfake: null,
    liveness: null,
  });

  const [camStatus, setCamStatus] = useState<CamStatus>("idle");
  const [phase, setPhase] = useState<Phase>("idle");
  const [faceDetected, setFaceDetected] = useState(false);
  const [modelsLoaded, setModelsLoaded] = useState(false);
  const [faaLoadFailed, setFaaLoadFailed] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [errorMsg, setErrorMsg] = useState("");

  // ── Load face-api.js models once ────────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    import("face-api.js")
      .then(async (faa) => {
        if (cancelled) return;
        faaRef.current = faa;
        await Promise.all([
          faa.nets.tinyFaceDetector.loadFromUri("/models"),
          faa.nets.faceLandmark68Net.loadFromUri("/models"),
        ]);
        if (!cancelled) setModelsLoaded(true);
      })
      .catch((err) => {
        console.warn("face-api.js load failed:", err);
        if (!cancelled) setFaaLoadFailed(true);
      });
    return () => { cancelled = true; };
  }, []);

  // ── Cleanup camera and in-flight polls on unmount ───────────────────
  useEffect(() => {
    return () => {
      runLoopRef.current = false;
      cancelAnimationFrame(loopRef.current);
      streamRef.current?.getTracks().forEach((t) => t.stop());
      cancelRefs.current.deepfake?.();
      cancelRefs.current.liveness?.();
    };
  }, []);

  // ── Detection loop (runs while camera is active) ─────────────────────
  const startDetectionLoop = useCallback(() => {
    runLoopRef.current = true;

    const detect = async () => {
      if (!runLoopRef.current) return;

      const video = videoRef.current;
      const canvas = overlayRef.current;
      const faa = faaRef.current;

      if (video && canvas && faa && modelsLoaded && video.readyState >= 2) {
        const { videoWidth: w, videoHeight: h } = video;
        if (canvas.width !== w) canvas.width = w;
        if (canvas.height !== h) canvas.height = h;

        const detections = await faa
          .detectAllFaces(video, new faa.TinyFaceDetectorOptions({ inputSize: 320, scoreThreshold: 0.4 }))
          .withFaceLandmarks();

        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.clearRect(0, 0, w, h);
          const resized = faa.resizeResults(detections, { width: w, height: h });

          // Bounding box — indigo
          resized.forEach(({ detection }) => {
            const { x, y, width, height } = detection.box;
            ctx.strokeStyle = "#4f46e5";
            ctx.lineWidth = 2;
            ctx.strokeRect(x, y, width, height);
          });

          // Landmarks — small teal dots
          resized.forEach(({ landmarks }) => {
            ctx.fillStyle = "#06b6d4";
            landmarks.positions.forEach(({ x, y }) => {
              ctx.beginPath();
              ctx.arc(x, y, 1.5, 0, 2 * Math.PI);
              ctx.fill();
            });
          });

          setFaceDetected(detections.length > 0);
        }
      }

      if (runLoopRef.current) {
        loopRef.current = requestAnimationFrame(detect);
      }
    };

    loopRef.current = requestAnimationFrame(detect);
  }, [modelsLoaded]);

  // Restart loop when models finish loading (camera may already be active)
  useEffect(() => {
    if (modelsLoaded && camStatus === "active") {
      startDetectionLoop();
    }
  }, [modelsLoaded, camStatus, startDetectionLoop]);

  // ── Start camera ─────────────────────────────────────────────────────
  async function startCamera() {
    if (!navigator.mediaDevices?.getUserMedia) {
      setCamStatus("unsupported");
      return;
    }
    setCamStatus("requesting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCamStatus("active");
      setPhase("ready");
      if (modelsLoaded) startDetectionLoop();
    } catch (err) {
      const e = err as DOMException;
      setCamStatus(e.name === "NotAllowedError" ? "denied" : "error");
    }
  }

  // ── Record & analyse ─────────────────────────────────────────────────
  async function handleCapture() {
    const stream = streamRef.current;
    if (!stream || phase === "recording" || phase === "analysing") return;

    setErrorMsg("");
    setPhase("recording");
    setCountdown(RECORD_SECONDS);

    const chunks: Blob[] = [];
    const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9")
      ? "video/webm;codecs=vp9"
      : MediaRecorder.isTypeSupported("video/webm;codecs=vp8")
      ? "video/webm;codecs=vp8"
      : "video/webm";

    const recorder = new MediaRecorder(stream, { mimeType });
    recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };

    recorder.onstop = async () => {
      const blob = new Blob(chunks, { type: "video/webm" });
      setPhase("analysing");

      const token = getToken() ?? "";

      const dfTask = detectDeepfake(blob, token);
      const lvTask = detectLiveness(blob, token);
      cancelRefs.current.deepfake = dfTask.cancel;
      cancelRefs.current.liveness = lvTask.cancel;

      try {
        const [deepfake, liveness] = await Promise.all([dfTask.promise, lvTask.promise]);
        onResult({ deepfake, liveness, capturedAt: new Date().toISOString() });
        setPhase("done");
      } catch (err: unknown) {
        const msg = (err as Error)?.message ?? "";
        if (msg === "Cancelled") return; // component unmounted — drop silently

        const status = (err as { response?: { status?: number } })?.response?.status;
        const detail =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;

        if (status === 401) {
          setErrorMsg("Session expired. Please log in again.");
        } else if (status === 503) {
          setErrorMsg("Detection service unavailable — please try again later.");
        } else {
          setErrorMsg(detail ?? "Analysis failed. Please try again.");
        }
        setPhase("error");
      } finally {
        cancelRefs.current.deepfake = null;
        cancelRefs.current.liveness = null;
      }
    };

    recorder.start(100); // emit data every 100 ms for reliable chunk delivery

    let remaining = RECORD_SECONDS;
    const tick = setInterval(() => {
      remaining -= 1;
      setCountdown(remaining);
      if (remaining <= 0) {
        clearInterval(tick);
        recorder.stop();
      }
    }, 1000);
  }

  function reset() {
    setPhase("ready");
    setErrorMsg("");
    setCountdown(0);
  }

  // ── Helpers ───────────────────────────────────────────────────────────
  // Allow capture before face-api.js finishes loading — models add the overlay
  // but aren't required for backend detection. Gate only when loaded + no face.
  const canCapture =
    camStatus === "active" &&
    (phase === "ready" || phase === "done" || phase === "error") &&
    (faaLoadFailed || !modelsLoaded || faceDetected);

  // ── Render ────────────────────────────────────────────────────────────
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>

      {/* ── Camera viewport ── */}
      <div
        style={{
          position: "relative",
          background: "#0f0f0f",
          borderRadius: 14,
          overflow: "hidden",
          border: `2px solid ${
            phase === "recording"
              ? C.danger
              : camStatus === "active" && faceDetected
              ? "#22c55e"
              : C.border
          }`,
          aspectRatio: "4/3",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {/* Video element (always mounted so the stream can attach) */}
        <video
          ref={videoRef}
          muted
          playsInline
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            display: camStatus === "active" ? "block" : "none",
          }}
        />

        {/* Face-api.js overlay canvas */}
        <canvas
          ref={overlayRef}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            pointerEvents: "none",
            display: camStatus === "active" ? "block" : "none",
          }}
        />

        {/* Placeholder when camera is off */}
        {camStatus !== "active" && (
          <div style={{ textAlign: "center", color: C.muted, padding: "2rem" }}>
            {camStatus === "requesting" ? (
              <Loader2 size={36} color={C.primary} className="animate-spin mx-auto" />
            ) : camStatus === "denied" ? (
              <CameraOff size={36} color={C.danger} style={{ margin: "0 auto 0.75rem" }} />
            ) : (
              <Camera size={36} color={C.muted} style={{ margin: "0 auto 0.75rem" }} />
            )}
            <div style={{ fontSize: 13, marginTop: 8, color: camStatus === "denied" ? C.danger : C.muted }}>
              {camStatus === "requesting"
                ? "Requesting camera…"
                : camStatus === "denied"
                ? "Camera access denied"
                : camStatus === "unsupported"
                ? "Camera not supported in this browser"
                : "Camera off"}
            </div>
          </div>
        )}

        {/* Recording badge */}
        {phase === "recording" && (
          <div
            style={{
              position: "absolute",
              top: 10,
              right: 10,
              background: C.danger,
              color: "#fff",
              borderRadius: 8,
              padding: "4px 12px",
              fontSize: 13,
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: "#fff",
                display: "inline-block",
                animation: "pulse 1s ease-in-out infinite",
              }}
            />
            REC {countdown}s
          </div>
        )}

        {/* Analysing overlay */}
        {phase === "analysing" && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              background: "rgba(15,15,15,0.7)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 12,
            }}
          >
            <Loader2 size={40} color={C.primary} className="animate-spin" />
            <div style={{ color: "#fff", fontSize: 14, fontWeight: 600 }}>
              Analysing…
            </div>
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: 6,
                justifyContent: "center",
                padding: "0 1rem",
              }}
            >
              {["Deepfake detection", "Liveness check", "Frame analysis"].map((s) => (
                <span
                  key={s}
                  style={{
                    background: C.primaryLight,
                    color: C.primary,
                    fontSize: 11,
                    padding: "2px 8px",
                    borderRadius: 20,
                  }}
                >
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Face-detection status badge */}
        {camStatus === "active" && phase !== "analysing" && (
          <div
            style={{
              position: "absolute",
              top: 10,
              left: 10,
              background: "rgba(0,0,0,0.55)",
              backdropFilter: "blur(4px)",
              borderRadius: 20,
              padding: "3px 10px",
              display: "flex",
              alignItems: "center",
              gap: 5,
              fontSize: 11,
              fontWeight: 600,
              color: faceDetected ? "#4ade80" : "#f87171",
            }}
          >
            {modelsLoaded ? (
              faceDetected ? (
                <><CheckCircle size={11} /> Face detected</>
              ) : (
                <><XCircle size={11} /> No face</>
              )
            ) : (
              <><Loader2 size={11} className="animate-spin" /> Loading models…</>
            )}
          </div>
        )}
      </div>

      {/* ── Camera denied — permission instructions ── */}
      {camStatus === "denied" && (
        <div
          style={{
            background: "#fef3c7",
            border: "1px solid #fcd34d",
            borderRadius: 10,
            padding: "0.875rem 1rem",
            display: "flex",
            gap: 10,
          }}
        >
          <AlertTriangle size={16} color={C.amber} style={{ flexShrink: 0, marginTop: 1 }} />
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#92400e", marginBottom: 4 }}>
              Camera permission blocked
            </div>
            <div style={{ fontSize: 12, color: "#78350f", lineHeight: 1.6 }}>
              Click the camera icon in your browser&apos;s address bar → select{" "}
              <strong>Allow</strong>, then reload and try again.
            </div>
          </div>
        </div>
      )}

      {/* ── Error state ── */}
      {phase === "error" && errorMsg && (
        <div
          style={{
            background: "#fee2e2",
            border: "1px solid #fecaca",
            borderRadius: 10,
            padding: "0.75rem 1rem",
            fontSize: 13,
            color: C.danger,
          }}
        >
          {errorMsg}
        </div>
      )}

      {/* ── Action buttons ── */}
      {camStatus === "idle" || camStatus === "denied" || camStatus === "unsupported" ? (
        <button
          onClick={startCamera}
          disabled={camStatus === "unsupported"}
          style={{
            width: "100%",
            background: camStatus === "unsupported" ? C.muted : C.primary,
            color: "#fff",
            border: "none",
            padding: "0.875rem",
            borderRadius: 10,
            fontSize: 15,
            fontWeight: 600,
            cursor: camStatus === "unsupported" ? "not-allowed" : "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            minHeight: 44,
          }}
          onMouseOver={(e) => {
            if (camStatus !== "unsupported") e.currentTarget.style.background = C.primaryDark;
          }}
          onMouseOut={(e) => {
            if (camStatus !== "unsupported") e.currentTarget.style.background = C.primary;
          }}
        >
          <Camera size={16} />
          {camStatus === "denied" ? "Retry camera" : "Start camera"}
        </button>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem" }}>
          <button
            onClick={handleCapture}
            disabled={!canCapture}
            style={{
              width: "100%",
              background: !canCapture ? "#d1d5db" : C.primary,
              color: !canCapture ? "#9ca3af" : "#fff",
              border: "none",
              padding: "0.875rem",
              borderRadius: 10,
              fontSize: 15,
              fontWeight: 600,
              cursor: !canCapture ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              minHeight: 44,
              transition: "background 0.15s",
            }}
            onMouseOver={(e) => {
              if (canCapture) e.currentTarget.style.background = C.primaryDark;
            }}
            onMouseOut={(e) => {
              if (canCapture) e.currentTarget.style.background = C.primary;
            }}
          >
            {phase === "recording" ? (
              <><span style={{ fontSize: 13 }}>●</span> Recording… {countdown}s</>
            ) : phase === "analysing" ? (
              <><Loader2 size={15} className="animate-spin" /> Analysing…</>
            ) : (
              <><ScanFace size={16} /> Capture &amp; Analyse</>
            )}
          </button>

          {/* Hint when face not detected */}
          {camStatus === "active" && !faceDetected && phase !== "recording" && phase !== "analysing" && (
            <p style={{ fontSize: 12, color: C.muted, textAlign: "center", margin: 0 }}>
              Position your face in the frame — detection requires a visible face
            </p>
          )}

          {/* Re-capture after done/error */}
          {(phase === "done" || phase === "error") && (
            <button
              onClick={reset}
              style={{
                background: "none",
                border: `1px solid ${C.border}`,
                borderRadius: 10,
                padding: "0.625rem",
                fontSize: 13,
                color: C.body,
                cursor: "pointer",
                width: "100%",
              }}
            >
              Capture again
            </button>
          )}
        </div>
      )}

      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
      `}</style>
    </div>
  );
}
