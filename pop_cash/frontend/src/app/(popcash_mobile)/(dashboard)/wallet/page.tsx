'use client';

import React from 'react';
import { Plus, CreditCard, Smartphone, Wifi } from 'lucide-react';

const Wallet = () => {
    return (
        <div className="space-y-8">
            <header className="flex justify-between items-center">
                <h1 className="text-2xl font-bold">My Wallet</h1>
                <button className="w-10 h-10 rounded-full bg-neon-purple/20 text-neon-purple flex items-center justify-center border border-neon-purple/50 hover:bg-neon-purple/30 transition-colors">
                    <Plus size={20} />
                </button>
            </header>

            {/* Cards Carousel (Simplified as stacked for now) */}
            <div className="relative h-48 w-full">
                {/* Back Card */}
                <div className="absolute top-0 left-4 right-4 h-48 bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl transform scale-95 translate-y-4 opacity-50 border border-white/5" />

                {/* Front Card */}
                <div className="absolute top-0 left-0 right-0 h-48 bg-gradient-to-br from-neon-blue/20 to-neon-purple/20 backdrop-blur-xl border border-white/10 rounded-2xl p-6 flex flex-col justify-between overflow-hidden">
                    <div className="absolute top-0 right-0 w-40 h-40 bg-neon-blue/20 blur-[50px] rounded-full pointer-events-none" />

                    <div className="flex justify-between items-start relative z-10">
                        <div className="text-sm font-semibold tracking-wider text-gray-300">POPCASH</div>
                        <Wifi size={24} className="rotate-90 text-gray-400" />
                    </div>

                    <div className="relative z-10">
                        <div className="text-2xl font-mono tracking-widest mb-2">•••• •••• •••• 4289</div>
                        <div className="flex justify-between items-end">
                            <div>
                                <div className="text-[10px] text-gray-400 uppercase mb-1">Card Holder</div>
                                <div className="font-medium">ALEX JOHNSON</div>
                            </div>
                            <div className="flex flex-col items-end">
                                <div className="text-[10px] text-gray-400 uppercase mb-1">Expires</div>
                                <div className="font-medium">09/28</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Payment Methods */}
            <div>
                <h3 className="text-lg font-bold mb-4">Payment Methods</h3>
                <div className="space-y-3">
                    <div className="flex items-center justify-between p-4 rounded-2xl bg-card-bg border border-white/5 hover:border-neon-purple/30 transition-colors cursor-pointer">
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center">
                                <CreditCard size={20} className="text-neon-pink" />
                            </div>
                            <div>
                                <h4 className="font-bold text-sm">Virtual Card</h4>
                                <p className="text-xs text-gray-400">Default •••• 4289</p>
                            </div>
                        </div>
                        <div className="w-4 h-4 rounded-full border border-neon-purple bg-neon-purple shadow-[0_0_10px_rgba(176,38,255,0.5)]" />
                    </div>

                    <div className="flex items-center justify-between p-4 rounded-2xl bg-card-bg border border-white/5 hover:border-neon-purple/30 transition-colors cursor-pointer">
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center">
                                <Smartphone size={20} className="text-neon-blue" />
                            </div>
                            <div>
                                <h4 className="font-bold text-sm">Apple Pay</h4>
                                <p className="text-xs text-gray-400">Connected</p>
                            </div>
                        </div>
                        <div className="w-4 h-4 rounded-full border border-gray-600" />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Wallet;
