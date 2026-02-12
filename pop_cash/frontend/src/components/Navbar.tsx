'use client';

import React, { useState } from 'react';
import { Home, ShoppingBag, ScanLine, CreditCard, User } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { twMerge } from 'tailwind-merge';
import ScanModal from './ScanModal';

const Navbar = () => {
    const pathname = usePathname();
    const [isScanModalOpen, setIsScanModalOpen] = useState(false);

    const navItems = [
        { icon: Home, label: 'Home', path: '/' },
        { icon: ShoppingBag, label: 'Shop', path: '/shop' },
        { icon: ScanLine, label: 'Scan & Pay', path: '/scan', isCenter: true },
        { icon: CreditCard, label: 'Card', path: '/wallet' },
        { icon: User, label: 'Profile', path: '/profile' },
    ];

    return (
        <>
            <div className="fixed bottom-0 left-0 right-0 z-50 pointer-events-none">
                <div className="w-full relative h-[100px] flex items-end">
                    {/* SVG Background */}
                    <div className="absolute bottom-0 left-0 w-full h-[100px] drop-shadow-[0_-5px_10px_rgba(0,0,0,0.5)] pointer-events-auto">
                        <svg viewBox="0 0 375 80" className="w-full h-full text-black fill-current" preserveAspectRatio="none">
                            <path d="M0,20 L138,20 C138,20 148,20 153,30 C162,48 172,60 187.5,60 C203,60 213,48 222,30 C227,20 237,20 237,20 L375,20 L375,80 L0,80 Z" />
                        </svg>
                    </div>

                    {/* Nav Items */}
                    <div className="relative z-10 w-full flex justify-between items-end px-2 pb-6 pointer-events-auto">
                        {navItems.map((item, index) => {
                            // Exact match for root, startsWith for others to handle sub-routes if any
                            const isActive = item.path === '/' ? pathname === '/' : pathname?.startsWith(item.path);

                            if (item.isCenter) {
                                return (
                                    <div key={index} className="flex flex-col items-center justify-end w-1/5 h-[100px] relative -top-2">
                                        <button
                                            onClick={() => setIsScanModalOpen(true)}
                                            className="w-16 h-16 rounded-full bg-[#1c1c1e] border-4 border-black flex items-center justify-center relative shadow-lg shadow-neon-purple/20 group cursor-pointer hover:shadow-neon-purple/40 transition-all active:scale-95"
                                        >
                                            <div className="absolute inset-0 rounded-full border border-white/20" />
                                            <ScanLine size={28} className="text-white group-hover:text-neon-purple transition-colors" />
                                            <div className="absolute -bottom-8 w-max">
                                                <span className="text-[10px] font-medium text-gray-400">{item.label}</span>
                                            </div>
                                        </button>
                                    </div>
                                );
                            }

                            return (
                                <Link
                                    key={index}
                                    href={item.path}
                                    className="flex flex-col items-center justify-center w-1/5 pb-0 gap-1 group"
                                >
                                    <item.icon
                                        size={24}
                                        strokeWidth={isActive ? 2.5 : 2}
                                        className={twMerge(
                                            "transition-colors duration-200",
                                            isActive ? "text-red-500" : "text-gray-400 group-hover:text-white"
                                        )}
                                    />
                                    <span className={twMerge(
                                        "text-[10px] font-medium transition-colors duration-200",
                                        isActive ? "text-red-500" : "text-gray-400 group-hover:text-white"
                                    )}>
                                        {item.label}
                                    </span>
                                </Link>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Scan Modal */}
            <ScanModal isOpen={isScanModalOpen} onClose={() => setIsScanModalOpen(false)} />
        </>
    );
};

export default Navbar;
