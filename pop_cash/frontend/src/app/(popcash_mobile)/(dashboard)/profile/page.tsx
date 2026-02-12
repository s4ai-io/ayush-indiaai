'use client';

import React from 'react';
import {
    ChevronRight,
    Pencil,
    History,
    Gift,
    Landmark,
    CreditCard,
    ShoppingCart,
    List,
    MapPin,
    User as UserIcon
} from 'lucide-react';

const Profile = () => {
    return (
        <div className="bg-black text-white pb-32">
            {/* Header */}
            <header className="flex justify-between items-center px-4 py-6">
                <h1 className="text-lg font-medium tracking-wide">MY PROFILE</h1>
                <div className="flex items-center gap-1 bg-white/10 rounded-full px-3 py-1 border border-white/20">
                    <div className="w-4 h-4 rounded-full bg-red-500 flex items-center justify-center text-[10px] font-bold">P</div>
                    <span className="text-sm font-medium">536</span>
                </div>
            </header>

            <div className="px-4 space-y-8">
                {/* Profile Card */}
                <div className="bg-[#1c1c1e] rounded-3xl p-6 flex items-center gap-4 relative overflow-hidden">
                    <div className="relative">
                        <div className="w-16 h-16 rounded-full border-2 border-red-400 flex items-center justify-center bg-white/5">
                            <UserIcon size={32} className="text-red-400" />
                        </div>
                        <div className="absolute bottom-0 right-0 w-6 h-6 bg-red-400 rounded-full flex items-center justify-center border-2 border-[#1c1c1e]">
                            <Pencil size={12} className="text-white" />
                        </div>
                    </div>

                    <div>
                        <h2 className="text-xl font-bold mb-1">+919920610470</h2>
                        <div className="flex items-center gap-2 text-sm text-gray-400">
                            <span className="text-red-400 text-lg leading-none">+</span>
                            <span>Link your UPI ID & get bonus</span>
                            <div className="flex items-center gap-1">
                                <div className="w-3 h-3 rounded-full bg-red-500 flex items-center justify-center text-[8px] font-bold text-white">P</div>
                                <span className="text-white font-bold">50</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* My Rewards */}
                <div>
                    <h3 className="text-gray-400 font-medium mb-4 ml-1">My Rewards</h3>
                    <div className="bg-[#1c1c1e] rounded-2xl overflow-hidden">
                        <MenuItem
                            icon={<History size={20} className="text-yellow-500" />}
                            label="Cashback Zone"
                            textColor="text-yellow-500"
                        />
                        <MenuItem
                            icon={<div className="w-5 h-5 rounded-full border border-white flex items-center justify-center text-[10px] font-bold">P</div>}
                            label="POPcoins"
                        />
                        <MenuItem
                            icon={<Gift size={20} />}
                            label="UPI Rewards"
                        />
                    </div>
                </div>

                {/* My UPI */}
                <div>
                    <h3 className="text-gray-400 font-medium mb-4 ml-1">My UPI</h3>
                    <div className="bg-[#1c1c1e] rounded-2xl overflow-hidden">
                        <MenuItem
                            icon={<Landmark size={20} />}
                            label="Link Bank Account"
                            badge="50"
                        />
                        <MenuItem
                            icon={<CreditCard size={20} />}
                            label="Link RuPay Credit Card"
                            badge="1000"
                        />
                    </div>
                </div>

                {/* My Shopping */}
                <div>
                    <h3 className="text-gray-400 font-medium mb-4 ml-1">My Shopping</h3>
                    <div className="bg-[#1c1c1e] rounded-2xl overflow-hidden">
                        <MenuItem
                            icon={<ShoppingCart size={20} />}
                            label="Orders"
                        />
                        <MenuItem
                            icon={<List size={20} />}
                            label="Wishlist"
                        />
                        <MenuItem
                            icon={<MapPin size={20} />}
                            label="Saved Addresses"
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

const MenuItem = ({ icon, label, textColor = "text-white", badge }: { icon: React.ReactNode, label: string, textColor?: string, badge?: string }) => (
    <div className="flex items-center justify-between p-4 border-b border-white/5 last:border-0 active:bg-white/5 transition-colors cursor-pointer">
        <div className="flex items-center gap-4">
            <div className="text-gray-400">
                {icon}
            </div>
            <span className={`font-medium ${textColor}`}>{label}</span>
        </div>
        <div className="flex items-center gap-3">
            {badge && (
                <div className="flex items-center gap-1 bg-white/10 px-2 py-1 rounded-full border border-white/10">
                    <span className="text-xs text-gray-300">Get</span>
                    <div className="w-3 h-3 rounded-full bg-red-500 flex items-center justify-center text-[8px] font-bold text-white">P</div>
                    <span className="text-xs font-bold text-white">{badge}</span>
                </div>
            )}
            <ChevronRight size={18} className="text-gray-600" />
        </div>
    </div>
);

export default Profile;
