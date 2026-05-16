"use client";

import { createContext, useContext } from "react";
import { useBehavioral } from "@/hooks/useBehavioral";
import type { CollectionStatus } from "@/lib/behavioral";
import BiometricStatus from "@/components/BiometricStatus";

const BehavioralContext = createContext<CollectionStatus | null>(null);

export function useBehavioralContext(): CollectionStatus {
  const ctx = useContext(BehavioralContext);
  if (!ctx) throw new Error("useBehavioralContext must be used inside BehavioralProvider");
  return ctx;
}

export default function BehavioralProvider({ children }: { children: React.ReactNode }) {
  const status = useBehavioral();

  return (
    <BehavioralContext.Provider value={status}>
      {children}
      <BiometricStatus />
    </BehavioralContext.Provider>
  );
}
