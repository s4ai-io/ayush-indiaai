
import React, { useState } from 'react';
import Markdown from 'react-markdown';
import { FiChevronLeft, FiChevronRight } from "react-icons/fi";
import { twMerge } from "tailwind-merge";

export type ToolTheme = "green" | "purple" | "slate" | "pink" | "amber" | "teal" | "yellow" | "red" | "violet" | "indigo" | "blue";

interface GenericToolCardProps {
    user_query: string;
    result?: string;
    status: "inProgress" | "executing" | "complete";
    title: string;
    subtitle: string;
    theme: ToolTheme;
    icon: string;
    toolRenderers?: Record<string, (data: any) => React.ReactNode>;
}

// ... existing helpers ...
// Unified Neon Theme Classes
const getThemeClasses = (theme: ToolTheme) => {
    // We Map all "themes" to varying styles of our core Neon aesthetic
    // But keeping it consistent with the global dark theme
    const base = {
        bg: "bg-card-bg/50 backdrop-blur-md", // Translucent dark
        border: "border-neon-purple/30",
        text: "text-white",
        subtext: "text-gray-400",
        iconBg: "bg-white/5",
        iconText: "text-neon-purple",
        progress: "border-neon-blue",
        ping: "bg-neon-purple",
        prose: "prose-invert" // Tailwind typography dark mode
    };

    // Optional: We could add subtle variations based on 'theme' prop if strictly needed,
    // but for a unified look, returning the consistent base is better.
    return base;
};

// Start of helper to get icon content
const getIcon = (icon: string) => {
    switch (icon) {
        case "currency": return <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />;
        case "target": return <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />;
        case "support": return <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />;
        case "tag": return <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />;
        case "calculator": return <><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.488 9H15V3.512A9.025 9.001 0 0120.488 9z" /></>;
        case "users": return <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />;
        case "cart": return <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />;
        case "clock": return <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />;
        case "game": return <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />;
        case "sparkles": return <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />;
        default: return <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />;
    }
}
// End of helper

