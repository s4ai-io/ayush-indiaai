'use client';

import React from 'react';
import { AreaChart, Area, Tooltip, ResponsiveContainer } from 'recharts';

const data = [
    { name: 'Mon', amount: 4000 },
    { name: 'Tue', amount: 3000 },
    { name: 'Wed', amount: 2000 },
    { name: 'Thu', amount: 2780 },
    { name: 'Fri', amount: 1890 },
    { name: 'Sat', amount: 2390 },
    { name: 'Sun', amount: 3490 },
];

const Analytics = () => {
    return (
        <div className="space-y-8">
            <header>
                <h1 className="text-2xl font-bold mb-1">Analytics</h1>
                <p className="text-gray-400 text-sm">Track your financial activity</p>
            </header>

            {/* Spending Overview */}
            <div className="bg-card-bg border border-white/5 rounded-3xl p-6 relative overflow-hidden">
                <div className="flex justify-between items-end mb-6">
                    <div>
                        <p className="text-gray-400 text-sm mb-1">Total Spending</p>
                        <h2 className="text-3xl font-bold">$1,245.50</h2>
                    </div>
                    <select className="bg-white/5 border border-white/10 rounded-lg px-3 py-1 text-xs text-gray-300 outline-none">
                        <option>This Week</option>
                        <option>Last Week</option>
                        <option>This Month</option>
                    </select>
                </div>

                <div className="h-[200px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data}>
                            <defs>
                                <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#b026ff" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#b026ff" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                                itemStyle={{ color: '#fff' }}
                            />
                            <Area type="monotone" dataKey="amount" stroke="#b026ff" strokeWidth={3} fillOpacity={1} fill="url(#colorAmount)" />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Categories */}
            <div>
                <h3 className="text-lg font-bold mb-4">Spending by Category</h3>
                <div className="space-y-4">
                    {[
                        { name: 'Shopping', amount: '$450.00', percent: 45, color: 'bg-neon-purple' },
                        { name: 'Food & Drink', amount: '$320.50', percent: 30, color: 'bg-neon-pink' },
                        { name: 'Transport', amount: '$120.00', percent: 15, color: 'bg-neon-blue' },
                        { name: 'Entertainment', amount: '$355.00', percent: 10, color: 'bg-yellow-400' },
                    ].map((cat, i) => (
                        <div key={i} className="bg-card-bg border border-white/5 rounded-2xl p-4">
                            <div className="flex justify-between items-center mb-2">
                                <span className="font-medium text-sm">{cat.name}</span>
                                <span className="font-bold text-sm">{cat.amount}</span>
                            </div>
                            <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                                <div className={`h-full ${cat.color} rounded-full`} style={{ width: `${cat.percent}%` }} />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Analytics;
