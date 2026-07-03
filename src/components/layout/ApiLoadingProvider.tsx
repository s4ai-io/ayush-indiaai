"use client";

import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { Flame } from "lucide-react";

interface ApiLoadingContextValue {
  isLoading: boolean;
}

const ApiLoadingContext = createContext<ApiLoadingContextValue>({
  isLoading: false,
});

export function useApiLoading() {
  return useContext(ApiLoadingContext);
}

// Guards against re-patching window.fetch across remounts / HMR.
let fetchPatched = false;

/**
 * System-level API loading indicator. Wraps window.fetch once so every
 * request in the app (server actions, ml-client, route handlers) is tracked
 * automatically, without touching individual call sites.
 */
export function ApiLoadingProvider({ children }: { children: ReactNode }) {
  const [pending, setPending] = useState(0);
  const pendingRef = useRef(0);

  useEffect(() => {
    if (fetchPatched || typeof window === "undefined") return;
    fetchPatched = true;

    const originalFetch = window.fetch.bind(window);

    window.fetch = async (...args: Parameters<typeof window.fetch>) => {
      pendingRef.current += 1;
      setPending(pendingRef.current);
      try {
        return await originalFetch(...args);
      } finally {
        pendingRef.current = Math.max(0, pendingRef.current - 1);
        setPending(pendingRef.current);
      }
    };
  }, []);

  const isLoading = pending > 0;

  return (
    <ApiLoadingContext.Provider value={{ isLoading }}>
      {children}
      <ApiLoadingIndicator isLoading={isLoading} />
    </ApiLoadingContext.Provider>
  );
}

function ApiLoadingIndicator({ isLoading }: { isLoading: boolean }) {
  return (
    <div
      aria-hidden={!isLoading}
      className={`pointer-events-none fixed inset-x-0 top-0 z-[200] transition-opacity duration-300 ${
        isLoading ? "opacity-100" : "opacity-0"
      }`}
    >
      <div className="relative h-[3px] w-full overflow-hidden">
        {isLoading && (
          <div className="absolute inset-y-0 w-1/3 animate-vine-travel rounded-full bg-gradient-to-r from-primary via-accent to-primary shadow-[0_0_8px_1px] shadow-accent/60" />
        )}
      </div>
      <div
        className={`absolute right-4 top-3 flex items-center gap-1.5 rounded-full bg-card/90 px-2.5 py-1 text-xs text-muted-foreground shadow-sm ring-1 ring-border backdrop-blur transition-all duration-300 ${
          isLoading ? "translate-y-0 opacity-100" : "-translate-y-1 opacity-0"
        }`}
      >
        <Flame className="h-3.5 w-3.5 animate-badge-flicker text-accent" />
        <span>Syncing…</span>
      </div>
    </div>
  );
}
