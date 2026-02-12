'use client';

import React, { createContext, useContext, useState } from 'react';

interface ChatContextType {
    isOpen: boolean;
    toggleChat: () => void;
    closeChat: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider = ({ children }: { children: React.ReactNode }) => {
    const [isOpen, setIsOpen] = useState(false);

    const toggleChat = () => setIsOpen((prev) => !prev);
    const closeChat = () => setIsOpen(false);

    return (
        <ChatContext.Provider value={{ isOpen, toggleChat, closeChat }}>
            {children}
        </ChatContext.Provider>
    );
};

export const useChat = () => {
    const context = useContext(ChatContext);
    if (context === undefined) {
        throw new Error('useChat must be used within a ChatProvider');
    }
    return context;
};
