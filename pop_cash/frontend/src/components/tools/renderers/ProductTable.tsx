import React from 'react';

export const ProductTable = ({ products }: { products: any[] }) => {
    if (!products || products.length === 0) return null;

    // Choose columns based on availability, prioritizing certain fields
    const hasSavings = products.some(p => p.savings_amount !== undefined);
    const hasPopcoins = products.some(p => p.popcoins_required !== undefined);
    const hasEfficiency = products.some(p => p.value_efficiency_score !== undefined);

    return (
        <div className="overflow-x-auto border border-white/10 rounded-xl mt-2 bg-card-bg/50 backdrop-blur-sm">
            <table className="min-w-full divide-y divide-white/10">
                <thead className="bg-white/5">
                    <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Product</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Price</th>
                        {hasPopcoins && <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">PopCoins</th>}
                        {hasSavings && <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Savings</th>}
                        {hasEfficiency && <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Score</th>}
                    </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                    {products.map((p, idx) => (
                        <tr key={idx} className="hover:bg-white/5 text-xs text-gray-200 transition-colors">
                            <td className="px-3 py-2 max-w-[150px] truncate" title={p.product_title || p.name}>
                                {p.product_title || p.name || `Product ${p.product_id}`}
                                {p.brand && <div className="text-[10px] text-gray-500">{p.brand}</div>}
                            </td>
                            <td className="px-3 py-2 whitespace-nowrap">
                                <div>₹{p.selling_price}</div>
                                {p.mrp && <div className="text-[10px] text-gray-500 line-through">₹{p.mrp}</div>}
                            </td>
                            {hasPopcoins && <td className="px-3 py-2 whitespace-nowrap font-medium text-neon-purple">{p.popcoins_required}</td>}
                            {hasSavings && <td className="px-3 py-2 whitespace-nowrap text-green-400">
                                <div>₹{p.savings_amount}</div>
                                {p.savings_percentage && <div className="text-[10px]">{p.savings_percentage.toFixed(0)}%</div>}
                            </td>}
                            {hasEfficiency && <td className="px-3 py-2 whitespace-nowrap text-neon-blue">{p.value_efficiency_score?.toFixed(2)}</td>}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
