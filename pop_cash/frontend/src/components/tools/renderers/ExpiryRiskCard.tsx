
import React from 'react';
import { FiAlertTriangle, FiCalendar, FiShoppingBag, FiChevronRight, FiPercent } from "react-icons/fi";

interface RecommendedProduct {
    product_id: string | null;
    product_title: string;
    category: string | null;
    brand: string;
    mrp: number;
    selling_price: number;
    popcoins_required: number;
    savings_amount: number;
    savings_percentage: number;
    value_efficiency_score: number;
    user_can_afford: boolean;
    image_list: string[] | null;
}

interface ExpiryRiskData {
    user_id: string;
    total_at_risk: number;
    expiry_timeline: {
        next_7_days: number;
        "8_to_15_days": number;
        "16_to_30_days": number;
    };
    urgent_action_needed: boolean;
    days_until_first_expiry: number;
    expiring_entries_count: number;
    recommended_products: RecommendedProduct[];
}

export const ExpiryRiskCard = ({ data }: { data: ExpiryRiskData | any }) => {
    if (!data || typeof data !== 'object') return null;

    return (
        <div className="flex flex-col gap-3 w-full">
            {/* Risk Summary Status Bar */}
            <div className={`w-full bg-gradient-to-r from-red-500/20 via-orange-500/10 to-red-500/20 backdrop-blur-md py-3 px-4 border border-red-500/20 rounded-2xl`}>
                <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                        <div className="relative">
                            <FiAlertTriangle className={`w-5 h-5 ${data.urgent_action_needed ? "text-red-500 animate-pulse" : "text-orange-400"}`} />
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">At Risk</span>
                            <span className="text-lg font-bold text-white leading-none whitespace-nowrap">
                                {data.total_at_risk?.toLocaleString()} <span className="text-xs font-normal text-gray-400">P</span>
                            </span>
                        </div>
                    </div>

                    <div className="h-8 w-px bg-white/10 mx-1"></div>

                    <div className="flex flex-col flex-1 items-center">
                        <span className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">Expiring In</span>
                        <div className="flex items-center gap-1.5 mt-0.5">
                            <FiCalendar className="w-3.5 h-3.5 text-orange-400" />
                            <span className="text-sm font-bold text-white">
                                {Math.abs(data.days_until_first_expiry)} Days
                            </span>
                        </div>
                    </div>

                    <div className="h-8 w-px bg-white/10 mx-1"></div>

                    <div className="flex flex-col items-end">
                        <span className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">Txn Count</span>
                        <span className="text-sm font-bold text-white mt-0.5">
                            {data.expiring_entries_count} Txns
                        </span>
                    </div>
                </div>
            </div>

            {/* Timeline Breakdown (Compact) */}
            <div className="flex gap-2 w-full px-1">
                {Object.entries(data.expiry_timeline).map(([key, value]) => (
                    <div key={key} className="flex-1 bg-white/5 rounded-xl p-2 border border-white/5 flex flex-col items-center">
                        <span className="text-[8px] text-gray-500 uppercase font-bold text-center leading-none mb-1">
                            {key.replace(/_/g, ' ')}
                        </span>
                        <span className={`text-xs font-bold ${Number(value) > 0 ? 'text-red-400' : 'text-gray-600'}`}>
                            {Number(value).toLocaleString()}
                        </span>
                    </div>
                ))}
            </div>

            {/* Recommendations Section */}
            {data.recommended_products?.length > 0 && (
                <div className="flex flex-col gap-2 mt-1">
                    <div className="flex items-center justify-between px-1">
                        <h4 className="text-[10px] uppercase font-bold text-gray-500 tracking-widest flex items-center gap-1.5">
                            <FiShoppingBag className="text-neon-purple" /> Spend to Save
                        </h4>
                    </div>

                    <div className="flex flex-col gap-2">
                        {data.recommended_products.slice(0, 3).map((product: RecommendedProduct, idx: number) => (
                            <div key={idx} className="group bg-white/5 hover:bg-white/10 transition-all rounded-xl p-2.5 border border-white/5 hover:border-neon-purple/30 flex items-center gap-3 active:scale-98 cursor-pointer">
                                {/* Small Thumbnail / Placeholder */}
                                <div className="w-12 h-12 bg-white/10 rounded-lg flex items-center justify-center shrink-0 overflow-hidden border border-white/5">
                                    {product.image_list && product.image_list.length > 0 ? (
                                        <img src={product.image_list[0]} alt="" className="w-full h-full object-cover" />
                                    ) : (
                                        <FiShoppingBag className="text-gray-600 w-6 h-6" />
                                    )}
                                </div>

                                <div className="flex-1 min-w-0">
                                    <h5 className="text-xs font-semibold text-gray-200 truncate leading-snug">
                                        {product.product_title}
                                    </h5>
                                    <div className="flex items-center gap-2 mt-1">
                                        <span className="text-[10px] text-white font-bold">₹{product.selling_price}</span>
                                        <span className="text-[10px] text-gray-500 line-through">₹{product.mrp}</span>
                                        <div className="flex items-center gap-0.5 bg-green-500/10 px-1 rounded text-[9px] text-green-400 font-bold border border-green-500/20">
                                            <FiPercent size={8} />{Math.round(product.savings_percentage)}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex flex-col items-end shrink-0">
                                    <div className="text-[10px] font-bold text-neon-purple flex items-center gap-1">
                                        -{product.popcoins_required} <span className="text-[8px] font-normal opacity-70 italic">P</span>
                                    </div>
                                    <FiChevronRight className="text-gray-600 group-hover:text-neon-purple mt-1" />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
