// React Hooks for Deepshield API Integration

import { useEffect, useState, useCallback } from "react";
import { DeepshieldAPIClient } from "./deepshield-api-client";
import {
  User,
  BehavioralEvent,
  BehavioralProfile,
  BehavioralAnalysisResult,
  RiskContext,
  RiskAssessmentResult,
} from "./deepshield-types";

interface UseAuthResult {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  register: (email: string, password: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  fetchCurrentUser: () => Promise<void>;
}

export function useAuth(): UseAuthResult {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("deepshield_token")
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const client = new DeepshieldAPIClient(token || undefined);

  const register = useCallback(
    async (email: string, password: string) => {
      setIsLoading(true);
      setError(null);
      try {
        const newUser = await client.register(email, password);
        setUser(newUser);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Registration failed");
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await client.login(email, password);
      setToken(response.access_token);
      const currentUser = await client.getCurrentUser();
      setUser(currentUser);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    client.clearToken();
    setUser(null);
    setToken(null);
  }, []);

  const fetchCurrentUser = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const currentUser = await client.getCurrentUser();
      setUser(currentUser);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch user");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token && !user) {
      fetchCurrentUser();
    }
  }, [token, user, fetchCurrentUser]);

  return {
    user,
    token,
    isLoading,
    error,
    register,
    login,
    logout,
    fetchCurrentUser,
  };
}

interface UseBiometricsResult {
  profile: BehavioralProfile | null;
  analysis: BehavioralAnalysisResult | null;
  riskAssessment: RiskAssessmentResult | null;
  isLoading: boolean;
  error: string | null;
  createBaseline: (userId: string, events: BehavioralEvent[]) => Promise<void>;
  analyzeBehavior: (userId: string, events: BehavioralEvent[]) => Promise<void>;
  assessRisk: (
    userId: string,
    biometricAnalysis: Record<string, unknown>,
    behavioralAnalysis: Record<string, unknown>,
    context: RiskContext
  ) => Promise<void>;
}

export function useBiometrics(token?: string): UseBiometricsResult {
  const [profile, setProfile] = useState<BehavioralProfile | null>(null);
  const [analysis, setAnalysis] = useState<BehavioralAnalysisResult | null>(null);
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessmentResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const client = new DeepshieldAPIClient(token);

  const createBaseline = useCallback(
    async (userId: string, events: BehavioralEvent[]) => {
      setIsLoading(true);
      setError(null);
      try {
        const newProfile = await client.createBaseline(userId, events);
        setProfile(newProfile);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Baseline creation failed");
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const analyzeBehavior = useCallback(
    async (userId: string, events: BehavioralEvent[]) => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await client.analyzeBehavior(userId, events);
        setAnalysis(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Analysis failed");
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const assessRisk = useCallback(
    async (
      userId: string,
      biometricAnalysis: Record<string, unknown>,
      behavioralAnalysis: Record<string, unknown>,
      context: RiskContext
    ) => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await client.assessRisk(
          userId,
          biometricAnalysis,
          behavioralAnalysis,
          context
        );
        setRiskAssessment(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Risk assessment failed");
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  return {
    profile,
    analysis,
    riskAssessment,
    isLoading,
    error,
    createBaseline,
    analyzeBehavior,
    assessRisk,
  };
}
