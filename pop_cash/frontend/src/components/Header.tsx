'use client';

import React from 'react';
import { Search, ShoppingCart, ScanLine, Sparkles, MessageCircle } from 'lucide-react';
import { useChat } from '../context/ChatContext';

const Header = () => {
    const { toggleChat } = useChat();

    return (
        <header className="flex justify-between items-center px-6 py-4 sticky top-0 bg-dark-bg/80 backdrop-blur-md z-40 border-b border-white/5">
            <div className="text-2xl font-black tracking-tighter text-white">
                pop
            </div>
            <div className="flex items-center gap-4">
                <Search size={24} className="text-white" />

                <ScanLine size={24} className="text-white" />
                <div className="flex items-center gap-1 bg-white/10 rounded-full px-3 py-1 border border-white/20">
                    <div className="w-4 h-4 rounded-full bg-red-500 flex items-center justify-center text-[10px] font-bold">P</div>
                    <span className="text-sm font-medium">536</span>
                </div>
                <ShoppingCart size={24} className="text-white" />
                <button
                    onClick={toggleChat}
                    className="relative group transition-all duration-300 hover:scale-110 hover:rotate-6 p-2 rounded-full hover:bg-neon-purple/10"
                >
                    {/* Glowing background effect */}
                    <div className="absolute inset-0 rounded-full bg-neon-blue/20 blur-md group-hover:bg-neon-purple/30 transition-all duration-300 animate-pulse"></div>

                    {/* Icon with glow */}
                    <MessageCircle
                        size={24}
                        className="relative text-neon-blue group-hover:text-neon-purple transition-colors duration-300 drop-shadow-[0_0_8px_rgba(38,240,255,0.6)] group-hover:drop-shadow-[0_0_12px_rgba(176,38,255,0.8)]"
                    />

                    {/* Pulsating sparkle indicator */}
                    <div className="absolute -top-0 -right-1 pointer-events-none scale-125">
                        <div className="relative">
                            <Sparkles
                                size={12}
                                className="text-neon-purple animate-pulse drop-shadow-[0_0_5px_rgba(250,204,21,0.8)]"
                            />
                            <div className="absolute inset-0 bg-neon-purple/20 blur-[2px] rounded-full animate-ping"></div>
                        </div>
                    </div>
                </button>
            </div>
        </header>
    );
};

export default Header;
