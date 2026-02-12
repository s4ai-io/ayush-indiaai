
import React from 'react';
import { FiShoppingCart, FiClock, FiAlertCircle, FiCheckCircle, FiChevronRight, FiTrendingUp } from "react-icons/fi";

interface CartItem {
    cart_id: string;
    product_title: string;
    quantity: number;
    price: number;
    age_hours: number;
    price_changed: boolean;
    is_available: boolean;
}

interface CartAbandonmentData {
    has_abandoned_items: boolean;
    cart_item_count: number;
    oldest_item_age_hours?: number;
    total_cart_value?: number;
    popcoins_required?: number;
    price_changes_detected?: boolean;
    availability_issues?: number;
    items?: CartItem[];
    recommendation?: string;
    message?: string;
}

export const CartRecoveryCard = ({ data }: { data: CartAbandonmentData | any }) => {
    if (!data || typeof data !== 'object') return null;

    if (!data.has_abandoned_items) {
        return (
            <div className="w-full bg-white/5 backdrop-blur-md p-4 rounded-2xl border border-white/10 flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-green-500/10 flex items-center justify-center border border-green-500/20">
                    <FiCheckCircle className="text-green-500 w-5 h-5" />
                </div>
                <div>
                    <h4 className="text-sm font-bold text-white">Cart is clean!</h4>
                    <p className="text-xs text-gray-400">{data.message || "No abandoned items found."}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-3 w-full">
            {/* Status Header */}
            <div className="w-full bg-gradient-to-r from-yellow-500/20 via-orange-500/10 to-yellow-500/20 backdrop-blur-md py-3 px-4 border border-yellow-500/20 rounded-2xl">
                <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                        <div className="relative">
                            <FiShoppingCart className="w-5 h-5 text-yellow-500" />
                            {data.cart_item_count > 0 && (
                                <span className="absolute -top-1 -right-1 bg-yellow-500 text-black text-[8px] font-bold w-3.5 h-3.5 rounded-full flex items-center justify-center border-2 border-black/50">
                                    {data.cart_item_count}
                                </span>
                            )}
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">In Cart</span>
                            <span className="text-lg font-bold text-white leading-none whitespace-nowrap">
                                ₹{data.total_cart_value?.toLocaleString()}
                            </span>
                        </div>
                    </div>

                    <div className="h-8 w-px bg-white/10 mx-1"></div>

                    <div className="flex flex-col flex-1 items-center">
                        <span className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">Oldest Item</span>
                        <div className="flex items-center gap-1.5 mt-0.5">
                            <FiClock className="w-3.5 h-3.5 text-orange-400" />
                            <span className="text-sm font-bold text-white">
                                {data.oldest_item_age_hours}h
                            </span>
                        </div>
                    </div>

                    <div className="h-8 w-px bg-white/10 mx-1"></div>

                    <div className="flex flex-col items-end">
                        <span className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">Coins Req.</span>
                        <span className="text-sm font-bold text-neon-purple mt-0.5">
                            {data.popcoins_required} <span className="text-[10px] font-normal opacity-70">P</span>
                        </span>
                    </div>
                </div>
            </div>

            {/* Notification/Alert */}
            {data.recommendation && (
                <div className="bg-yellow-500/10 border border-yellow-500/20 p-2.5 rounded-xl flex items-start gap-2.5">
                    <FiAlertCircle className="text-yellow-500 w-4 h-4 mt-0.5 shrink-0" />
                    <p className="text-xs text-yellow-200/90 leading-snug">{data.recommendation}</p>
                </div>
            )}

            {/* Cart Items List (Compact) */}
            {data.items && data.items.length > 0 && (
                <div className="flex flex-col gap-2">
                    {data.items.slice(0, 3).map((item: CartItem, idx: number) => (
                        <div key={idx} className="group bg-white/5 hover:bg-white/10 transition-all rounded-xl p-3 border border-white/5 hover:border-yellow-500/30 flex items-center gap-3 cursor-pointer">
                            <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center shrink-0 border border-white/5">
                                <FiShoppingCart className="text-gray-500 w-5 h-5" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <h5 className="text-xs font-semibold text-gray-200 truncate">{item.product_title}</h5>
                                <div className="flex items-center gap-3 mt-1">
                                    <span className="text-[10px] text-white font-bold">₹{item.price}</span>
                                    <span className="text-[10px] text-gray-500">Qty: {item.quantity}</span>
                                    {item.price_changed && (
                                        <span className="flex items-center gap-0.5 text-[9px] text-orange-400 font-bold bg-orange-400/10 px-1 rounded border border-orange-400/20">
                                            <FiTrendingUp size={8} /> Price Alert
                                        </span>
                                    )}
                                </div>
                            </div>
                            <FiChevronRight className="text-gray-600 group-hover:text-yellow-500 shrink-0" />
                        </div>
                    ))}
                    {data.items.length > 3 && (
                        <button className="text-[10px] font-bold text-yellow-500/70 hover:text-yellow-500 uppercase tracking-widest text-center py-1">
                            + {data.items.length - 3} More Items
                        </button>
                    )}
                </div>
            )}
        </div>
    );
};
