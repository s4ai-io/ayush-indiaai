'use client';

import React from 'react';
import { ChevronRight, ArrowRight, Star } from 'lucide-react';

const Shop = () => {
    return (
        <div className="bg-black text-white pb-32">
            <div className="space-y-8 pt-4 pb-8">
                {/* First Purchase Special Deal Banner */}
                <div className="px-4">
                    <div className="w-full h-12 rounded-2xl bg-gradient-to-r from-orange-500 via-pink-500 to-purple-600 flex items-center justify-center relative overflow-hidden">
                        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1607083206968-13611e3d76db?q=80&w=2070')] opacity-10 bg-cover bg-center" />
                        <p className="relative z-10 text-sm font-bold text-white">Special price just for you!</p>
                    </div>
                </div>

                {/* First Purchase Special Deal Section */}
                <div className="px-4">
                    <div className="mb-3">
                        <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider">FIRST PURCHASE SPECIAL DEAL</h3>
                        <p className="text-gray-500 text-xs">Get exclusive offers on your first shop</p>
                    </div>
                </div>

                {/* POP Daily Drops */}
                <div className="px-4">
                    <div className="mb-4">
                        <h3 className="text-sm font-medium text-white uppercase tracking-wider flex items-center gap-2">
                            <span className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center text-xs font-bold">P</span>
                            POP
                        </h3>
                        <h2 className="text-2xl font-black text-white uppercase mt-1">DAILY DROPS</h2>
                        <p className="text-gray-400 text-sm">Premium deals refreshed daily</p>
                    </div>

                    <div className="w-full aspect-[16/9] bg-gradient-to-br from-red-900 via-red-800 to-black rounded-2xl relative overflow-hidden border border-white/10">
                        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1607083206325-caf1edba7a0f?q=80&w=2070')] opacity-30 bg-cover bg-center" />

                        {/* Product images scattered */}
                        <div className="absolute top-4 left-4 w-20 h-20 rounded-xl overflow-hidden border-2 border-white/20 rotate-[-12deg] shadow-xl">
                            <img src="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=200" className="w-full h-full object-cover" alt="Product" />
                        </div>
                        <div className="absolute top-8 right-8 w-24 h-24 rounded-xl overflow-hidden border-2 border-white/20 rotate-[8deg] shadow-xl">
                            <img src="https://images.unsplash.com/photo-1572635196237-14b3f281503f?q=80&w=200" className="w-full h-full object-cover" alt="Product" />
                        </div>
                        <div className="absolute bottom-20 left-8 w-16 h-16 rounded-xl overflow-hidden border-2 border-white/20 rotate-[15deg] shadow-xl">
                            <img src="https://images.unsplash.com/photo-1523275335684-37898b6baf30?q=80&w=200" className="w-full h-full object-cover" alt="Product" />
                        </div>

                        <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between">
                            <div>
                                <p className="text-white/80 text-xs mb-1">Limited time offers</p>
                                <h3 className="text-xl font-bold text-white">Shop All</h3>
                            </div>
                            <button className="bg-neon-pink hover:bg-neon-purple transition-colors px-5 py-2 rounded-full font-bold text-sm flex items-center gap-2">
                                Shop All <ArrowRight size={14} />
                            </button>
                        </div>
                    </div>
                </div>

                {/* New Year Wishlist */}
                <div className="px-4">
                    <div className="mb-4">
                        <h3 className="text-sm font-medium text-gray-300 uppercase tracking-wider">NEW YEAR WISHLIST</h3>
                        <p className="text-gray-400 text-sm">First essentials for all your needs</p>
                    </div>

                    <div className="flex gap-3 overflow-x-auto pb-4 scrollbar-hide">
                        {[
                            { name: "Men's Fashion", img: '/category-men.png' },
                            { name: "Women's Fashion", img: 'https://images.unsplash.com/photo-1525845859779-54d477ff291f?q=80&w=400' },
                            { name: 'Footwear', img: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=400' },
                            { name: 'Electronics', img: 'https://images.unsplash.com/photo-1519389950473-47ba0277781c?q=80&w=400' },
                            { name: 'Personal Care', img: '/category-care.png' },
                            { name: 'Food', img: 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=400' },
                            { name: 'Home & Living', img: 'https://images.unsplash.com/photo-1484101403633-562f891dc89a?q=80&w=400' },
                            { name: 'Make Up', img: 'https://images.unsplash.com/photo-1596462502278-27bfdd403348?q=80&w=400' },
                            { name: 'Sports corner', img: 'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?q=80&w=400' },
                        ].map((cat, i) => (
                            <div key={i} className="min-w-[120px] flex-shrink-0">
                                <div className="w-full aspect-square rounded-2xl overflow-hidden border border-white/10 relative group mb-2">
                                    <img src={cat.img} alt={cat.name} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
                                    <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
                                </div>
                                <p className="text-xs font-medium text-gray-300 text-center">{cat.name}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Brand of the Day */}
                <div className="px-4">
                    <div className="mb-4">
                        <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider">TODAY'S FEATURED BRAND</h3>
                        <h2 className="text-2xl font-black text-white uppercase mt-1">BRAND OF THE DAY</h2>
                    </div>

                    <div className="w-full aspect-[16/9] bg-gradient-to-br from-amber-900 via-yellow-800 to-black rounded-2xl relative overflow-hidden border border-amber-500/20">
                        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=2070')] opacity-20 bg-cover bg-center" />

                        {/* Discount Badge */}
                        <div className="absolute top-4 right-4 bg-red-600 text-white px-4 py-2 rounded-xl shadow-xl">
                            <div className="text-xs font-bold">Upto</div>
                            <div className="text-3xl font-black leading-none">65% off</div>
                        </div>

                        {/* Brand Logo */}
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white/10 backdrop-blur-md px-8 py-6 rounded-2xl border border-white/20">
                            <h2 className="text-5xl font-black text-white tracking-wider">MIVI</h2>
                        </div>

                        <div className="absolute bottom-4 left-4 right-4">
                            <button className="w-full bg-white text-black px-4 py-3 rounded-xl font-bold text-sm flex items-center justify-center gap-2 hover:bg-gray-100 transition-colors">
                                Explore Brand <ChevronRight size={16} />
                            </button>
                        </div>
                    </div>
                </div>

                {/* POP Forward 2025 */}
                <div className="px-4">
                    <div className="mb-4">
                        <div className="flex items-center gap-2 mb-1">
                            <span className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center text-xs font-bold">P</span>
                            <h3 className="text-sm font-medium text-white uppercase tracking-wider">POP FORWARD 2025</h3>
                            <span className="text-yellow-400">🎯</span>
                        </div>
                        <p className="text-gray-400 text-sm">Stay ahead throughout the year</p>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        {/* Top Tech 2025 */}
                        <div className="aspect-square bg-gradient-to-br from-blue-900 to-black rounded-2xl relative overflow-hidden border border-blue-500/20 p-4 flex flex-col justify-between">
                            <div className="absolute top-2 right-2 bg-red-600 text-white px-2 py-1 rounded-lg text-xs font-bold">
                                90%
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white mb-1">Top Tech 2025</h3>
                                <p className="text-xs text-gray-400">Latest gadgets</p>
                            </div>
                            <div className="flex gap-1">
                                {[1, 2].map((i) => (
                                    <div key={i} className="w-12 h-12 rounded-lg bg-white/10 border border-white/20" />
                                ))}
                            </div>
                        </div>

                        {/* Fuel New Goals */}
                        <div className="aspect-square bg-gradient-to-br from-purple-900 to-black rounded-2xl relative overflow-hidden border border-purple-500/20 p-4 flex flex-col justify-between">
                            <div className="absolute top-2 right-2 bg-purple-600 text-white px-2 py-1 rounded-lg text-xs font-bold">
                                65% off
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white mb-1">Fuel New Goals</h3>
                                <p className="text-xs text-gray-400">Health supplements</p>
                            </div>
                            <div className="flex gap-1">
                                {[1, 2].map((i) => (
                                    <div key={i} className="w-12 h-12 rounded-lg bg-white/10 border border-white/20" />
                                ))}
                            </div>
                        </div>

                        {/* Home Essentials 2025 */}
                        <div className="aspect-square bg-gradient-to-br from-red-900 to-black rounded-2xl relative overflow-hidden border border-red-500/20 p-4 flex flex-col justify-between">
                            <div>
                                <h3 className="text-lg font-bold text-white mb-1">Home Essentials 2025</h3>
                                <p className="text-xs text-gray-400">New Year New Vibes</p>
                            </div>
                            <div className="w-full h-12 rounded-lg bg-white/10 border border-white/20" />
                        </div>

                        {/* Glow into Refresh 2026 */}
                        <div className="aspect-square bg-gradient-to-br from-pink-900 to-black rounded-2xl relative overflow-hidden border border-pink-500/20 p-4 flex flex-col justify-between">
                            <div className="absolute top-2 right-2 bg-pink-600 text-white px-2 py-1 rounded-lg text-xs font-bold">
                                70% off
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white mb-1">Glow into Refresh 2026</h3>
                                <p className="text-xs text-gray-400">Self-care products</p>
                            </div>
                        </div>

                        {/* Step into Comfort */}
                        <div className="aspect-square bg-gradient-to-br from-slate-900 to-black rounded-2xl relative overflow-hidden border border-slate-500/20 p-4 flex flex-col justify-between">
                            <div className="absolute top-2 right-2 bg-green-600 text-white px-2 py-1 rounded-lg text-xs font-bold">
                                95%
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white mb-1">Step into Comfort</h3>
                                <p className="text-xs text-gray-400">New Year New Steps</p>
                            </div>
                            <div className="w-full h-12 rounded-lg bg-white/10 border border-white/20" />
                        </div>

                        {/* Starting from ₹29 */}
                        <div className="aspect-square bg-gradient-to-br from-teal-900 to-black rounded-2xl relative overflow-hidden border border-teal-500/20 p-4 flex flex-col justify-between">
                            <div>
                                <h3 className="text-2xl font-black text-white mb-1">Starting from</h3>
                                <p className="text-3xl font-black text-teal-400">₹29</p>
                            </div>
                            <div className="flex gap-1">
                                {[1, 2].map((i) => (
                                    <div key={i} className="w-12 h-12 rounded-lg bg-white/10 border border-white/20" />
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Shop;
