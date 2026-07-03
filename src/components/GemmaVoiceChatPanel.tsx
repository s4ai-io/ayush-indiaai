"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUp, Check, Copy, Loader2, Mic, RotateCw, Sparkles, Square, X } from "lucide-react";
import { useServerGemmaVoiceAgent } from "@/hooks/useServerGemmaVoiceAgent";
import { VoiceInputButton } from "@/components/VoiceInputButton";
import { LanguageSelector } from "@/components/LanguageSelector";
import { cn } from "@/lib/utils";
import type { VoiceFlow, VoiceModel } from "@/types/voiceModel";

interface GemmaVoiceChatPanelProps {
  flow: VoiceFlow;
  onExtracted: (extracted: Record<string, unknown>) => void;
}

const MODEL_LABEL: Record<VoiceModel, string> = { gemma4: "Gemma-4", phi4: "Phi-4" };

/**
 * The app's only chat/voice-assistant UI (no AG-UI/CopilotKit involved) —
 * a closable floating panel, fixed to the viewport so it never scrolls with
 * the page. Backs onto two interchangeable turn endpoints selected via the
 * model toggle in the input toolbar:
 *  - Gemma-4-12B (Modal-hosted, POST /api/gemma4-turn) — understands audio
 *    directly, so its mic button records and sends raw audio.
 *  - Phi-4 (vLLM-hosted, POST /api/phi4-turn) — text-only, so its mic
 *    button reuses the browser/cloud speech-to-text path (VoiceInputButton
 *    → /api/transcribe) and sends the resulting transcript as a text turn.
 * Both reply with the same {reply, extracted} shape, so switching models
 * mid-conversation doesn't change how results are consumed.
 */
export function GemmaVoiceChatPanel({ flow, onExtracted }: GemmaVoiceChatPanelProps) {
  const { status, error, messages, isRecording, startRecording, stopRecording, sendTextTurn, stopGeneration, reset } =
    useServerGemmaVoiceAgent(flow, { onExtracted });

  const [isOpen, setIsOpen] = useState(true);
  const [model, setModel] = useState<VoiceModel>("gemma4");
  const [textInput, setTextInput] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [language, setLanguage] = useState("hi-IN");
  const [dictateError, setDictateError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

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
    await sendTextTurn(text, model).catch(() => {});
  };

  const handleDictateTranscript = (text: string) => {
    setDictateError(null);
    if (text.trim()) sendTextTurn(text.trim(), model).catch(() => {});
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
    <>
      {/* "Open assistant" launcher — shown whenever the panel is closed */}
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className={cn(
          "fixed bottom-6 right-6 z-40 flex items-center gap-2 pl-3.5 pr-4 py-3 rounded-full bg-primary text-primary-foreground shadow-xl hover:shadow-2xl hover:scale-105 active:scale-95 transition-all duration-200",
          isOpen ? "opacity-0 scale-90 pointer-events-none" : "opacity-100 scale-100"
        )}
        title="Open the AI assistant"
      >
        <Sparkles className="w-4 h-4" />
        <span className="text-sm font-semibold">Assistant</span>
      </button>

      {/* Backdrop — mobile only */}
      <div
        className={cn(
          "fixed inset-0 bg-black/40 backdrop-blur-[2px] z-40 md:hidden transition-opacity duration-300",
          isOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        )}
        onClick={() => setIsOpen(false)}
        aria-hidden="true"
      />

      {/* Panel — full-screen drawer on mobile, floating closable panel on desktop */}
      <div
        className={cn(
          "fixed top-0 right-0 h-full w-full sm:w-96 z-50 flex flex-col bg-background border-l border-border transition-transform duration-300 ease-in-out",
          "shadow-[-12px_0_32px_-8px_rgba(0,0,0,0.12)]",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between gap-2 px-4 py-3.5 border-b border-border bg-primary/5 shrink-0">
          <span className="text-base font-semibold text-foreground tracking-tight flex items-center gap-1.5 min-w-0">
            <Sparkles className="w-4 h-4 text-primary shrink-0" />
            <span className="truncate">{flow === "registration" ? "Registration Assistant" : "Treatment Assistant"}</span>
          </span>
          <button
            type="button"
            onClick={() => setIsOpen(false)}
            className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-muted text-muted-foreground hover:text-foreground transition-all cursor-pointer shrink-0"
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
                Hello! I can help you fill out this form. Speak or type.
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

        {(error || dictateError) && (
          <div className="px-4 py-1 text-xs text-destructive shrink-0">{error || dictateError}</div>
        )}

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
              {/* Left Controls — language + model toggle */}
              <div className="flex items-center gap-1.5">
                <LanguageSelector selectedLanguage={language} onLanguageChange={setLanguage} />
                <div className="inline-flex items-center rounded-full border border-border bg-background p-0.5 text-[11px] shadow-sm">
                  {(Object.keys(MODEL_LABEL) as VoiceModel[]).map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setModel(m)}
                      title={m === "gemma4" ? "Gemma-4-12B — understands audio directly" : "Phi-4 — transcribes audio first"}
                      className={cn(
                        "rounded-full px-2.5 py-1 font-semibold transition-all",
                        model === m ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
                      )}
                    >
                      {MODEL_LABEL[m]}
                    </button>
                  ))}
                </div>
              </div>

              {/* Right Controls */}
              <div className="flex items-center gap-2.5">
                {model === "gemma4" ? (
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
                ) : (
                  <VoiceInputButton
                    onTranscript={handleDictateTranscript}
                    onError={setDictateError}
                    language={language}
                  />
                )}

                {processing ? (
                  <button
                    type="button"
                    onClick={stopGeneration}
                    className="flex items-center justify-center w-8 h-8 rounded-full bg-foreground text-background shrink-0 cursor-pointer hover:scale-110 active:scale-90 transition-all"
                    title="Stop generating"
                  >
                    <Square className="w-3.5 h-3.5 fill-current" />
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={handleSendText}
                    disabled={!textInput.trim() || isRecording}
                    className={`flex items-center justify-center transition-all shrink-0 cursor-pointer ${
                      !textInput.trim() || isRecording
                        ? "text-muted-foreground/30 cursor-not-allowed"
                        : "text-foreground hover:text-emerald-700 dark:hover:text-emerald-500 hover:scale-110 active:scale-90"
                    }`}
                    title="Send"
                  >
                    <ArrowUp className="w-5 h-5" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
