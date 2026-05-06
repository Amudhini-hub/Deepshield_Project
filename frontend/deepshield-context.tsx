// React Context Provider for Deepshield API

import React, {
  createContext,
  useContext,
  ReactNode,
  useState,
  useCallback,
  useEffect,
} from "react";
import { DeepshieldAPIClient } from "./deepshield-api-client";
import { User } from "./deepshield-types";

interface DeepshieldContextType {
  client: DeepshieldAPIClient;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (email: string, password: string) => Promise<void>;
}

const DeepshieldContext = createContext<DeepshieldContextType | undefined>(
  undefined
);

interface DeepshieldProviderProps {
  children: ReactNode;
}

export function DeepshieldProvider({ children }: DeepshieldProviderProps) {
  const [client] = useState(() => new DeepshieldAPIClient());
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await client.login(email, password);
      const currentUser = await client.getCurrentUser();
      setUser(currentUser);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Login failed";
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [client]);

  const logout = useCallback(() => {
    client.clearToken();
    setUser(null);
    setError(null);
  }, [client]);

  const register = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const newUser = await client.register(email, password);
      setUser(newUser);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Registration failed";
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [client]);

  // Restore session on mount
  useEffect(() => {
    const initializeSession = async () => {
      const token = localStorage.getItem("deepshield_token");
      if (token) {
        setIsLoading(true);
        try {
          const currentUser = await client.getCurrentUser();
          setUser(currentUser);
        } catch (err) {
          client.clearToken();
        } finally {
          setIsLoading(false);
        }
      }
    };

    initializeSession();
  }, [client]);

  const value: DeepshieldContextType = {
    client,
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    logout,
    register,
  };

  return (
    <DeepshieldContext.Provider value={value}>
      {children}
    </DeepshieldContext.Provider>
  );
}

export function useDeepshield(): DeepshieldContextType {
  const context = useContext(DeepshieldContext);
  if (!context) {
    throw new Error("useDeepshield must be used within DeepshieldProvider");
  }
  return context;
}
