"use client";

import { Cloud, Cpu } from 'lucide-react';
import type { VoicePipelineMode } from '@/types/voiceModel';

interface VoicePipelineToggleProps {
    mode: VoicePipelineMode;
    onChange: (mode: VoicePipelineMode) => void;
}

/**
 * Lets the user pick between the existing cloud pipeline (Modal ASR + Phi-4,
 * default — unchanged behavior) and the new on-device Gemma-4 pipeline.
 * Purely additive: nothing reads this component's state except the two
 * pages that render it.
 */
export function VoicePipelineToggle({ mode, onChange }: VoicePipelineToggleProps) {
    return (
        <div className="inline-flex items-center rounded-full border border-border bg-muted/40 p-0.5 text-xs">
            <button
                type="button"
                onClick={() => onChange('cloud')}
                title="Cloud pipeline: Modal ASR + Phi-4 (default)"
                className={`flex items-center gap-1 rounded-full px-2.5 py-1 transition-colors ${mode === 'cloud'
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
            >
                <Cloud className="w-3 h-3" />
                Cloud
            </button>
            <button
                type="button"
                onClick={() => onChange('local')}
                title="On-device pipeline: Gemma-4-E2B running in your browser (WebGPU required)"
                className={`flex items-center gap-1 rounded-full px-2.5 py-1 transition-colors ${mode === 'local'
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
            >
                <Cpu className="w-3 h-3" />
                Local
            </button>
        </div>
    );
}
