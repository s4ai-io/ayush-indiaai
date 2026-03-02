'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
// TODO: Wire up to real backend API (GET /api/ml/trends)
const diseaseTrendsData: Record<string, unknown>[] = [];

export function TrendChart() {
    return (
        <ResponsiveContainer width="100%" height={400}>
            <LineChart
                data={diseaseTrendsData}
                margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} vertical={false} />
                <XAxis
                    dataKey="month"
                    stroke="#888888"
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                />
                <YAxis
                    stroke="#888888"
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value) => `${value}`}
                />
                <Tooltip
                    contentStyle={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    itemStyle={{ color: '#1e293b', padding: 0 }}
                />
                <Legend wrapperStyle={{ paddingTop: '20px' }} />

                <Line type="monotone" dataKey="dengue" stroke="#ef4444" name="Dengue" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="flu" stroke="#f59e0b" name="Seasonal Flu" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="arthritis" stroke="#8b5cf6" name="Arthritis (Vata)" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="asthma" stroke="#10b981" name="Asthma (Kapha)" strokeWidth={2} dot={false} />
            </LineChart>
        </ResponsiveContainer>
    );
}
