// Deepshield API Types and Interfaces

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface BehavioralEvent {
  type: string;
  timestamp: number;
  x?: number;
  y?: number;
  is_error?: boolean;
  metadata?: Record<string, string>;
}

export interface BehavioralProfile {
  user_id: string;
  typing_speed: number;
  typing_rhythm: number;
  error_rate: number;
  mouse_velocity: number;
  mouse_acceleration: number;
  click_interval: number;
  interaction_pattern: Record<string, unknown>;
  created_at: string;
  confidence: number;
}

export interface BehavioralAnalysisResult {
  user_id: string;
  is_legitimate: boolean;
  confidence: number;
  typing_score: number;
  mouse_score: number;
  interaction_score: number;
  anomaly_flags: string[];
  risk_level: string;
  timestamp: string;
}

export interface RiskContext {
  device?: Record<string, unknown>;
  location?: Record<string, unknown>;
  attempt_history?: Record<string, unknown>;
}

export interface RiskAssessmentResult {
  risk_score: number;
  risk_level: string;
  confidence: number;
  factors: Record<string, number>;
  additional_verification_needed: boolean;
  recommended_action: string;
  timestamp: string;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
}
