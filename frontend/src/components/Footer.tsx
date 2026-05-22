import { Shield } from "lucide-react";

export default function Footer() {
  return (
    <footer
      style={{ background: "#002460", borderTop: "3px solid #C8922A" }}
    >
      <div
        className="px-6 md:px-12 py-5"
        style={{ maxWidth: 1100, margin: "0 auto" }}
      >
        <div className="flex justify-between items-center flex-wrap gap-4">
          <div className="flex items-center gap-2.5">
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: 7,
                background: "#C8922A",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Shield size={14} color="#fff" />
            </div>
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#C8922A", lineHeight: 1.1 }}>
                Indian Overseas Bank
              </div>
              <div style={{ fontSize: 10, color: "rgba(255,255,255,0.5)" }}>
                DeepShield · Secure Authentication
              </div>
            </div>
          </div>

          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.5)", textAlign: "center" }}>
            Built by Team Innovate X for IOB Cybernova Hackathon 2026
          </div>

          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)" }}>
            FastAPI · PyTorch · AWS ECS · Redis
          </div>
        </div>
      </div>
    </footer>
  );
}
