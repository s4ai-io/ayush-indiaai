import React from 'react';
import { HelpCircle, ArrowRight } from 'lucide-react';

interface Question {
    id: string;
    text: string;
    category: string;
}

interface QuestionFlowCardProps {
    questions: Question[];
    round: number;
    accumulatedContext: string;
    onQuestionSelect: (question: Question) => void;
}

export function QuestionFlowCard({ 
    questions, 
    round, 
    accumulatedContext, 
    onQuestionSelect 
}: QuestionFlowCardProps) {
    return (
        <div className="w-full max-w-4xl mx-auto p-6 rounded-2xl bg-gradient-to-br from-indigo-900/40 to-purple-900/40 border border-white/10 backdrop-blur-sm">
            {/* Header with Progress */}
            <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        <HelpCircle className="w-6 h-6 text-indigo-400" />
                        Let's Find What You're Looking For
                    </h3>
                    <div className="px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-300 text-sm font-medium">
                        Level {round}
                    </div>
                </div>
                
                {/* Context Breadcrumb */}
                {accumulatedContext && (
                    <div className="flex items-center gap-2 text-sm text-gray-300 bg-white/5 rounded-lg px-3 py-2 border border-white/10">
                        <span className="text-gray-400">Your path:</span>
                        <span className="font-medium">{accumulatedContext}</span>
                    </div>
                )}
            </div>

            {/* Questions Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {questions.map((question, index) => (
                    <button
                        key={`${question.text}-${index}`}
                        onClick={() => onQuestionSelect(question)}
                        className="group relative p-5 rounded-xl bg-gradient-to-br from-white/5 to-white/10 
                                 border border-white/10 hover:border-indigo-400/50 
                                 transition-all duration-300 hover:scale-105 hover:shadow-xl 
                                 hover:shadow-indigo-500/20 text-left overflow-hidden"
                    >
                        {/* Background glow effect */}
                        <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 
                                      opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                        
                        {/* Content */}
                        <div className="relative z-10 flex items-start justify-between gap-3">
                            <div className="flex-1">
                                <div className="text-xs text-indigo-300 mb-2 font-medium uppercase tracking-wide">
                                    {question.category}
                                </div>
                                <p className="text-white font-medium leading-relaxed">
                                    {question.text}
                                </p>
                            </div>
                            <ArrowRight className="w-5 h-5 text-indigo-400 flex-shrink-0 
                                                 group-hover:translate-x-1 transition-transform" />
                        </div>

                        {/* Animated corner accent */}
                        <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-br 
                                      from-indigo-400/20 to-transparent rounded-bl-full 
                                      opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    </button>
                ))}
            </div>

            {/* Helper text */}
            <div className="mt-4 text-center text-sm text-gray-400">
                Select an option to continue exploring
            </div>
        </div>
    );
}
