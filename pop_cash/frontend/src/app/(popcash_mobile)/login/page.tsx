'use client';

import React from 'react';
import { useRouter } from 'next/navigation';

const Login = () => {
    const router = useRouter();

    const handleLogin = (e: React.FormEvent) => {
        e.preventDefault();
        router.push('/');
    };

    return (
        <div className="min-h-screen bg-dark-bg text-white flex flex-col items-center justify-center p-6 relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] bg-neon-purple/20 rounded-full blur-[120px] pointer-events-none" />
            <div className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] bg-neon-blue/20 rounded-full blur-[120px] pointer-events-none" />

            <div className="w-full max-w-sm relative z-10">
                <div className="text-center mb-10">
                    <h1 className="text-4xl font-bold mb-2 tracking-tight">
                        Pop<span className="text-neon-purple">Cash</span>
                    </h1>
                    <p className="text-gray-400">The future of mobile banking</p>
                </div>

                <form onSubmit={handleLogin} className="space-y-6">
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-300 ml-1">Email Address</label>
                        <input
                            type="email"
                            placeholder="alex@example.com"
                            className="w-full bg-card-bg border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-gray-600 focus:outline-none focus:border-neon-purple/50 focus:ring-1 focus:ring-neon-purple/50 transition-all"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-300 ml-1">Password</label>
                        <input
                            type="password"
                            placeholder="••••••••"
                            className="w-full bg-card-bg border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-gray-600 focus:outline-none focus:border-neon-purple/50 focus:ring-1 focus:ring-neon-purple/50 transition-all"
                        />
                    </div>

                    <div className="flex justify-end">
                        <button type="button" className="text-sm text-neon-purple hover:text-neon-pink transition-colors">
                            Forgot Password?
                        </button>
                    </div>

                    <button
                        type="submit"
                        className="w-full bg-gradient-to-r from-neon-purple to-neon-pink text-white font-bold py-4 rounded-xl shadow-lg shadow-neon-purple/20 hover:scale-[1.02] active:scale-[0.98] transition-all"
                    >
                        Sign In
                    </button>
                </form>

                <div className="mt-8 text-center">
                    <p className="text-gray-400 text-sm">
                        Don't have an account?{' '}
                        <button className="text-neon-blue font-medium hover:underline">Sign Up</button>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Login;
