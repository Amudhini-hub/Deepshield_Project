// Exact shapes returned by the FastAPI backend endpoints

export interface DeepfakeResponse {
  user_id: number;
  is_deepfake: boolean;
  confidence: number;        // 0–1, confidence in the verdict (not the fake-probability)
  detection_method: string;
  frame_count: number;
  details: Record<string, unknown>;
  anomalies: string[];
  timestamp: string;
  heatmap_frame: string | null;        // base64 JPEG of the Grad-CAM overlay
  heatmap_frame_index: number | null;  // index of the most suspicious frame
}

export interface LivenessResponse {
  user_id: number;
  is_alive: boolean;
  confidence: number;        // 0–1
  challenge_type: string;
  frame_count: number;
  details: Record<string, unknown>;
  timestamp: string;
}

// Combined result passed to the UI after both API calls complete
export interface DetectionResult {
  deepfake: DeepfakeResponse;
  liveness: LivenessResponse;
  capturedAt: string;        // ISO timestamp of when the capture was taken
}

// Derived helpers used across display components

/** Returns the fake-probability percentage (0–100). confidence from backend IS always the fake score. */
export function fakePct(r: DeepfakeResponse): number {
  return r.confidence * 100;
}

/** Returns authenticity score (0–100): 100 = definitely real, 0 = definitely fake. */
export function authenticityPct(r: DeepfakeResponse): number {
  return (1 - r.confidence) * 100;
}

/** Returns "ALLOW" | "CHALLENGE" | "BLOCK" based on detection results. */
export function riskDecision(r: DetectionResult): "ALLOW" | "CHALLENGE" | "BLOCK" {
  if (r.deepfake.is_deepfake) return "BLOCK";
  if (!r.liveness.is_alive) return "CHALLENGE";
  if (r.liveness.confidence < 0.25) return "CHALLENGE";
  return "ALLOW";
}
