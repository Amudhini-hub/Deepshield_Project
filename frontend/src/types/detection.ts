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

/** Returns the fake-probability percentage (0–100). */
export function fakePct(r: DeepfakeResponse): number {
  return (r.is_deepfake ? r.confidence : 1 - r.confidence) * 100;
}

/** Returns "ALLOW" | "CHALLENGE" | "BLOCK" based on detection results. */
export function riskDecision(r: DetectionResult): "ALLOW" | "CHALLENGE" | "BLOCK" {
  const fp = fakePct(r.deepfake);
  if (r.deepfake.is_deepfake || !r.liveness.is_alive) return "BLOCK";
  if (fp > 30 || r.liveness.confidence < 0.7) return "CHALLENGE";
  return "ALLOW";
}
