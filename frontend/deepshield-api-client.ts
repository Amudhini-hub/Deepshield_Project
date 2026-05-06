// Deepshield API Client

import {
  User,
  TokenResponse,
  BehavioralEvent,
  BehavioralProfile,
  BehavioralAnalysisResult,
  RiskContext,
  RiskAssessmentResult,
  HealthStatus,
} from "./deepshield-types";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api/v1";

export class DeepshieldAPIClient {
  private token: string | null = null;

  constructor(token?: string) {
    this.token = token || localStorage.getItem("deepshield_token");
  }

  setToken(token: string): void {
    this.token = token;
    localStorage.setItem("deepshield_token", token);
  }

  clearToken(): void {
    this.token = null;
    localStorage.removeItem("deepshield_token");
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: response.statusText,
      }));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json() as Promise<T>;
  }

  // Auth endpoints
  async register(email: string, password: string): Promise<User> {
    return this.request<User>("/users/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async login(email: string, password: string): Promise<TokenResponse> {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const response = await fetch(`${API_BASE_URL}/users/login`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error("Login failed");
    }

    const data = await response.json() as TokenResponse;
    this.setToken(data.access_token);
    return data;
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>("/users/me", {
      method: "GET",
    });
  }

  // Biometric endpoints
  async createBaseline(userId: string, events: BehavioralEvent[]): Promise<BehavioralProfile> {
    return this.request<BehavioralProfile>("/baseline", {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
        events,
      }),
    });
  }

  async analyzeBehavior(userId: string, events: BehavioralEvent[]): Promise<BehavioralAnalysisResult> {
    return this.request<BehavioralAnalysisResult>("/analyze", {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
        events,
      }),
    });
  }

  // Risk assessment endpoint
  async assessRisk(
    userId: string,
    biometricAnalysis: Record<string, unknown>,
    behavioralAnalysis: Record<string, unknown>,
    context: RiskContext
  ): Promise<RiskAssessmentResult> {
    return this.request<RiskAssessmentResult>("/risk", {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
        biometric_analysis: biometricAnalysis,
        behavioral_analysis: behavioralAnalysis,
        context,
      }),
    });
  }

  // Health check
  async healthCheck(): Promise<HealthStatus> {
    return this.request<HealthStatus>("/health", {
      method: "GET",
    });
  }
}

// Singleton instance
export const deepshieldAPI = new DeepshieldAPIClient();

// Hook for React component usage
export function useDeepshieldAPI(token?: string): DeepshieldAPIClient {
  return new DeepshieldAPIClient(token);
}
