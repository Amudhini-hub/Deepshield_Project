"use client";

import { useEffect, useState } from "react";
import {
  startCollection,
  stopCollection,
  getStatus,
  subscribe,
  type CollectionStatus,
} from "@/lib/behavioral";
import {
  isAuthenticated,
  getToken,
  getUserIdFromToken,
  AUTH_CHANGE_EVENT,
} from "@/lib/auth";

function resolveUserId(): string | null {
  const token = getToken();
  return token ? getUserIdFromToken(token) : null;
}

export function useBehavioral(): CollectionStatus {
  const [status, setStatus] = useState<CollectionStatus>(getStatus);

  useEffect(() => {
    // Start immediately if already authenticated
    if (isAuthenticated()) {
      const uid = resolveUserId();
      if (uid) startCollection(uid);
    }

    // Subscribe to engine status changes
    const unsubscribe = subscribe(setStatus);

    // React to same-tab login / logout
    function onAuthChange(e: Event) {
      const detail = (e as CustomEvent<{ authenticated: boolean }>).detail;
      if (detail.authenticated) {
        const uid = resolveUserId();
        if (uid) startCollection(uid);
      } else {
        stopCollection();
      }
    }

    // React to cross-tab login / logout via storage event
    function onStorage(e: StorageEvent) {
      if (e.key !== "ds_access_token") return;
      if (e.newValue) {
        const uid = getUserIdFromToken(e.newValue);
        if (uid) startCollection(uid);
      } else {
        stopCollection();
      }
    }

    window.addEventListener(AUTH_CHANGE_EVENT, onAuthChange);
    window.addEventListener("storage", onStorage);

    return () => {
      unsubscribe();
      window.removeEventListener(AUTH_CHANGE_EVENT, onAuthChange);
      window.removeEventListener("storage", onStorage);
      stopCollection();
    };
  }, []);

  return status;
}
