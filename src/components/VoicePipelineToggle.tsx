"use client";

import { Cloud, Sparkles } from "lucide-react";
import type { VoicePipelineMode } from "@/types/voiceModel";

interface VoicePipelineToggleProps {
  mode: VoicePipelineMode;
  onChange: (mode: VoicePipelineMode) => void;
}

/**
 * Lets the user pick between the existing pipeline (Modal ASR + IndicTrans2 +
 * Phi-4 via AG-UI tool-calling, default — unchanged behavior) and the new
 * Gemma-4-12B pipeline (Modal-hosted, understands audio directly, no
 * AG-UI/tool-calling). Purely additive: nothing reads this component's state
 * except the pages that render it.
 */
export function VoicePipelineToggle({ mode, onChange }: VoicePipelineToggleProps) {
  return (
    <div className="inline-flex items-center rounded-full border border-border bg-muted/40 p-0.5 text-xs">
      <button
        type="button"
        onClick={() => onChange("cloud")}
        title="Cloud pipeline: Modal ASR + Phi-4 (default)"
        className={`flex items-center gap-1 rounded-full px-2.5 py-1 transition-colors ${
          mode === "cloud"
            ? "bg-primary text-primary-foreground"
            : "text-muted-foreground hover:text-foreground"
        }`}
      >
        <Cloud className="w-3 h-3" />
        Cloud
      </button>
      <button
        type="button"
        onClick={() => onChange("gemma4")}
        title="Gemma-4-12B: understands audio directly (Modal-hosted)"
        className={`flex items-center gap-1 rounded-full px-2.5 py-1 transition-colors ${
          mode === "gemma4"
            ? "bg-primary text-primary-foreground"
            : "text-muted-foreground hover:text-foreground"
        }`}
      >
        <Sparkles className="w-3 h-3" />
        Gemma-4
      </button>
    </div>
  );
}
