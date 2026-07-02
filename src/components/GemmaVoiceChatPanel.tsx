"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUp, Check, Cloud, Copy, Loader2, Mic, RotateCw, Sparkles, X } from "lucide-react";
import { useServerGemmaVoiceAgent } from "@/hooks/useServerGemmaVoiceAgent";
import { LanguageSelector } from "@/components/LanguageSelector";
import type { VoiceFlow } from "@/types/voiceModel";

interface GemmaVoiceChatPanelProps {
  flow: VoiceFlow;
  onExtracted: (extracted: Record<string, unknown>) => void;
  /** Switches the page back to Cloud mode. */
  onSwitchToCloud: () => void;
  selectedLanguage?: string;
  onLanguageChange?: (lang: string) => void;
}

/**
 * Gemma-4-12B (Modal-hosted) voice + text panel — styled to match the AG-UI
 * CopilotSidebar chat window used by Cloud mode (same copilotKitSidebar/
 * copilotKitWindow shell, message bubbles, and input bar), per the
 * gemma-4-integration branch's VoiceChatPanel. Unlike that branch's
 * WebGPU/E2B pipeline, there's no on-device model to load — the model runs
 * on Modal, so turns are just a network round trip.
 */
export function GemmaVoiceChatPanel({
  flow,
  onExtracted,
  onSwitchToCloud,
  selectedLanguage,
  onLanguageChange,
}: GemmaVoiceChatPanelProps) {
  const { status, error, messages, isRecording, startRecording, stopRecording, sendTextTurn, reset } =
    useServerGemmaVoiceAgent(flow, { onExtracted });

  const [textInput, setTextInput] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [localLanguage, setLocalLanguage] = useState(selectedLanguage || "hi-IN");
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (selectedLanguage) setLocalLanguage(selectedLanguage);
  }, [selectedLanguage]);

  const handleLanguageChange = (lang: string) => {
    setLocalLanguage(lang);
    onLanguageChange?.(lang);
  };

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  const processing = status === "processing";

  const toggleRecording = async () => {
    if (isRecording) {
      stopRecording();
      return;
    }
    if (processing) return;
    await startRecording().catch(() => {});
  };

  const handleSendText = async () => {
    const text = textInput.trim();
    if (!text || processing || isRecording) return;
    setTextInput("");
    textareaRef.current?.focus();
    await sendTextTurn(text).catch(() => {});
  };

  const handleCopy = (text: string, msgId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(msgId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleNewChat = () => {
    reset();
  };

  return (
    <div className="copilotKitSidebar" style={{ zIndex: 1100 }}>
      <div className="copilotKitWindow open flex flex-col h-full bg-background border-l border-border/40 shadow-xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3.5 border-b border-border/40 bg-background shrink-0">
          <span className="text-base font-semibold text-foreground tracking-tight flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-primary" />
            {flow === "registration" ? "Registration Assistant" : "Treatment Assistant"}
          </span>
          <button
            type="button"
            onClick={onSwitchToCloud}
            className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-muted text-muted-foreground hover:text-foreground transition-all cursor-pointer"
            title="Close Assistant"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 flex flex-col" ref={scrollRef}>
          {messages.length === 0 && (
            <div className="py-4 items-start text-sm text-foreground flex flex-col gap-2 animate-in fade-in duration-300">
              <p className="text-foreground font-normal leading-relaxed text-sm">
                Hello! I can help you fill out this form. Speak or type — I understand audio directly, in
                any Indic language, up to several minutes long.
              </p>
            </div>
          )}

          {messages.map((m) => (
            <div key={m.id} className="flex flex-col gap-1">
              {m.role === "user" ? (
                <div className="flex justify-end w-full animate-in slide-in-from-right-2 duration-200">
                  <div className="bg-muted text-foreground rounded-2xl px-4 py-2.5 max-w-[85%] text-sm shadow-sm leading-relaxed">
                    {m.content}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col gap-1.5 py-2 items-start w-full animate-in slide-in-from-left-2 duration-200">
                  <p className="text-sm text-foreground leading-relaxed pr-2 whitespace-pre-wrap">{m.content}</p>
                  <div className="flex items-center gap-1 mt-1 text-muted-foreground/60">
                    <button
                      type="button"
                      onClick={() => handleCopy(m.content, m.id)}
                      className="p-1 rounded-md hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
                      title="Copy to clipboard"
                    >
                      {copiedId === m.id ? (
                        <Check className="w-3.5 h-3.5 text-green-600 dark:text-green-500" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}

          {processing && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground py-2 self-start animate-pulse">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
              <span>Thinking…</span>
            </div>
          )}
        </div>

        {error && <div className="px-4 py-1 text-xs text-destructive shrink-0">{error}</div>}

        {/* Input Box and Controls Area */}
        <div className="p-4 bg-background shrink-0 flex flex-col">
          {messages.length > 0 && (
            <div className="flex justify-center mb-3 animate-in fade-in zoom-in-95 duration-200">
              <button
                type="button"
                onClick={handleNewChat}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-full border border-border/80 bg-background text-xs font-medium text-foreground hover:bg-muted shadow-sm transition-all cursor-pointer"
              >
                <RotateCw className="w-3.5 h-3.5 text-muted-foreground" />
                New Chat
              </button>
            </div>
          )}

          <div className="border border-border/80 rounded-[24px] bg-[#f8f9fa] dark:bg-muted/10 p-3.5 flex flex-col gap-2 shadow-sm">
            <textarea
              ref={textareaRef}
              rows={1}
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendText();
                }
              }}
              placeholder={isRecording ? "Listening…" : "Type a message..."}
              disabled={processing || isRecording}
              className="w-full min-h-[40px] max-h-[160px] resize-none bg-transparent outline-none border-none text-sm p-1 text-foreground placeholder:text-muted-foreground/70 focus:ring-0 focus:outline-none"
            />

            <div className="flex items-center justify-between border-t border-border/20 pt-2.5 mt-1 shrink-0">
              {/* Left Controls */}
              <div className="flex items-center gap-2">
                <LanguageSelector selectedLanguage={localLanguage} onLanguageChange={handleLanguageChange} />

                {/* Segmented Cloud/Gemma-4 Toggle */}
                <div className="inline-flex items-center rounded-full border border-border/40 bg-muted/40 p-0.5 text-[11px]">
                  <button
                    type="button"
                    onClick={onSwitchToCloud}
                    className="flex items-center gap-1 rounded-full px-3 py-1 text-muted-foreground hover:text-foreground transition-all cursor-pointer"
                    title="Switch back to the cloud assistant"
                  >
                    <Cloud className="w-3.5 h-3.5" />
                    Cloud
                  </button>
                  <button
                    type="button"
                    disabled
                    className="flex items-center gap-1 rounded-full px-3 py-1 bg-emerald-700 text-white font-medium shadow-sm transition-all"
                    title="Using Gemma-4-12B (Modal-hosted)"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    Gemma-4
                  </button>
                </div>
              </div>

              {/* Right Controls */}
              <div className="flex items-center gap-2.5">
                <button
                  type="button"
                  onClick={toggleRecording}
                  disabled={processing}
                  className={`w-9 h-9 rounded-full flex items-center justify-center border transition-all shadow-sm cursor-pointer hover:scale-105 active:scale-95 ${
                    isRecording
                      ? "bg-red-500 text-white border-red-500 animate-pulse"
                      : "bg-white dark:bg-zinc-800 border-border/60 text-foreground hover:bg-gray-50 dark:hover:bg-zinc-700"
                  } ${processing ? "opacity-50 cursor-not-allowed" : ""}`}
                  title={isRecording ? "Stop recording" : "Start voice input"}
                >
                  <Mic className="w-4 h-4" />
                </button>

                <button
                  type="button"
                  onClick={handleSendText}
                  disabled={!textInput.trim() || processing || isRecording}
                  className={`flex items-center justify-center transition-all shrink-0 cursor-pointer ${
                    !textInput.trim() || processing || isRecording
                      ? "text-muted-foreground/30 cursor-not-allowed"
                      : "text-foreground hover:text-emerald-700 dark:hover:text-emerald-500 hover:scale-110 active:scale-90"
                  }`}
                  title="Send"
                >
                  {processing ? (
                    <Loader2 className="w-5 h-5 animate-spin text-primary" />
                  ) : (
                    <ArrowUp className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>
          </div>

          <div className="text-[10px] text-muted-foreground/60 font-semibold text-center mt-2.5">
            Gemma-4-12B · understands audio directly
          </div>
        </div>
      </div>
    </div>
  );
}
