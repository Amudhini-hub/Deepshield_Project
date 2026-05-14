"use client";

import { useState } from "react";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import { Copy, Check } from "lucide-react";

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

const card: React.CSSProperties = {
  background: C.card,
  border: `0.5px solid ${C.border}`,
  borderRadius: 12,
  padding: "1.5rem",
};

// ── Code samples ──────────────────────────────────────────────────────

const snippets: Record<string, { label: string; code: string }> = {
  python: {
    label: "Python",
    code: `import requests

API_KEY = "your_api_key"
BASE    = "http://localhost:8000/api/v1"

# 1. Register / Login
session = requests.Session()
token_res = session.post(f"{BASE}/users/login",
    data={"username": "you@bank.com", "password": "secret"})
token = token_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Deepfake detection
with open("clip.mp4", "rb") as f:
    result = session.post(f"{BASE}/deepfake/detect",
        files={"file": f}, headers=headers).json()

# 3. Liveness verification
with open("clip.mp4", "rb") as f:
    liveness = session.post(f"{BASE}/liveness/detect",
        files={"file": f}, headers=headers).json()

# 4. Use the decision
if result["is_deepfake"] or not liveness["is_alive"]:
    block_attempt(user_id)          # Deepfake detected
elif result["confidence"] < 0.7:
    trigger_mfa(user_id)            # Low confidence
else:
    grant_access(user_id)           # Verified real`,
  },
  javascript: {
    label: "JavaScript",
    code: `const BASE = "http://localhost:8000/api/v1";

// 1. Login
const tokenRes = await fetch(\`\${BASE}/users/login\`, {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({ username: "you@bank.com", password: "secret" }),
});
const { access_token } = await tokenRes.json();

// 2. Deepfake detection
const formData = new FormData();
formData.append("file", videoBlob, "clip.webm");

const result = await fetch(\`\${BASE}/deepfake/detect\`, {
  method: "POST",
  headers: { Authorization: \`Bearer \${access_token}\` },
  body: formData,
}).then(r => r.json());

// 3. Liveness
const liveness = await fetch(\`\${BASE}/liveness/detect\`, {
  method: "POST",
  headers: { Authorization: \`Bearer \${access_token}\` },
  body: formData,
}).then(r => r.json());

// 4. Decision
if (result.is_deepfake || !liveness.is_alive) {
  blockAttempt(userId);
} else if (result.confidence < 0.7) {
  triggerMFA(userId);
} else {
  grantAccess(userId);
}`,
  },
  curl: {
    label: "cURL",
    code: `# 1. Login — get JWT token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/users/login \\
  -d "username=you@bank.com&password=secret" \\
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Deepfake detection
curl -X POST http://localhost:8000/api/v1/deepfake/detect \\
  -H "Authorization: Bearer $TOKEN" \\
  -F "file=@/path/to/clip.mp4"

# 3. Liveness verification
curl -X POST http://localhost:8000/api/v1/liveness/detect \\
  -H "Authorization: Bearer $TOKEN" \\
  -F "file=@/path/to/clip.mp4"

# 4. Health check (no auth required)
curl http://localhost:8000/api/v1/health`,
  },
};

// ── Endpoint reference ────────────────────────────────────────────────

const endpoints = [
  { method: "POST", path: "/users/register", auth: false, desc: "Register a new user account" },
  { method: "POST", path: "/users/login", auth: false, desc: "Authenticate and receive JWT tokens" },
  { method: "POST", path: "/users/refresh", auth: false, desc: "Refresh an expired access token" },
  { method: "POST", path: "/users/logout", auth: true, desc: "Invalidate the current token" },
  { method: "GET",  path: "/users/me", auth: true, desc: "Get authenticated user profile" },
  { method: "POST", path: "/deepfake/detect", auth: true, desc: "Run deepfake detection on uploaded video (mp4, webm, avi, mov)" },
  { method: "POST", path: "/liveness/detect", auth: true, desc: "Run liveness verification on uploaded video" },
  { method: "POST", path: "/analyze", auth: true, desc: "Analyse behavioural biometrics against baseline" },
  { method: "POST", path: "/baseline", auth: true, desc: "Create a behavioural baseline for a user" },
  { method: "POST", path: "/risk", auth: true, desc: "Compute composite risk score" },
  { method: "GET",  path: "/health", auth: false, desc: "API health check" },
  { method: "GET",  path: "/health/status", auth: false, desc: "Detailed component health status" },
];

const methodColor = (m: string) => {
  if (m === "GET") return { bg: "#f0fdf4", color: C.success };
  if (m === "POST") return { bg: C.primaryLight, color: C.primaryDark };
  return { bg: "#fef3c7", color: C.amber };
};

// ── Component ─────────────────────────────────────────────────────────

