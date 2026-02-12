'use client';

import React from 'react';
import { Search, ShoppingCart, ScanLine, ChevronRight, ArrowRight } from 'lucide-react';

const Home = () => {
    return (
        <div className="bg-black text-white pb-32">


            <div className="space-y-8 pt-4 pb-8">
                {/* UPI Banner */}
                <div className="px-4">
                    <div className="w-full h-32 rounded-2xl bg-gradient-to-r from-blue-900 to-black border border-white/10 relative overflow-hidden flex items-center justify-between p-6">
                        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1614850523459-c2f4c699c52e?q=80&w=2070&auto=format&fit=crop')] opacity-20 bg-cover bg-center" />
                        <div className="relative z-10 max-w-[60%]">
                            <h2 className="text-lg font-bold leading-tight mb-1">Make your first POP UPI transaction and get bonus</h2>
                            <div className="flex items-center gap-2">
                                <div className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center text-xs font-bold">P</div>
                                <span className="text-3xl font-bold">100</span>
                            </div>
                        </div>
                        <button className="relative z-10 bg-white text-black px-4 py-2 rounded-lg font-bold text-xs flex items-center gap-1">
                            PAY NOW <ChevronRight size={14} />
                        </button>
                    </div>
                </div>

                {/* Blackout Promo Card */}
                <div className="px-4">
                    <div className="mb-2">
                        <h3 className="text-sm font-medium text-gray-300 uppercase tracking-wider">PAY WITH POP UPI</h3>
                        <p className="text-gray-400 text-sm">Shop & save with POPcoins!</p>
                    </div>
                    <div className="w-full aspect-[16/9] bg-[#8B5CF6] rounded-2xl border-2 border-[#A78BFA] p-6 relative overflow-hidden">
                        <div className="absolute top-4 right-4 bg-[#FDBA74] text-[#C2410C] px-3 py-1 rounded-lg transform rotate-12 border-2 border-[#FB923C]">
                            <div className="text-[10px] font-bold leading-none">UP TO</div>
                            <div className="text-xl font-black leading-none">90% OFF</div>
                            <div className="text-[10px] font-bold leading-none">WITH POPCOINS</div>
                        </div>

                        <h2 className="text-3xl font-black text-[#D1FAE5] leading-none mb-1">Prepare for</h2>
                        <h2 className="text-3xl font-black text-[#D1FAE5] leading-none mb-1">a full-scale</h2>
                        <h2 className="text-3xl font-black text-[#D1FAE5] leading-none mb-6">blackout.</h2>

                        <div className="flex gap-3 mb-6">
                            {['bewakoof', 'nike', 'yogabar', 'boat'].map((brand, i) => (
                                <div key={i} className="bg-white rounded px-2 py-1 h-8 flex items-center justify-center">
                                    <span className="text-black font-bold text-xs">{brand}</span>
                                </div>
                            ))}
                        </div>

                        <div className="w-full bg-white/20 h-2 rounded-full mb-2">
                            <div className="w-2/3 h-full bg-[#2DD4BF] rounded-full relative">
                                <div className="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-4 bg-[#2DD4BF] rounded-full shadow-lg" />
                            </div>
                        </div>

                        <div className="flex justify-between items-center">
                            <div className="text-white font-bold text-sm">27 NOVEMBER AT 6PM</div>
                            <div className="w-8 h-8 rounded-full bg-[#D1FAE5] flex items-center justify-center">
                                <ChevronRight size={20} className="text-black" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Know Your POP */}
                <div className="px-4">
                    <div className="mb-4">
                        <h3 className="text-sm font-medium text-gray-300 uppercase tracking-wider">KNOW YOUR POP</h3>
                        <p className="text-gray-400 text-sm">Everything you need in one POP!</p>
                    </div>

                    <div className="grid grid-cols-3 gap-3">
                        {[
                            { icon: ShoppingCart, label: 'Shop', badge: 'Get ₹ 1000' },
                            { icon: ScanLine, label: 'Scan & Pay', badge: 'Get 2% POPcoins', highlight: true },
                            { icon: ArrowRight, label: 'Send Money', badge: null }
                        ].map((item, i) => (
                            <div key={i} className="aspect-square rounded-2xl bg-[#1c1c1e] border border-white/10 flex flex-col items-center justify-center relative overflow-hidden group">
                                {item.highlight && (
                                    <div className="absolute top-0 inset-x-0 bg-orange-500 text-black text-[10px] font-bold text-center py-1">
                                        {item.badge}
                                    </div>
                                )}
                                <item.icon size={32} className="text-white mb-2" />
                                <span className="text-sm font-medium text-gray-300">{item.label}</span>
                                {!item.highlight && item.badge && (
                                    <div className="absolute bottom-0 inset-x-0 bg-orange-500 text-black text-[10px] font-bold text-center py-1 translate-y-full group-hover:translate-y-0 transition-transform">
                                        {item.badge}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* First Purchase Deal */}
                <div className="px-4">
                    <div className="w-full h-24 rounded-2xl bg-gradient-to-r from-orange-500 via-pink-500 to-purple-600 flex items-center justify-between p-4 relative overflow-hidden">
                        <div className="relative z-10">
                            <div className="text-xs font-bold text-white/80 uppercase tracking-wider mb-1">FIRST-TIME BUYER BONUS</div>
                            <div className="text-xl font-bold text-white leading-tight">Special price just for you!</div>
                        </div>
                    </div>
                </div>

                {/* Daily Drops */}
                <div className="px-4">
                    <div className="mb-4">
                        <h3 className="text-sm font-medium text-gray-300 uppercase tracking-wider">FIRST PURCHASE SPECIAL DEAL</h3>
                        <p className="text-gray-400 text-sm">Get exclusive discounts on your first shop</p>
                    </div>

                    <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide">
                        {/* Card 1 */}
                        <div className="min-w-[85%] aspect-[16/9] bg-[#1c1c1e] rounded-2xl relative overflow-hidden group">
                            <img src="https://images.unsplash.com/photo-1515955656352-a1fa3ffcd111?q=80&w=2070&auto=format&fit=crop" className="absolute inset-0 w-full h-full object-cover opacity-50" />
                            <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent" />
                            <div className="absolute bottom-4 left-4">
                                <h3 className="text-2xl font-black text-white uppercase italic">DAILY DROPS</h3>
                                <p className="text-gray-300 text-sm mb-3">Premium deals refreshed daily</p>
                                <button className="bg-white/20 backdrop-blur-md border border-white/30 text-white px-4 py-2 rounded-full text-sm font-bold flex items-center gap-2">
                                    Shop now <ArrowRight size={14} />
                                </button>
                            </div>
                        </div>
                        {/* Card 2 */}
                        <div className="min-w-[85%] aspect-[16/9] bg-[#1c1c1e] rounded-2xl relative overflow-hidden">
                            <div className="absolute inset-0 bg-gradient-to-br from-pink-900 to-purple-900" />
                            <div className="absolute inset-0 flex flex-col justify-center p-6">
                                <h3 className="text-2xl font-bold text-white mb-2">Win ₹500</h3>
                                <h3 className="text-xl text-white mb-4">Zomato Voucher</h3>
                                <button className="bg-red-600 text-white px-4 py-2 rounded-full text-sm font-bold w-max">
                                    Know More
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Grand Picks */}
                <div className="px-4">
                    <div className="mb-4">
                        <h3 className="text-sm font-medium text-gray-300 uppercase tracking-wider">POP GRAND PICKS</h3>
                        <p className="text-gray-400 text-sm">Exclusive deals. Exclusive drops.</p>
                    </div>

                    <div className="grid grid-cols-4 gap-3">
                        {[
                            { name: 'Men', img: '/category-men.png' },
                            { name: 'Women', img: 'https://images.unsplash.com/photo-1525845859779-54d477ff291f?q=80&w=1000&auto=format&fit=crop' },
                            { name: 'Food', img: 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=1000&auto=format&fit=crop' },
                            { name: 'Care', img: '/category-care.png' },
                            { name: 'Footwear', img: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=1000&auto=format&fit=crop' },
                            { name: 'Tech', img: 'https://images.unsplash.com/photo-1519389950473-47ba0277781c?q=80&w=1000&auto=format&fit=crop' },
                            { name: 'Home', img: 'https://images.unsplash.com/photo-1484101403633-562f891dc89a?q=80&w=1000&auto=format&fit=crop' },
                            { name: 'Sports', img: 'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?q=80&w=1000&auto=format&fit=crop' },
                        ].map((cat, i) => (
                            <div key={i} className="flex flex-col items-center gap-2">
                                <div className="w-full aspect-square rounded-2xl overflow-hidden border border-white/10 relative group">
                                    <img src={cat.img} alt={cat.name} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
                                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                                </div>
                                <span className="text-xs font-medium text-gray-300">{cat.name}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Home;
