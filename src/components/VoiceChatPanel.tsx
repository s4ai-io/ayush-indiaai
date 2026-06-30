"use client";

import { useEffect, useRef, useState } from 'react';
import { Mic, Loader2, AlertTriangle, Play, Cloud, ArrowUp, RotateCw, Copy, ThumbsUp, ThumbsDown, Settings, X, Check } from 'lucide-react';
import { useLocalVoiceAgent } from '@/hooks/useLocalVoiceAgent';
import { useWebGPU } from '@/hooks/useWebGPU';
import { LanguageSelector } from '@/components/LanguageSelector';
import type { VoiceFlow } from '@/services/voiceModel/prompts';
import type { LoadingStatus } from '@/types/voiceModel';

interface VoiceChatPanelProps {
    flow: VoiceFlow;
    onExtracted: (extracted: Record<string, unknown>) => void;
    /** Switches the page back to Cloud mode. */
    onSwitchToCloud: () => void;
    selectedLanguage?: string;
    onLanguageChange?: (lang: string) => void;
    onNewChat?: () => void;
}

function formatBytes(bytes: number): string {
    if (!bytes) return '0 MB';
    const mb = bytes / (1024 * 1024);
    return mb >= 1024 ? `${(mb / 1024).toFixed(2)} GB` : `${mb.toFixed(0)} MB`;
}

function getStatusMessage(status: LoadingStatus): string {
    switch (status) {
        case 'idle': return 'Preparing to load the on-device model…';
        case 'checking_webgpu': return 'Detecting WebGPU support…';
        case 'no_webgpu': return 'WebGPU is not available';
        case 'loading_tokenizer': return 'Loading tokenizer…';
        case 'downloading': return 'Downloading model weights (~1.5GB, cached after first load)';
        case 'compiling': return 'Compiling WebGPU shaders…';
        case 'ready': return 'Model ready';
        case 'error': return 'Failed to load model';
        default: return 'Initializing…';
    }
}

/**
 * Local (on-device) voice + text pipeline panel — the Local-mode counterpart to
 * CopilotSidebar. Custom styled to match the new Gemma-4 chatbox UI.
 */
