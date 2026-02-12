'use client';

import React from 'react';
import { X } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useChat } from '../context/ChatContext';
import Chat from './Chat';

// Utility for tailwind class merging
function cn(...inputs: (string | undefined | null | false)[]) {
    return twMerge(clsx(inputs));
}

const Chatbot = () => {
    const { isOpen, closeChat } = useChat();

    return (
        <div
            className={cn(
                "fixed bottom-24 right-0 px-4 z-50 w-[100%] flex flex-col transition-all duration-500 ease-in-out origin-bottom-right h-[calc(100vh-10rem)] backdrop-blur-xl",
                isOpen
                    ? "opacity-100 scale-100 translate-y-0"
                    : "opacity-0 scale-75 translate-y-10 pointer-events-none"
            )}
        >
            <div className="bg-card-bg/95 backdrop-blur-xl border border-neon-purple/30 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-full relative">
                {/* Close Button Overlay */}
                <button
                    onClick={closeChat}
                    className="absolute top-4 right-4 z-10 p-2 bg-black/50 hover:bg-black/70 rounded-full text-white/70 hover:text-white transition-all backdrop-blur-sm"
                >
                    <X size={20} />
                </button>

                <Chat />
            </div>
        </div>
    );
};

export default Chatbot;