// Carousel Component
const ImageCarousel = ({ images }: { images: string[] }) => {
    const [currentIndex, setCurrentIndex] = useState(0);

    const nextSlide = () => {
        setCurrentIndex((prev) => (prev + 1) % images.length);
    };

    const prevSlide = () => {
        setCurrentIndex((prev) => (prev - 1 + images.length) % images.length);
    };

    if (!images || images.length === 0) return null;

    return (
        <div className="relative w-full h-48 mb-4 group rounded-xl overflow-hidden shadow-sm border border-gray-100 bg-gray-50">
            <img
                src={images[currentIndex]}
                alt={`Product ${currentIndex + 1} `}
                className="w-full h-full object-contain mix-blend-multiply"
            />

            {images.length > 1 && (
                <>
                    <button
                        onClick={prevSlide}
                        className="absolute left-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white text-gray-800 p-1.5 rounded-full shadow-md transition-all opacity-0 group-hover:opacity-100"
                    >
                        <FiChevronLeft size={18} />
                    </button>
                    <button
                        onClick={nextSlide}
                        className="absolute right-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white text-gray-800 p-1.5 rounded-full shadow-md transition-all opacity-0 group-hover:opacity-100"
                    >
                        <FiChevronRight size={18} />
                    </button>
                    <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1.5">
                        {images.map((_, idx) => (
                            <div
                                key={idx}
                                className={`w - 1.5 h - 1.5 rounded - full transition - all ${idx === currentIndex ? 'bg-indigo-600 w-3' : 'bg-gray-300'} `}
                            ></div>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
};

// Helper to extract images and clean text
const parsePythonLiteral = (str: string) => {
    let cursor = 0;

    const peek = () => str[cursor];
    const consume = () => str[cursor++];
    const eof = () => cursor >= str.length;

    const skipWhitespace = () => {
        while (!eof() && /\s/.test(peek())) cursor++;
    };

    const parseString = () => {
        const quote = consume(); // ' or "
        let result = "";
        while (!eof()) {
            const char = consume();
            if (char === '\\') {
                if (!eof()) result += consume();
            } else if (char === quote) {
                return result;
            } else {
                result += char;
            }
        }
        return result;
    }

    const parseNumber = () => {
        let start = cursor;
        if (peek() === '-') consume();
        while (!eof() && /[0-9.]/.test(peek())) consume();
        const numStr = str.slice(start, cursor);
        return parseFloat(numStr);
    }

    const parseIdentifier = () => {
        let start = cursor;
        while (!eof() && /[a-zA-Z0-9_.]/.test(peek())) consume();
        return str.slice(start, cursor);
    }

    const parseValue = (): any => {
        skipWhitespace();
        if (eof()) return null;

        const char = peek();

        if (char === "'" || char === '"') return parseString();
        if (/[0-9\-]/.test(char)) return parseNumber();
        if (char === '[') return parseList();
        if (char === '{') return parseDict();
        if (char === '(') return parseTuple();

        if (/[a-zA-Z_]/.test(char)) {
            const id = parseIdentifier();
            if (id === 'None') return null;
            if (id === 'True') return true;
            if (id === 'False') return false;

            skipWhitespace();
            if (peek() === '(') {
                return parseCall(id);
            }
            return id;
        }

        cursor++;
        return null;
    }

    const parseList = () => {
        consume(); // [
        const res = [];
        while (!eof()) {
            skipWhitespace();
            if (peek() === ']') { consume(); break; }
            res.push(parseValue());
            skipWhitespace();
            if (peek() === ',') consume();
        }
        return res;
    }

    const parseTuple = () => {
        consume(); // (
        const res = [];
        while (!eof()) {
            skipWhitespace();
            if (peek() === ')') { consume(); break; }
            res.push(parseValue());
            skipWhitespace();
            if (peek() === ',') consume();
        }
        return res;
    }

    const parseDict = () => {
        consume(); // {
        const res: any = {};
        while (!eof()) {
            skipWhitespace();
            if (peek() === '}') { consume(); break; }
            const key = parseValue();
            skipWhitespace();
            if (peek() === ':') consume();
            const val = parseValue();
            res[key] = val;
            skipWhitespace();
            if (peek() === ',') consume();
        }
        return res;
    }

    const parseCall = (name: string) => {
        consume(); // (
        const args: any[] = [];
        const kwargs: any = {};

        while (!eof()) {
            skipWhitespace();
            if (peek() === ')') { consume(); break; }

            const start = cursor;
            if (/[a-zA-Z_]/.test(peek())) {
                const possibleId = parseIdentifier();
                skipWhitespace();
                if (peek() === '=') {
                    consume();
                    const val = parseValue();
                    kwargs[possibleId] = val;
                } else {
                    // Backtrack if not a kwarg
                    cursor = start;
                    args.push(parseValue());
                }
            } else {
                args.push(parseValue());
            }

            skipWhitespace();
            if (peek() === ',') consume();
        }

        if (Object.keys(kwargs).length > 0) {
            return { __type: name, ...kwargs, __args: args };
        }
        if (name.includes('datetime')) {
            if (args.length >= 3) {
                return new Date(args[0], args[1] - 1, args[2], args[3] || 0, args[4] || 0, args[5] || 0).toLocaleString();
            }
            return `[${name}: ${args.join(', ')}]`;
        }

        return { __type: name, ...kwargs, __args: args };
    }

    return parseValue();
}

// Helper to extract images and clean text
const processContent = (result?: string) => {
    if (!result) return { text: "", images: [], tools: [] };

    let text = result;
    let images: string[] = [];
    let tools: any[] = [];

    // 1. Try to parse assuming it is the specific Python dict format
    if (text.trim().startsWith("{") && text.includes("'response':")) {
        try {
            const parsed = parsePythonLiteral(text);
            if (parsed && typeof parsed === 'object') {
                if (parsed.response) text = parsed.response;
                if (parsed.sources && Array.isArray(parsed.sources)) {
                    // Flatten sources if it's nested
                    tools = parsed.sources.flat();
                }
            }
        } catch (e) {
            console.warn("Failed to parse tool result as Python literal", e);
        }
    }
    // Fallback old parsing if needed
    else if (text.trim().startsWith("{'response':")) {
        try {
            const match = text.match(/'response':\s*(['"])([\s\S]*?)\1/);
            if (match && match[2]) {
                text = match[2].replace(/\\n/g, '\n');
            }
        } catch (e) {
            // parsing failed
        }
    }

    // 2. Extract image URLs
    const urlPattern = /(https?:\/\/[^\s]+?\.(?:jpg|jpeg|png|gif|webp))/gi;
    const mdImagePattern = /!\[.*?\]\((https?:\/\/[^\s]+?)\)/g;

    let mdMatch;
    while ((mdMatch = mdImagePattern.exec(text)) !== null) {
        if (mdMatch[1]) images.push(mdMatch[1]);
    }

    const rawMatches = text.match(urlPattern);
    if (rawMatches) {
        rawMatches.forEach(url => {
            if (!images.includes(url) && !text.includes(`](${url})`)) {
                images.push(url);
            }
        });
    }

    if (images.length > 0) {
        text = text.replace(mdImagePattern, '');
    }

    return { text, images, tools };
}

const ToolDetails = ({ tools, theme, toolRenderers }: { tools: any[], theme: ToolTheme, toolRenderers?: Record<string, (data: any) => React.ReactNode> }) => {
    const styles = getThemeClasses(theme);
    const [expanded, setExpanded] = useState<number | null>(null);

    if (!tools || tools.length === 0) return null;

    return (
        <div className="mt-4 pt-4">
            <div className="space-y-3">
                {tools.map((tool, idx) => {
                    const isExpanded = expanded === idx;
                    const rawOutput = tool.raw_output;
                    const hasItems = Array.isArray(rawOutput) && rawOutput.length > 0;

                    const CustomRenderer = toolRenderers?.[tool.tool_name];
                    // console.log("tool", tool);
                    // console.log("CustomRenderer", CustomRenderer);

                    if (!CustomRenderer) return null;

                    return (
                        <div key={idx} className="overflow-hidden  rounded-xl">
                            <div className="px-6 py-0">
                                {CustomRenderer(rawOutput)}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export function GenericToolCard({ user_query, result, status, title, subtitle, theme, icon, toolRenderers }: GenericToolCardProps) {
    const styles = getThemeClasses(theme);
    const { text, images, tools } = processContent(result);
    // console.log("tools", tools);

    return (
        <div className={`p-5 rounded-2xl shadow-xl border w-full transition-all duration-300 ${styles.bg} ${styles.border} `}>
            <div className={`flex items-center gap-3 mb-4 border-b pb-3 border-white/10`}>
                <div className={`${styles.iconBg} p-2 rounded-lg ${styles.iconText} shadow-lg shadow-neon-purple/20 border border-white/10`}>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        {getIcon(icon)}
                    </svg>
                </div>
                <div>
                    <h3 className={`font-bold text-md ${styles.text} `}>{title}</h3>
                    <p className={`text-xs ${styles.subtext} font-medium uppercase tracking-wider`}>{subtitle}</p>
                </div>
                <div className="ml-auto">
                    {status === "inProgress" || status === "executing" ? (
                        <span className="flex h-3 w-3 relative">
                            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${styles.ping} opacity-75`}></span>
                            <span className={`relative inline-flex rounded-full h-3 w-3 bg-neon-purple`}></span>
                        </span>
                    ) : (
                        <span className="text-neon-blue drop-shadow-[0_0_3px_rgba(38,240,255,0.5)]">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                        </span>
                    )}
                </div>
            </div>

            {/* <div className="mb-4 bg-gray-50 p-3 rounded-lg border border-gray-100">
                <p className="text-xs text-gray-400 uppercase font-bold mb-1">Request</p>
                <p className="text-sm text-gray-700 italic">"{user_query}"</p>
            </div> */}

            {status === "inProgress" || status === "executing" ? (
                <div className="py-8 text-center">
                    <div className={`inline-block animate-spin rounded-full h-8 w-8 border-b-2 ${styles.progress} mb-2`}></div>
                    <p className={`${styles.iconText} font-medium animate-pulse`}>Processing...</p>
                </div>
            ) : (
                <div className={`prose prose-sm ${styles.prose} max-w-none text-gray-300`}>
                    {/* {images.length > 0 && <ImageCarousel images={images} />}
                    <Markdown>{text || ""}</Markdown> */}
                    {tools && tools.length > 0 && <ToolDetails tools={tools} theme={theme} toolRenderers={toolRenderers} />}
                </div>
            )}
        </div>
    );
}
