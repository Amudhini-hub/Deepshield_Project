# Deepshield Frontend Integration Guide

## Overview

This guide provides everything you need to integrate Deepshield biometric authentication into your React frontend.

## Installation

1. Copy the following files to your project:
   - `deepshield-types.ts` - TypeScript type definitions
   - `deepshield-api-client.ts` - API client class
   - `deepshield-hooks.ts` - React hooks
   - `deepshield-context.tsx` - React Context provider

2. Set the API URL in your `.env` file:
   ```
   REACT_APP_API_URL=http://localhost:5000/api/v1
   ```

## Basic Setup

### 1. Wrap Your App with DeepshieldProvider

```tsx
import { DeepshieldProvider } from "./deepshield-context";

function App() {
  return (
    <DeepshieldProvider>
      <YourAppContent />
    </DeepshieldProvider>
  );
}
```

### 2. Authentication

Use the `useAuth` hook in your components:

```tsx
import { useAuth } from "./deepshield-hooks";

function LoginPage() {
  const { login, isLoading, error } = useAuth();

  const handleLogin = async (email: string, password: string) => {
    try {
      await login(email, password);
      // Navigate to dashboard on successful login
    } catch (err) {
      console.error("Login failed:", err);
    }
  };

  return (
    // Your login form JSX
  );
}
```

## Advanced Features

### Biometric Analysis

```tsx
import { useBiometrics } from "./deepshield-hooks";

function BiometricCapture() {
  const { createBaseline, analyzeBehavior, isLoading } = useBiometrics(token);
  
  const captureBaseline = async () => {
    const events = [
      { type: "keypress", timestamp: 100.0 },
      { type: "mousemove", timestamp: 101.0, x: 100, y: 50 },
    ];
    
    await createBaseline(userId, events);
  };
  
  return (
    // Your biometric capture JSX
  );
}
```

### Risk Assessment

```tsx
import { useDeepshield } from "./deepshield-context";

function RiskCheck() {
  const { client } = useDeepshield();
  
  const assessRisk = async () => {
    const result = await client.assessRisk(
      userId,
      { overall_score: 0.8 },
      { confidence: 0.85 },
      {
        device: { is_registered: true },
        location: { country: "US" },
        attempt_history: {},
      }
    );
    
    if (result.additional_verification_needed) {
      // Show additional verification UI
    }
  };
  
  return (
    // Your risk assessment JSX
  );
}
```

## API Reference

### Types

All types are exported from `deepshield-types.ts`:

- `User` - User information
- `TokenResponse` - Login response with access token
- `BehavioralEvent` - Individual user interaction event
- `BehavioralProfile` - User's behavioral baseline profile
- `BehavioralAnalysisResult` - Result of behavior analysis
- `RiskContext` - Context for risk assessment
- `RiskAssessmentResult` - Risk assessment result

### Hooks

#### `useAuth()`

Returns authentication-related state and methods:

```tsx
const {
  user,              // Current authenticated user
  token,             // JWT token
  isLoading,         // Loading state
  error,             // Error message if any
  register,          // Register new user (email, password)
  login,             // Login user (email, password)
  logout,            // Logout current user
  fetchCurrentUser,  // Refetch current user data
} = useAuth();
```

#### `useBiometrics(token?)`

Returns biometric-related methods and state:

```tsx
const {
  profile,           // Current behavioral profile
  analysis,          // Latest behavior analysis
  riskAssessment,    // Latest risk assessment
  isLoading,         // Loading state
  error,             // Error message if any
  createBaseline,    // Create baseline (userId, events)
  analyzeBehavior,   // Analyze behavior (userId, events)
  assessRisk,        // Assess risk (userId, biometric, behavioral, context)
} = useBiometrics(token);
```

### DeepshieldAPIClient

Direct API client usage:

```tsx
import { DeepshieldAPIClient } from "./deepshield-api-client";

const client = new DeepshieldAPIClient(token);

// Authentication
await client.register(email, password);
await client.login(email, password);
const user = await client.getCurrentUser();

// Biometrics
const profile = await client.createBaseline(userId, events);
const analysis = await client.analyzeBehavior(userId, events);
const risk = await client.assessRisk(userId, bio, behavioral, context);

// Health
const status = await client.healthCheck();
```

## Error Handling

All API methods throw errors on failure. Wrap calls in try-catch:

```tsx
try {
  await client.login(email, password);
} catch (error) {
  console.error("Login failed:", error.message);
  // Show user-friendly error message
}
```

## Security Considerations

1. **Token Storage**: Tokens are stored in `localStorage`. Consider using more secure alternatives in production.

2. **API URL**: Set `REACT_APP_API_URL` to your backend URL. Never hardcode production URLs.

3. **HTTPS**: Always use HTTPS in production to protect token transmission.

4. **CORS**: Ensure backend CORS settings allow your frontend domain.

## Example: Complete Login Flow

```tsx
import React, { useState } from "react";
import { useAuth } from "./deepshield-hooks";

function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { login, isLoading, error, user } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      // Redirect to dashboard
    } catch (err) {
      // Error is already in `error` state
    }
  };

  if (user) {
    return <div>Welcome, {user.email}!</div>;
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? "Logging in..." : "Login"}
      </button>
      {error && <div className="error">{error}</div>}
    </form>
  );
}

export default LoginForm;
```

## Troubleshooting

### "Failed to fetch" errors
- Check that the backend API is running
- Verify `REACT_APP_API_URL` is correct
- Check browser console for CORS errors

### "Invalid authentication credentials"
- Token may have expired
- Try logging in again
- Check that token is being sent in Authorization header

### "API Error: 403"
- User ID mismatch between frontend and request
- User is not authenticated for the endpoint
- Re-authenticate with `login()`

## Support

For issues, refer to the main Deepshield documentation or contact the development team.