export function VoiceChatPanel({ 
    flow, 
    onExtracted, 
    onSwitchToCloud,
    selectedLanguage,
    onLanguageChange,
    onNewChat
}: VoiceChatPanelProps) {
    const { gpuInfo, isDetecting } = useWebGPU();
    const {
        status,
        error,
        modelState,
        messages,
        setMessages,
        streamingReply,
        ensureModelLoaded,
        sendTextTurn,
        isRecording,
        recorderError,
        startRecording,
        stopRecording,
        reset,
    } = useLocalVoiceAgent(flow, { onExtracted });

    const [textInput, setTextInput] = useState('');
    const [copiedId, setCopiedId] = useState<string | null>(null);
    const [feedback, setFeedback] = useState<Record<string, 'up' | 'down' | null>>({});
    
    const [localLanguage, setLocalLanguage] = useState(selectedLanguage || 'hi-IN');
    const scrollRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        if (selectedLanguage) {
            setLocalLanguage(selectedLanguage);
        }
    }, [selectedLanguage]);

    const handleLanguageChange = (lang: string) => {
        setLocalLanguage(lang);
        if (onLanguageChange) {
            onLanguageChange(lang);
        }
    };

    useEffect(() => {
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
    }, [messages, streamingReply]);

    // Start loading the moment the user opts into Local mode (panel mounts)
    useEffect(() => {
        if (gpuInfo.supported) {
            ensureModelLoaded().catch(() => {});
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [gpuInfo.supported]);

    const modelReady = modelState?.status === 'ready';
    const modelLoading = !!modelState && !modelReady && modelState.status !== 'error' && modelState.status !== 'no_webgpu' && modelState.status !== 'idle';
    const modelErrored = modelState?.status === 'error' || modelState?.status === 'no_webgpu';
    const unsupported = !isDetecting && !gpuInfo.supported;

    const toggleRecording = async () => {
        if (isRecording) {
            stopRecording();
            return;
        }
        if (!modelReady) return;
        await startRecording().catch(() => {});
    };

    const handleSendText = async () => {
        const text = textInput.trim();
        if (!text || !modelReady || status === 'generating') return;
        setTextInput('');
        textareaRef.current?.focus();
        await sendTextTurn(text).catch(() => {});
    };

    const handleRegenerate = async (msgId: string) => {
        if (!setMessages || status === 'generating') return;
        const idx = messages.findIndex(m => m.id === msgId);
        if (idx === -1) return;
        // Find the last user message before this assistant message
        const userMsg = [...messages.slice(0, idx)].reverse().find(m => m.role === 'user');
        if (userMsg) {
            const newMsgs = messages.slice(0, idx);
            setMessages(newMsgs);
            await sendTextTurn(userMsg.content).catch(() => {});
        }
    };

    const handleCopy = (text: string, msgId: string) => {
        navigator.clipboard.writeText(text);
        setCopiedId(msgId);
        setTimeout(() => setCopiedId(null), 2000);
    };

    const handleFeedback = (msgId: string, type: 'up' | 'down') => {
        setFeedback(prev => {
            const current = prev[msgId];
            return {
                ...prev,
                [msgId]: current === type ? null : type
            };
        });
    };

    const handleNewChatClick = () => {
        reset();
        if (onNewChat) {
            onNewChat();
        }
    };

    return (
        <div className="copilotKitSidebar" style={{ zIndex: 1100 }}>
            <div className="copilotKitWindow open flex flex-col h-full bg-background border-l border-border/40 shadow-xl overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3.5 border-b border-border/40 bg-background shrink-0">
                    <span className="text-base font-semibold text-foreground tracking-tight">
                        {flow === 'registration' ? 'Registration Assistant' : 'Treatment Assistant'}
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

                {/* Messages Area / Loader */}
                {unsupported ? (
                    <div className="flex-1 overflow-y-auto p-4">
                        <div className="rounded-xl border border-amber-200 bg-amber-50/50 dark:bg-amber-950/20 dark:border-amber-900/50 p-4 text-sm text-amber-800 dark:text-amber-300 flex gap-3 shadow-sm">
                            <AlertTriangle className="w-5 h-5 shrink-0 text-amber-500 mt-0.5" />
                            <div>
                                <p className="font-semibold">On-device mode isn&apos;t supported in this browser.</p>
                                <p className="mt-1 text-xs text-amber-700 dark:text-amber-400 leading-relaxed">
                                    WebGPU is required (Chrome/Edge 113+, Safari 18+). Use the Cloud assistant
                                    by clicking the close button above or switching modes.
                                </p>
                            </div>
                        </div>
                    </div>
                ) : (
                    <>
                        <div className="flex-1 overflow-y-auto p-4 space-y-4 flex flex-col" ref={scrollRef}>
                            {/* Model load progress — shown until ready */}
                            {!modelReady && (
                                <div className="p-4 bg-muted/30 rounded-2xl border border-border/30 text-xs space-y-3 shrink-0 shadow-sm">
                                    <div className="flex items-center gap-2 font-medium text-foreground">
                                        {modelLoading && (
                                            <span className="flex h-2.5 w-2.5 relative">
                                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
                                                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary" />
                                            </span>
                                        )}
                                        <span>{getStatusMessage(modelState?.status ?? 'idle')}</span>
                                    </div>

                                    {modelLoading && (
                                        <>
                                            <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                                                <div
                                                    className="h-full bg-primary transition-all duration-300"
                                                    style={{ width: `${modelState?.progress ?? 0}%` }}
                                                />
                                            </div>
                                            <div className="flex justify-between text-muted-foreground font-mono text-[10px]">
                                                <span>{modelState?.progress ?? 0}%</span>
                                                {!!modelState?.totalBytes && (
                                                    <span>{formatBytes(modelState.downloadedBytes)} / {formatBytes(modelState.totalBytes)}</span>
                                                )}
                                            </div>
                                            {modelState?.activeFile && (
                                                <p className="truncate text-muted-foreground font-mono text-[10px]">{modelState.activeFile}</p>
                                            )}
                                        </>
                                    )}

                                    {modelErrored && (
                                        <div className="space-y-2">
                                            <p className="text-destructive text-[11px] leading-relaxed">{modelState?.errorMsg}</p>
                                            <button
                                                type="button"
                                                onClick={() => ensureModelLoaded().catch(() => {})}
                                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-destructive text-destructive-foreground text-[11px] font-medium hover:bg-destructive/90 transition-colors shadow-sm animate-in fade-in"
                                            >
                                                <Play className="w-3.5 h-3.5" /> Retry
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}

                            {modelReady && messages.length === 0 && !streamingReply && (
                                <div className="py-4 items-start text-sm text-foreground flex flex-col gap-2 animate-in fade-in duration-300">
                                    <p className="text-foreground font-normal leading-relaxed text-sm">
                                        Hello! I can help you fill out this form. Just tell me your details.
                                    </p>
                                </div>
                            )}

                            {/* Message List */}
                            {messages.map((m) => (
                                <div key={m.id} className="flex flex-col gap-1">
                                    {m.role === 'user' ? (
                                        <div className="flex justify-end w-full animate-in slide-in-from-right-2 duration-200">
                                            <div className="bg-muted text-foreground rounded-2xl px-4 py-2.5 max-w-[85%] text-sm shadow-sm leading-relaxed">
                                                {m.content}
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="flex flex-col gap-1.5 py-2 items-start w-full animate-in slide-in-from-left-2 duration-200">
                                            <p className="text-sm text-foreground leading-relaxed pr-2 whitespace-pre-wrap">
                                                {m.content}
                                            </p>
                                            <div className="flex items-center gap-1 mt-1 text-muted-foreground/60">
                                                <button
                                                    type="button"
                                                    onClick={() => handleRegenerate(m.id)}
                                                    className="p-1 rounded-md hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
                                                    title="Regenerate response"
                                                >
                                                    <RotateCw className="w-3.5 h-3.5" />
                                                </button>
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
                                                <button
                                                    type="button"
                                                    onClick={() => handleFeedback(m.id, 'up')}
                                                    className={`p-1 rounded-md hover:bg-muted transition-colors cursor-pointer ${
                                                        feedback[m.id] === 'up' ? 'text-green-600 dark:text-green-500' : 'hover:text-foreground'
                                                    }`}
                                                    title="Thumbs up"
                                                >
                                                    <ThumbsUp className={`w-3.5 h-3.5 ${feedback[m.id] === 'up' ? 'fill-current' : ''}`} />
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={() => handleFeedback(m.id, 'down')}
                                                    className={`p-1 rounded-md hover:bg-muted transition-colors cursor-pointer ${
                                                        feedback[m.id] === 'down' ? 'text-red-500 hover:text-foreground' : 'hover:text-foreground'
                                                    }`}
                                                    title="Thumbs down"
                                                >
                                                    <ThumbsDown className={`w-3.5 h-3.5 ${feedback[m.id] === 'down' ? 'fill-current' : ''}`} />
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}

                            {/* Streaming Reply */}
                            {streamingReply && (
                                <div className="flex flex-col gap-1 py-2 items-start w-full">
                                    <p className="text-sm text-foreground leading-relaxed pr-2 whitespace-pre-wrap">
                                        {streamingReply}
                                    </p>
                                </div>
                            )}

                            {/* Thinking State */}
                            {status === 'generating' && !streamingReply && (
                                <div className="flex items-center gap-2 text-xs text-muted-foreground py-2 self-start animate-pulse">
                                    <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
                                    <span>Thinking…</span>
                                </div>
                            )}
                        </div>

                        {(error || recorderError) && (
                            <div className="px-4 py-1 text-xs text-destructive shrink-0">
                                {error || recorderError}
                            </div>
                        )}

                        {/* Input Box and Controls Area */}
                        <div className="p-4 bg-background shrink-0 flex flex-col">
                            {/* Centered New Chat Button */}
                            {modelReady && (
                                <div className="flex justify-center mb-3 animate-in fade-in zoom-in-95 duration-200">
                                    <button
                                        type="button"
                                        onClick={handleNewChatClick}
                                        className="flex items-center gap-1.5 px-4 py-1.5 rounded-full border border-border/80 bg-background text-xs font-medium text-foreground hover:bg-muted shadow-sm transition-all cursor-pointer hover:scale-102 active:scale-98"
                                    >
                                        <RotateCw className="w-3.5 h-3.5 text-muted-foreground" />
                                        New Chat
                                    </button>
                                </div>
                            )}

                            {/* Input Container */}
                            <div className="border border-border/80 rounded-[24px] bg-[#f8f9fa] dark:bg-muted/10 p-3.5 flex flex-col gap-2 shadow-sm">
                                <textarea
                                    ref={textareaRef}
                                    rows={1}
                                    value={textInput}
                                    onChange={(e) => setTextInput(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && !e.shiftKey) {
                                            e.preventDefault();
                                            handleSendText();
                                        }
                                    }}
                                    placeholder={modelReady ? 'Type a message...' : 'Waiting for model...'}
                                    disabled={!modelReady || status === 'generating' || isRecording}
                                    className="w-full min-h-[40px] max-h-[160px] resize-none bg-transparent outline-none border-none text-sm p-1 text-foreground placeholder:text-muted-foreground/70 focus:ring-0 focus:outline-none"
                                />
                                
                                {/* Footer row inside input box */}
                                <div className="flex items-center justify-between border-t border-border/20 pt-2.5 mt-1 shrink-0">
                                    {/* Left Controls */}
                                    <div className="flex items-center gap-2">
                                        <LanguageSelector
                                            selectedLanguage={localLanguage}
                                            onLanguageChange={handleLanguageChange}
                                        />

                                        {/* Segmented Cloud/Local Toggle */}
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
                                                title="Using Local on-device model"
                                            >
                                                <Settings className="w-3.5 h-3.5" />
                                                Local
                                            </button>
                                        </div>
                                    </div>

                                    {/* Right Controls */}
                                    <div className="flex items-center gap-2.5">
                                        {/* Mic Button */}
                                        <button
                                            type="button"
                                            onClick={toggleRecording}
                                            disabled={!modelReady || status === 'generating'}
                                            className={`w-9 h-9 rounded-full flex items-center justify-center border transition-all shadow-sm cursor-pointer hover:scale-105 active:scale-95 ${
                                                isRecording
                                                    ? 'bg-red-500 text-white border-red-500 animate-pulse'
                                                    : 'bg-white dark:bg-zinc-800 border-border/60 text-foreground hover:bg-gray-50 dark:hover:bg-zinc-700'
                                            }`}
                                            title={isRecording ? 'Stop recording' : 'Start voice input'}
                                        >
                                            <Mic className="w-4 h-4" />
                                        </button>
                                        
                                        {/* Send Button */}
                                        <button
                                            type="button"
                                            onClick={handleSendText}
                                            disabled={!modelReady || !textInput.trim() || status === 'generating' || isRecording}
                                            className={`flex items-center justify-center transition-all shrink-0 cursor-pointer ${
                                                !textInput.trim() || !modelReady || status === 'generating' || isRecording
                                                    ? 'text-muted-foreground/30 cursor-not-allowed'
                                                    : 'text-foreground hover:text-emerald-700 dark:hover:text-emerald-500 hover:scale-110 active:scale-90'
                                            }`}
                                            title="Send"
                                        >
                                            {status === 'generating' ? (
                                                <Loader2 className="w-5 h-5 animate-spin text-primary" />
                                            ) : (
                                                <ArrowUp className="w-5 h-5" />
                                            )}
                                        </button>
                                    </div>
                                </div>
                            </div>
                            
                            {/* Powered by CopilotKit */}
                            <div className="text-[10px] text-muted-foreground/60 font-semibold text-center mt-2.5">
                                Powered by CopilotKit
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
