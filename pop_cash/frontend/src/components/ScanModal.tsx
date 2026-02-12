'use client';

import React from 'react';
import { X, ScanLine, Flashlight, RotateCw, Image as ImageIcon } from 'lucide-react';

interface ScanModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const ScanModal = ({ isOpen, onClose }: ScanModalProps) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/95 backdrop-blur-sm">
            {/* Modal Container */}
            <div className="relative w-full h-full max-w-lg flex flex-col bg-dark-bg">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-gradient-to-r from-neon-purple/10 to-neon-blue/10">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-neon-purple/20 border border-neon-purple/30">
                            <ScanLine className="text-neon-purple" size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">Scan & Pay</h2>
                            <p className="text-xs text-gray-400">Align QR code within the frame</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-full bg-white/5 hover:bg-white/10 transition-colors text-white"
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* Camera View */}
                <div className="flex-1 relative overflow-hidden bg-gradient-to-br from-gray-900 to-black">
                    {/* Simulated Camera Feed with Grid Pattern */}
                    <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAwIDEwIEwgNDAgMTAgTSAxMCAwIEwgMTAgNDAgTSAwIDIwIEwgNDAgMjAgTSAyMCAwIEwgMjAgNDAgTSAwIDMwIEwgNDAgMzAgTSAzMCAwIEwgMzAgNDAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjAzKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIiAvPjwvc3ZnPg==')] opacity-50"></div>

                    {/* Scanning Frame */}
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="relative w-72 h-72">
                            {/* Corner Borders */}
                            <div className="absolute top-0 left-0 w-16 h-16 border-t-4 border-l-4 border-neon-purple rounded-tl-2xl"></div>
                            <div className="absolute top-0 right-0 w-16 h-16 border-t-4 border-r-4 border-neon-purple rounded-tr-2xl"></div>
                            <div className="absolute bottom-0 left-0 w-16 h-16 border-b-4 border-l-4 border-neon-purple rounded-bl-2xl"></div>
                            <div className="absolute bottom-0 right-0 w-16 h-16 border-b-4 border-r-4 border-neon-purple rounded-br-2xl"></div>

                            {/* Scanning Line Animation */}
                            <div className="absolute inset-0 overflow-hidden">
                                <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-neon-blue to-transparent animate-scan shadow-[0_0_10px_rgba(38,240,255,0.8)]"></div>
                            </div>

                            {/* Glow Effect */}
                            <div className="absolute inset-0 bg-neon-purple/5 rounded-2xl blur-xl"></div>
                        </div>
                    </div>

                    {/* Overlay Gradient */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/80 pointer-events-none"></div>
                </div>

                {/* Bottom Controls */}
                <div className="px-6 py-6 bg-gradient-to-t from-black to-card-bg border-t border-white/10">
                    <div className="flex items-center justify-around gap-4 mb-4">
                        {/* Flash */}
                        <button className="flex flex-col items-center gap-2 p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors border border-white/10 w-full">
                            <Flashlight className="text-neon-blue" size={24} />
                            <span className="text-xs text-gray-400">Flash</span>
                        </button>

                        {/* Rotate Camera */}
                        <button className="flex flex-col items-center gap-2 p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors border border-white/10 w-full">
                            <RotateCw className="text-neon-purple" size={24} />
                            <span className="text-xs text-gray-400">Flip</span>
                        </button>

                        {/* Gallery */}
                        <button className="flex flex-col items-center gap-2 p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors border border-white/10 w-full">
                            <ImageIcon className="text-neon-pink" size={24} />
                            <span className="text-xs text-gray-400">Gallery</span>
                        </button>
                    </div>

                    {/* Info Text */}
                    <div className="text-center">
                        <p className="text-sm text-gray-400 mb-1">Position the QR code within the frame</p>
                        <p className="text-xs text-gray-500">The code will be scanned automatically</p>
                    </div>
                </div>
            </div>

            {/* Custom CSS for scanning animation */}
            <style jsx>{`
                @keyframes scan {
                    0%, 100% {
                        top: 0;
                        opacity: 0;
                    }
                    10% {
                        opacity: 1;
                    }
                    90% {
                        opacity: 1;
                    }
                    100% {
                        top: 100%;
                        opacity: 0;
                    }
                }
                .animate-scan {
                    animation: scan 2s ease-in-out infinite;
                }
            `}</style>
        </div>
    );
};

export default ScanModal;