function CodeBlock({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div style={{ position: "relative" }}>
      <pre
        style={{
          background: C.heading,
          borderRadius: 12,
          padding: "1.5rem 2rem",
          fontFamily: "'Fira Code', 'Courier New', monospace",
          fontSize: 13,
          lineHeight: 1.8,
          overflowX: "auto",
          color: "#e2e8f0",
          margin: 0,
        }}
      >
        <code>{code}</code>
      </pre>
      <button
        onClick={copy}
        style={{
          position: "absolute",
          top: 12,
          right: 12,
          background: "rgba(255,255,255,0.1)",
          border: "1px solid rgba(255,255,255,0.2)",
          borderRadius: 6,
          padding: "4px 10px",
          color: "#e2e8f0",
          fontSize: 12,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: 4,
        }}
      >
        {copied ? <Check size={13} /> : <Copy size={13} />}
        {copied ? "Copied!" : "Copy"}
      </button>
    </div>
  );
}

export default function IntegrationPage() {
  const [activeTab, setActiveTab] = useState<keyof typeof snippets>("python");

  return (
    <div style={{ background: C.pageBg, color: C.heading, minHeight: "100vh" }}>
      <Nav />

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "3rem" }}>
        {/* Header */}
        <div style={{ marginBottom: "3rem" }}>
          <div style={{ fontSize: 12, color: C.primary, fontWeight: 600, letterSpacing: 1, textTransform: "uppercase", marginBottom: 8 }}>
            Integration guide
          </div>
          <h1 style={{ fontSize: 36, fontWeight: 700, color: C.heading, marginBottom: 10 }}>
            Banks integrate in 5 lines of code
          </h1>
          <p style={{ fontSize: 16, color: C.body, maxWidth: 600, lineHeight: 1.7 }}>
            DeepShield is API-first. No SDK required. Call our REST endpoints
            from any language and get a structured fraud decision in under 800ms.
          </p>
        </div>

        {/* Quick-start badges */}
        <div
          style={{
            background: C.card,
            border: `0.5px solid ${C.border}`,
            borderRadius: 12,
            padding: "1.25rem 1.5rem",
            display: "flex",
            gap: "1.5rem",
            flexWrap: "wrap",
            alignItems: "center",
            marginBottom: "2rem",
          }}
        >
          <div style={{ fontSize: 13, fontWeight: 600, color: C.heading }}>Quick facts</div>
          {[
            { label: "Base URL", value: "http://localhost:8000/api/v1" },
            { label: "Auth", value: "Bearer JWT" },
            { label: "Max video size", value: "50 MB" },
            { label: "Formats", value: "mp4, webm, avi, mov, mkv" },
          ].map(({ label, value }) => (
            <div key={label} style={{ fontSize: 13, color: C.body }}>
              <span style={{ color: C.muted }}>{label}: </span>
              <code
                style={{
                  background: C.primaryLight,
                  color: C.primaryDark,
                  padding: "2px 7px",
                  borderRadius: 4,
                  fontSize: 12,
                  fontFamily: "monospace",
                }}
              >
                {value}
              </code>
            </div>
          ))}
        </div>

        {/* Code samples */}
        <div style={{ marginBottom: "2rem" }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: C.heading, marginBottom: "1.25rem" }}>
            Code samples
          </div>

          {/* Tabs */}
          <div
            style={{
              display: "flex",
              gap: "0.25rem",
              marginBottom: "1rem",
              background: C.card,
              border: `0.5px solid ${C.border}`,
              borderRadius: 10,
              padding: 4,
              width: "fit-content",
            }}
          >
            {(Object.keys(snippets) as Array<keyof typeof snippets>).map((key) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                style={{
                  padding: "6px 16px",
                  borderRadius: 7,
                  border: "none",
                  fontSize: 13,
                  fontWeight: 500,
                  cursor: "pointer",
                  background: activeTab === key ? C.primary : "transparent",
                  color: activeTab === key ? "#fff" : C.body,
                  transition: "all 0.15s",
                }}
              >
                {snippets[key].label}
              </button>
            ))}
          </div>

          <CodeBlock code={snippets[activeTab].code} />
        </div>

        {/* Auth flow */}
        <div style={{ ...card, marginBottom: "2rem" }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: C.heading, marginBottom: "1rem" }}>
            Authentication
          </div>
          <p style={{ fontSize: 14, color: C.body, lineHeight: 1.7, marginBottom: "1.25rem" }}>
            DeepShield uses JWT Bearer tokens. Login to receive an{" "}
            <code style={{ background: C.primaryLight, color: C.primaryDark, padding: "1px 6px", borderRadius: 4, fontSize: 12 }}>
              access_token
            </code>{" "}
            (short-lived) and a{" "}
            <code style={{ background: C.primaryLight, color: C.primaryDark, padding: "1px 6px", borderRadius: 4, fontSize: 12 }}>
              refresh_token
            </code>{" "}
            (long-lived). Pass the access token in every request header.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem" }}>
            {[
              { step: "1", title: "Login", body: "POST /users/login with form-encoded username + password. Receive access_token and refresh_token." },
              { step: "2", title: "Authenticate", body: "Include Authorization: Bearer <access_token> in every protected request header." },
              { step: "3", title: "Refresh", body: "When access_token expires, POST /users/refresh with refresh_token to get a new pair." },
            ].map((s) => (
              <div
                key={s.step}
                style={{
                  background: C.pageBg,
                  border: `0.5px solid ${C.border}`,
                  borderRadius: 8,
                  padding: "1rem",
                }}
              >
                <div
                  style={{
                    width: 28,
                    height: 28,
                    background: C.primaryLight,
                    borderRadius: 7,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: C.primary,
                    fontSize: 12,
                    fontWeight: 700,
                    marginBottom: 8,
                  }}
                >
                  {s.step}
                </div>
                <div style={{ fontSize: 13, fontWeight: 600, color: C.heading, marginBottom: 4 }}>{s.title}</div>
                <div style={{ fontSize: 12, color: C.body, lineHeight: 1.5 }}>{s.body}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Response schema */}
        <div style={{ ...card, marginBottom: "2rem" }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: C.heading, marginBottom: "1rem" }}>
            Response schemas
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem" }}>
            {[
              {
                title: "Deepfake detection",
                path: "POST /deepfake/detect",
                fields: [
                  { f: "is_deepfake", t: "boolean", d: "True if deepfake detected" },
                  { f: "confidence", t: "float 0–1", d: "Model confidence" },
                  { f: "detection_method", t: "string", d: "Which model triggered" },
                  { f: "frame_count", t: "int", d: "Frames analysed" },
                  { f: "anomalies", t: "string[]", d: "List of detected artifacts" },
                  { f: "timestamp", t: "ISO 8601", d: "Processing time" },
                ],
              },
              {
                title: "Liveness verification",
                path: "POST /liveness/detect",
                fields: [
                  { f: "is_alive", t: "boolean", d: "True if real live person" },
                  { f: "confidence", t: "float 0–1", d: "Liveness confidence" },
                  { f: "challenge_type", t: "string", d: "passive | active" },
                  { f: "frame_count", t: "int", d: "Frames analysed" },
                  { f: "details", t: "object", d: "Signal breakdown" },
                  { f: "timestamp", t: "ISO 8601", d: "Processing time" },
                ],
              },
            ].map((schema) => (
              <div key={schema.title}>
                <div style={{ fontSize: 14, fontWeight: 600, color: C.heading, marginBottom: 6 }}>
                  {schema.title}
                </div>
                <div style={{ fontSize: 12, color: C.muted, marginBottom: 10, fontFamily: "monospace" }}>
                  {schema.path}
                </div>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                  <thead>
                    <tr>
                      {["Field", "Type", "Description"].map((h) => (
                        <th
                          key={h}
                          style={{
                            textAlign: "left",
                            color: C.muted,
                            fontWeight: 600,
                            paddingBottom: 8,
                            borderBottom: `0.5px solid ${C.border}`,
                            textTransform: "uppercase",
                            letterSpacing: 0.5,
                            fontSize: 10,
                          }}
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {schema.fields.map((row) => (
                      <tr key={row.f}>
                        <td style={{ padding: "8px 0", fontFamily: "monospace", color: C.primary, borderBottom: `0.5px solid ${C.border}` }}>
                          {row.f}
                        </td>
                        <td style={{ padding: "8px 8px", color: C.amber, borderBottom: `0.5px solid ${C.border}` }}>
                          {row.t}
                        </td>
                        <td style={{ padding: "8px 0", color: C.body, borderBottom: `0.5px solid ${C.border}` }}>
                          {row.d}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        </div>

        {/* Endpoint reference */}
        <div style={card}>
          <div style={{ fontSize: 18, fontWeight: 700, color: C.heading, marginBottom: "1rem" }}>
            Endpoint reference
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {["Method", "Endpoint", "Auth", "Description"].map((h) => (
                  <th
                    key={h}
                    style={{
                      textAlign: "left",
                      fontSize: 10,
                      fontWeight: 600,
                      color: C.muted,
                      textTransform: "uppercase",
                      letterSpacing: 1,
                      paddingBottom: 10,
                      borderBottom: `0.5px solid ${C.border}`,
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {endpoints.map((ep, i) => {
                const mc = methodColor(ep.method);
                return (
                  <tr key={ep.path} style={{ borderBottom: i < endpoints.length - 1 ? `0.5px solid ${C.border}` : "none" }}>
                    <td style={{ padding: "10px 0" }}>
                      <span
                        style={{
                          fontSize: 10,
                          fontWeight: 700,
                          padding: "2px 8px",
                          borderRadius: 4,
                          background: mc.bg,
                          color: mc.color,
                        }}
                      >
                        {ep.method}
                      </span>
                    </td>
                    <td style={{ padding: "10px 12px", fontFamily: "monospace", fontSize: 13, color: C.heading }}>
                      {ep.path}
                    </td>
                    <td style={{ padding: "10px 12px", fontSize: 12 }}>
                      {ep.auth ? (
                        <span style={{ color: C.primary, fontWeight: 600 }}>Required</span>
                      ) : (
                        <span style={{ color: C.muted }}>None</span>
                      )}
                    </td>
                    <td style={{ padding: "10px 0", fontSize: 13, color: C.body }}>{ep.desc}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <Footer />
    </div>
  );
}
