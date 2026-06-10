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

/** Returns authenticity score (0–100): 100 = definitely real, 0 = definitely fake.
 *  Uses a sigmoid centred at the detection threshold (0.75) so real faces display
 *  70–95% real and deepfakes display 15–40% real, giving a clear visual split.
 */
export function authenticityPct(r: DeepfakeResponse): number {
  const k = 7.24;       // steepness — calibrated so 63% fake → 70% real display
  const t = 0.75;       // threshold (same as backend DEEPFAKE_DETECTION_THRESHOLD)
  return (1 / (1 + Math.exp(k * (r.confidence - t)))) * 100;
}

/** Returns "ALLOW" | "CHALLENGE" | "BLOCK" based on detection results. */
export function riskDecision(r: DetectionResult): "ALLOW" | "CHALLENGE" | "BLOCK" {
  if (r.deepfake.is_deepfake) return "BLOCK";
  if (!r.liveness.is_alive) return "CHALLENGE";
  if (r.liveness.confidence < 0.25) return "CHALLENGE";
  return "ALLOW";
}
