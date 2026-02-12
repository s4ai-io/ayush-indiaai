
import React from 'react';
import { FiClock, FiCreditCard, FiTrendingUp, FiAlertCircle } from "react-icons/fi";

interface BalanceData {
    user_id: string;
    total_popcoins_earned: number;
    total_popcoins_spent: number;
    current_balance: number;
    popcoins_expiring_soon: number;
    last_earned_date: string;
    last_updated: string;
}

export const BalanceCard = ({ data }: { data: BalanceData | any }) => {
    if (!data || typeof data !== 'object') return null;

    // Helper to format date if needed, or just use relevant part
    const formatDate = (dateStr: string) => {
        try {
            return new Date(dateStr).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            return dateStr;
        }
    };

    return (
        <div className="w-full bg-gradient-to-r from-neon-purple/15 via-neon-blue/10 to-neon-purple/15 backdrop-blur-md py-2 border-b border-white/10 rounded-xl">
            {/* Lean Status Bar Layout */}
            <div className="flex items-center justify-between px-4 gap-2">

                {/* Primary Balance */}
                <div className="flex items-center gap-1.5 min-w-0">
                    <FiCreditCard className="w-3.5 h-3.5 text-neon-purple shrink-0" />
                    <span className="font-bold text-md whitespace-nowrap">{data.current_balance?.toLocaleString()} <span className="text-[12px] text-gray-500 font-normal">P</span></span>
                </div>

                {/* Divider */}
                <div className="w-px h-3 bg-white/10 shrink-0"></div>

                {/* Lifetime Earned */}
                <div className="flex items-center gap-1 min-w-0" title="Lifetime Earned">
                    <FiTrendingUp className="w-3 h-3 text-neon-blue shrink-0" />
                    <div className="flex flex-col">
                        <span className="text-xs text-gray-400 leading-none uppercase">Earned</span>
                        <span className="font-bold text-md leading-tight">{data.total_popcoins_earned?.toLocaleString()}</span>
                    </div>
                </div>

                {/* Divider */}
                <div className="w-px h-3 bg-white/10 shrink-0"></div>

                {/* Expiring Soon */}
                <div className="flex items-center gap-1 min-w-0" title="Expiring Soon">
                    <FiAlertCircle className={`w-3 h-3 shrink-0 ${data.popcoins_expiring_soon > 0 ? "text-red-400" : "text-gray-500"}`} />
                    <div className="flex flex-col">
                        <span className="text-xs text-gray-400 leading-none uppercase">Expiry</span>
                        <span className={`font-bold text-md leading-tight ${data.popcoins_expiring_soon > 0 ? "text-red-300" : "text-gray-400"}`}>
                            {data.popcoins_expiring_soon?.toLocaleString() || 0}
                        </span>
                    </div>
                </div>

            </div>
        </div>
    );
};
