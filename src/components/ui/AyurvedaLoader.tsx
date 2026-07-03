"use client";

import { useEffect, useState, type CSSProperties } from "react";
import { cn } from "@/lib/utils";

const DOSHA_MESSAGES = [
  "Balancing Vata, Pitta & Kapha…",
  "Consulting the ancient texts…",
  "Infusing herbal wisdom…",
  "Aligning your prakriti…",
  "Gathering healing insights…",
];

interface AyurvedaLoaderProps {
  /** Renders as a full-viewport overlay with a rotating Ayurveda tagline. */
  fullscreen?: boolean;
  label?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const SIZE_MAP = { sm: 40, md: 80, lg: 120 } as const;

export function AyurvedaLoader({
  fullscreen = false,
  label,
  size = "md",
  className,
}: AyurvedaLoaderProps) {
  const [messageIndex, setMessageIndex] = useState(0);
  const dimension = SIZE_MAP[size];

  useEffect(() => {
    if (!fullscreen) return;
    const interval = setInterval(() => {
      setMessageIndex((i) => (i + 1) % DOSHA_MESSAGES.length);
    }, 2200);
    return () => clearInterval(interval);
  }, [fullscreen]);

  const lampWidth = dimension;
  const lampHeight = dimension * 0.42;
  const flameWidth = dimension * 0.34;
  const flameHeight = dimension * 0.56;
  const emberSize = dimension * 0.4;

  const diya = (
    <div
      className={cn("relative shrink-0", className)}
      style={{ width: dimension, height: dimension * 0.95 }}
      role="status"
      aria-label={label ?? "Loading"}
    >
      {/* warm ember glow behind the wick */}
      <span
        className="absolute rounded-full bg-accent/50 blur-md animate-diya-ember"
        style={{
          width: emberSize,
          height: emberSize,
          left: "50%",
          top: lampHeight * 0.65,
          marginLeft: -emberSize / 2,
          marginTop: -emberSize / 2,
        }}
      />

      {/* flickering flame */}
      <svg
        viewBox="0 0 100 100"
        className="absolute animate-diya-flicker"
        style={
          {
            width: flameWidth,
            height: flameHeight,
            left: "50%",
            top: dimension * 0.02,
            marginLeft: -flameWidth / 2,
            transformOrigin: "50% 100%",
          } as CSSProperties
        }
      >
        <defs>
          <linearGradient id="ayurveda-flame" x1="0" y1="1" x2="0" y2="0">
            <stop offset="0%" stopColor="hsl(15 85% 48%)" />
            <stop offset="55%" stopColor="hsl(35 95% 55%)" />
            <stop offset="100%" stopColor="hsl(50 100% 72%)" />
          </linearGradient>
        </defs>
        <path
          d="M50 6 C32 28 24 48 32 66 C37 79 63 79 68 66 C76 48 68 28 50 6 Z"
          fill="url(#ayurveda-flame)"
        />
      </svg>

      {/* lamp body */}
      <svg
        viewBox="0 0 100 40"
        className="absolute"
        style={{
          width: lampWidth,
          height: lampHeight,
          left: "50%",
          bottom: 0,
          marginLeft: -lampWidth / 2,
        }}
      >
        <defs>
          <linearGradient id="ayurveda-lamp" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="hsl(var(--accent))" />
            <stop offset="100%" stopColor="hsl(30 55% 32%)" />
          </linearGradient>
        </defs>
        <path
          d="M2 16 Q50 -4 98 16 Q74 32 50 24 Q26 32 2 16 Z"
          fill="url(#ayurveda-lamp)"
        />
        <path
          d="M8 15 Q50 0 92 15"
          fill="none"
          stroke="hsl(50 100% 85% / 0.6)"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );

  if (!fullscreen) {
    return diya;
  }

  return (
    <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center gap-5 bg-background/85 backdrop-blur-sm">
      {diya}
      <div className="flex flex-col items-center gap-1 text-center px-4">
        <p className="text-sm font-medium text-foreground">
          {label ?? "Loading ISHA Ayush"}
        </p>
        <p
          key={messageIndex}
          className="text-xs text-muted-foreground animate-loader-fade-in"
        >
          {DOSHA_MESSAGES[messageIndex]}
        </p>
      </div>
    </div>
  );
}
