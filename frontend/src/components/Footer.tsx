import { Shield } from "lucide-react";

export default function Footer() {
  return (
    <footer
      className="px-12 py-6"
      style={{ background: "#fff", borderTop: "0.5px solid #e0e7ff" }}
    >
      <div className="flex justify-between items-center flex-wrap gap-4 max-w-[1100px] mx-auto">
        <div className="flex items-center gap-2 text-base font-semibold" style={{ color: "#1e1b4b" }}>
          <div
            className="w-[26px] h-[26px] rounded-lg flex items-center justify-center text-white"
            style={{ background: "#4f46e5" }}
          >
            <Shield size={13} />
          </div>
          DeepShield
        </div>
        <div className="text-xs" style={{ color: "#9ca3af" }}>
          Built by Team Innovate X for IOB Cybernova Hackathon 2026
        </div>
        <div className="text-xs" style={{ color: "#9ca3af" }}>
          FastAPI · TensorFlow · AWS ECS · Redis
        </div>
      </div>
    </footer>
  );
}
