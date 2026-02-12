import React from 'react';
import Navbar from '@/components/Navbar';
import Chatbot from '@/components/Chatbot';
import Header from '@/components/Header';
import { ChatProvider } from '@/context/ChatContext';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <ChatProvider>
            <div className="relative min-h-screen bg-dark-bg">
                {/* Background gradients for neon effect */}
                <div className="fixed inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute top-[-5%] left-[-5%] w-[40%] h-[40%] bg-neon-purple/20 rounded-full blur-[100px]" />
                    <div className="absolute bottom-[-5%] right-[-5%] w-[40%] h-[40%] bg-neon-blue/20 rounded-full blur-[100px]" />
                </div>

                <div className="relative z-10">
                    <Header />
                    <main className="p-4 pb-32">
                        {children}
                    </main>
                    <Navbar />
                    <Chatbot />
                </div>
            </div>
        </ChatProvider>
    );
}
