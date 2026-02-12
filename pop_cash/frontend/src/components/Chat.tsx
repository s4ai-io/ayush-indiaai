"use client";

import { GenericToolCard } from "@/components/tools/GenericToolCard";
import { ProductTable } from "@/components/tools/renderers/ProductTable";
import { ProductCarousel } from "@/components/tools/renderers/ProductCarousel";
import { BalanceCard } from "@/components/tools/renderers/BalanceCard";
import { ExpiryRiskCard } from "@/components/tools/renderers/ExpiryRiskCard";
import { CartRecoveryCard } from "@/components/tools/renderers/CartRecoveryCard";
import { QuestionFlowCard } from "@/components/tools/QuestionFlowCard";

import { useCopilotAction, useCopilotChat } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { Sparkles, RotateCcw, Wallet, TrendingUp, ShoppingBag, ShoppingCart } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useCopilotContext } from "@copilotkit/react-core";
import { VoiceInputButton } from "@/components/VoiceInputButton";

export default function Chat() {

    const { threadId, setThreadId } = useCopilotContext();

    const handleThreadChange = () => {
        // Generate new GUID
        const newThreadId = crypto.randomUUID();
        console.log("newThreadId", newThreadId);
        setThreadId(newThreadId);
    };

    return (

        <YourMainContent handleThreadChange={handleThreadChange} />

    );
}

// Suggestion Card Component
interface SuggestionCardProps {
    icon: React.ReactNode;
    title: string;
    message: string;
    gradient: string;
    onClick: () => void;
}

function SuggestionCard({ icon, title, message, gradient, onClick }: SuggestionCardProps) {
    return (
        <button
            onClick={onClick}
            style={{ cursor: 'pointer' }}
            className={`group relative p-4 rounded-2xl bg-gradient-to-br ${gradient} border border-white/10 hover:border-white/30 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-neon-purple/20 text-left overflow-hidden`}
        >
            {/* Background glow effect */}
            {/* <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div> */}
            
            {/* Content */}
            <div className="relative z-10">
                <div className="flex flex-col items-center text-center gap-3">
                    <div className="w-16 h-16 rounded-2xl bg-white/10 backdrop-blur-sm 
                    flex items-center justify-center 
                    group-hover:bg-white/20 transition-colors">
                        <div className="text-2xl">
                            {icon}
                        </div>
                    </div>
                    <h3 className="font-semibold text-sm text-white 
                   group-hover:text-neon-blue transition-colors">
                        {title}
                    </h3>
                </div>
            </div>

            {/* Animated corner accent */}
            <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-white/10 to-transparent rounded-bl-full opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
        </button>
    );
}

function YourMainContent({ handleThreadChange }: { handleThreadChange: () => void }) {

    const [hasMessages, setHasMessages] = useState(false);
    const chatInputRef = useRef<HTMLTextAreaElement | null>(null);
    const context = useCopilotContext();
    const [voiceError, setVoiceError] = useState<string | null>(null);

    // Monitor messages and hide cards when any message exists
    useEffect(() => {
        // Check if there are any user messages in the chat
        const checkMessages = () => {
            // Look specifically for user messages, not system messages
            const userMessageElements = document.querySelectorAll('[class*="UserMessage"]');
            
            if (userMessageElements && userMessageElements.length > 0) {
                setHasMessages(true);
            }
        };
        
        // Check immediately and set up an interval to keep checking
        checkMessages();
        const interval = setInterval(checkMessages, 500);
        
        return () => clearInterval(interval);
    }, []);

    // Suggestion data
    const suggestions = [
        {
            icon: <Wallet className="w-10 h-10 text-neon-purple" />,
            title: "My popCoins Balance",
            message: "Please fetch my popCoins balance and expiry details.",
            gradient: "from-purple-900/40 to-purple-700/20",
        },
        {
            icon: <TrendingUp className="w-10 h-10 text-neon-blue" />,
            title: "Get Recommendations",
            message: "Get me best deals + popCoin combinations from the catalog",
            gradient: "from-blue-900/40 to-blue-700/20",
        },
        {
            icon: <ShoppingBag className="w-10 h-10 text-neon-pink" />,
            title: "Explore Catalog",
            message: "Explore products and services from different categories.",
            gradient: "from-pink-900/40 to-pink-700/20",
        },
        {
            icon: <ShoppingCart className="w-10 h-10 text-green-400" />,
            title: "Top Selling Products",
            message: "top women tees",
            gradient: "from-green-900/40 to-green-700/20",
        },
    ];

    // Handle voice transcript
    const handleVoiceTranscript = (transcript: string) => {
        console.log('Voice transcript received:', transcript);
        setVoiceError(null);
        
        // Helper function to find element in Shadow DOM
        const findElementDeep = (selector: string): HTMLElement | null => {
            // Try regular DOM first
            let element = document.querySelector(selector) as HTMLElement;
            if (element) return element;
            
            // Search in shadow roots
            const allElements = document.querySelectorAll('*');
            for (const el of allElements) {
                if (el.shadowRoot) {
                    element = el.shadowRoot.querySelector(selector) as HTMLElement;
                    if (element) return element;
                }
            }
            return null;
        };
        
        // Find and update textarea
        const textarea = findElementDeep('textarea') as HTMLTextAreaElement;
        if (textarea) {
            // Get current value and append transcript
            const currentValue = textarea.value;
            const newValue = currentValue ? `${currentValue} ${transcript}` : transcript;
            
            // Set the value using native setter
            const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype,
                'value'
            )?.set;
            
            if (nativeTextAreaValueSetter) {
                nativeTextAreaValueSetter.call(textarea, newValue);
            }
            
            // Trigger events to update React state
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
            textarea.dispatchEvent(new Event('change', { bubbles: true }));
            textarea.focus();
            
            console.log('Transcript inserted into textarea:', newValue);
        } else {
            console.error('Could not find textarea to insert transcript');
            setVoiceError('Failed to insert voice input. Please try again.');
        }
    };
    
    const handleVoiceError = (error: string) => {
        console.error('Voice input error:', error);
        setVoiceError(error);
        
        // Clear error after 5 seconds
        setTimeout(() => setVoiceError(null), 5000);
    };

    const handleSuggestionClick = (message: string) => {
        console.log('Card clicked with message:', message);
        setHasMessages(true);
        
        // Helper function to find element in Shadow DOM
        const findElementDeep = (selector: string): HTMLElement | null => {
            // Try regular DOM first
            let element = document.querySelector(selector) as HTMLElement;
            if (element) return element;
            
            // Search in shadow roots
            const allElements = document.querySelectorAll('*');
            for (const el of allElements) {
                if (el.shadowRoot) {
                    element = el.shadowRoot.querySelector(selector) as HTMLElement;
                    if (element) return element;
                }
            }
            return null;
        };
        
        // Try to submit with retries
        const attemptSubmit = (retries = 0, maxRetries = 10) => {
            if (retries >= maxRetries) {
                console.error('Failed to find textarea after', maxRetries, 'attempts');
                return;
            }
            
            const textarea = findElementDeep('textarea') as HTMLTextAreaElement;
            console.log(`Attempt ${retries + 1}: Found textarea:`, textarea);
            
            if (textarea) {
                // Focus the textarea
                textarea.focus();
                
                // Set the value
                const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLTextAreaElement.prototype,
                    'value'
                )?.set;
                
                if (nativeTextAreaValueSetter) {
                    nativeTextAreaValueSetter.call(textarea, message);
                }
                
                // Trigger all possible events
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                textarea.dispatchEvent(new Event('change', { bubbles: true }));
                textarea.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
                
                console.log('Textarea value set to:', textarea.value);
                
                // Try to submit
                setTimeout(() => {
                    // Look for submit button
                    let submitButton = findElementDeep('button[type="submit"]') as HTMLButtonElement;
                    
                    if (!submitButton) {
                        // Try to find the form and look for buttons
                        const form = textarea.closest('form');
                        if (form) {
                            const buttons = form.querySelectorAll('button');
                            submitButton = Array.from(buttons).find(btn => 
                                !btn.disabled && btn.type !== 'button'
                            ) as HTMLButtonElement;
                        }
                    }
                    
                    console.log('Found submit button:', submitButton);
                    
                    if (submitButton && !submitButton.disabled) {
                        submitButton.click();
                        console.log('Submit button clicked successfully');
                    } else {
                        // Fallback: simulate Enter key press
                        console.log('Trying Enter key as fallback');
                        const enterEvent = new KeyboardEvent('keydown', {
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true,
                            cancelable: false
                        });
                        textarea.dispatchEvent(enterEvent);
                        
                        // Also try keypress
                        textarea.dispatchEvent(new KeyboardEvent('keypress', {
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true,
                            cancelable: false
                        }));
                    }
                }, 100);
            } else {
                // Retry after a delay
                const delay = 100 * Math.pow(1.5, retries); // Exponential backoff
                console.log(`Textarea not found, retrying in ${delay}ms...`);
                setTimeout(() => attemptSubmit(retries + 1, maxRetries), delay);
            }
        };
        
        // Start attempting to submit
        setTimeout(() => attemptSubmit(), 100);
    };

    // --- Agent Tools ---

    useCopilotAction({
        name: "get_smart_recommendations",
        description: "Get smart recommendations for maximizing PopCoins.",
        available: "disabled",
        parameters: [
            { name: "user_query", type: "string", required: true },
        ],
        render: ({ args, status, result }) => {

            if (typeof result === "string") {
                // Define custom renderers for specific tools
                const toolRenderers = {
                    // "find_optimal_redemption": (data: any) => <ProductTable products={data} />,
                    "find_optimal_redemption": (data: any) => <ProductCarousel products={data} />,
                    "get_xcoin_balance": (data: any) => <BalanceCard data={data} />,
                };

                // check if it can be converted to json obj
                try {
                    // const jsonResult = JSON.parse(result);
                    // console.log("jsonResult", jsonResult);
                    return (
                        <GenericToolCard
                            user_query={args.user_query || ""}
                            status={status}
                            result={result}
                            title="Smart Recommendations"
                            subtitle="PopCash Advisor"
                            theme="indigo"
                            icon="sparkles"
                            toolRenderers={toolRenderers}
                        />

                    );
                } catch (e) {
                    console.log("e", e);
                    console.log("result", result);
                }
            }
            return (<></>);
        },
    });

    // useCopilotAction({
    //   name: "get_personalized_earnings_advice",
    //   description: "Get personalized advice on how to earn more PopCoins.",
    //   available: "disabled",
    //   parameters: [
    //     { name: "user_query", type: "string", required: true },
    //   ],
    //   render: ({ args, status, result }) => {
    //     return (
    //       <GenericToolCard
    //         user_query={args.user_query || ""}
    //         status={status}
    //         result={result}
    //         title="Earnings Optimizer"
    //         subtitle="PopCash Wealth"
    //         theme="green"
    //         icon="currency"
    //       />
    //     );
    //   },
    // });

    // useCopilotAction({
    //   name: "get_goal_shopping_assistance",
    //   description: "Help user set and track product goals.",
    //   available: "disabled",
    //   parameters: [
    //     { name: "user_query", type: "string", required: true },
    //   ],
    //   render: ({ args, status, result }) => {
    //     return (
    //       <GenericToolCard
    //         user_query={args.user_query || ""}
    //         status={status}
    //         result={result}
    //         title="Goal Assistant"
    //         subtitle="PopCash Goals"
    //         theme="purple"
    //         icon="target"
    //       />
    //     );
    //   },
    // });

    // useCopilotAction({
    //   name: "get_transaction_support",
    //   description: "Troubleshoot transaction and payment issues.",
    //   available: "disabled",
    //   parameters: [
    //     { name: "user_query", type: "string", required: true },
    //   ],
    //   render: ({ args, status, result }) => {
    //     return (
    //       <GenericToolCard
    //         user_query={args.user_query || ""}
    //         status={status}
    //         result={result}
    //         title="Support Center"
    //         subtitle="Transaction Help"
    //         theme="slate"
    //         icon="support"
    //       />
    //     );
    //   },
    // });

    useCopilotAction({
        name: "get_catalog_insights",
        description: "Discover products and trends in the catalog.",
        available: "disabled",
        parameters: [
            { name: "user_query", type: "string", required: true },
        ],
        render: ({ args, status, result }) => {
            // if (status !== 'complete') {
            //     return (
            //         <>
            //             <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
            //         </>
            //     );
            // }
            if (typeof result === "string") {
                // Define custom renderers for specific tools
                const toolRenderers = {
                    "get_catalog_products": (data: any) => <ProductCarousel products={data} />,
                    "get_xcoin_balance": (data: any) => <BalanceCard data={data} />,
                    "get_product_trends": (data: any) => <ProductCarousel products={data} />,
                    "get_product_recommendations": (data: any) => <ProductCarousel products={data} />,
                };

                // check if it can be converted to json obj
                try {
                    // const jsonResult = JSON.parse(result);
                    // console.log("jsonResult", jsonResult);
                    return (
                        <GenericToolCard
                            user_query={args.user_query || ""}
                            status={status}
                            result={result}
                            title="Trend Scout"
                            subtitle="Catalog & Trends"
                            theme="pink"
                            icon="tag"
                            toolRenderers={toolRenderers}
                        />
                    );

                } catch (e) {
                    console.log("e", e);
                    console.log("result", result);
                }
            }
            return (<></>);

        },
    });

    // useCopilotAction({
    //   name: "get_budget_insights",
    //   description: "Analyze spending and manage budget.",
    //   available: "disabled",
    //   parameters: [
    //     { name: "user_query", type: "string", required: true },
    //   ],
    //   render: ({ args, status, result }) => {
    //     return (
    //       <GenericToolCard
    //         user_query={args.user_query || ""}
    //         status={status}
    //         result={result}
    //         title="Budget Manager"
    //         subtitle="Spend Smart"
    //         theme="amber"
    //         icon="calculator"
    //       />
    //     );
    //   },
    // });

    // useCopilotAction({
    //   name: "get_referral_assistance",
    //   description: "Manage referrals and rewards.",
    //   available: "disabled",
    //   parameters: [
    //     { name: "user_query", type: "string", required: true },
    //   ],
    //   render: ({ args, status, result }) => {
    //     return (
    //       <GenericToolCard
    //         user_query={args.user_query || ""}
    //         status={status}
    //         result={result}
    //         title="Referral Assistant"
    //         subtitle="Share & Earn"
    //         theme="teal"
    //         icon="users"
    //       />
    //     );
    //   },
    // });

    useCopilotAction({
        name: "get_cart_recovery_assistance",
        description: "Help with abandoned cart items.",
        available: "disabled",
        parameters: [
            { name: "user_query", type: "string", required: true },
        ],
        render: ({ args, status, result }) => {
            if (typeof result === "string") {
                const toolRenderers = {
                    "detect_cart_abandonment": (data: any) => <CartRecoveryCard data={data} />,
                };

                return (
                    <GenericToolCard
                        user_query={args.user_query || ""}
                        status={status}
                        result={result}
                        title="Cart Assistant"
                        subtitle="Forgot Something?"
                        theme="yellow"
                        icon="cart"
                        toolRenderers={toolRenderers}
                    />
                );
            }
            return (<></>);
        },
    });

    useCopilotAction({
        name: "get_expiry_management_advice",
        description: "Manage expiring PopCoins.",
        available: "disabled",
        parameters: [
            { name: "user_query", type: "string", required: true },
        ],
        render: ({ args, status, result }) => {
            if (typeof result === "string") {
                // Define custom renderers for specific tools
                const toolRenderers = {
                    "predict_expiry_risk": (data: any) => <ExpiryRiskCard data={data} />,
                    "get_xcoin_balance": (data: any) => <BalanceCard data={data} />,
                };

                // check if it can be converted to json obj
                try {
                    // const jsonResult = JSON.parse(result);
                    // console.log("jsonResult", jsonResult);
                    return (
                        <GenericToolCard
                            user_query={args.user_query || ""}
                            status={status}
                            result={result}
                            title="Expiry Manager"
                            subtitle="Act Now"
                            theme="red"
                            icon="clock"
                            toolRenderers={toolRenderers}
                        />

                    );
                } catch (e) {
                    console.log("e", e);
                    console.log("result", result);
                }
            }
            return (<></>);
        },
    });

    useCopilotAction({
        name: "get_question_navigation",
        description: "Interactive question-based catalog exploration.",
        available: "disabled",
        parameters: [
            { name: "user_query", type: "string", required: true },
        ],
        render: ({ args, status, result }) => {
            console.log("[QuestionNav] Status:", status, "Result type:", typeof result);
            if (typeof result === "string") {
                console.log("[QuestionNav] Result string:", result);
                try {
                    // The backend returns a dict-like string with 'response', 'sources', 'reasoning'
                    // We need to extract the 'response' field which contains the actual JSON
                    
                    let jsonStr = result;
                    
                    // Try to extract the response field value
                    // Look for 'response': followed by a quoted string
                    const responseStart = result.indexOf("'response':");
                    if (responseStart !== -1) {
                        // Find the opening quote after 'response':
                        const valueStart = result.indexOf("'", responseStart + "'response':".length);
                        if (valueStart !== -1) {
                            // Find the matching closing quote (accounting for escaped quotes)
                            let valueEnd = valueStart + 1;
                            let escapeCount = 0;
                            
                            while (valueEnd < result.length) {
                                if (result[valueEnd] === '\\') {
                                    escapeCount++;
                                    valueEnd++;
                                } else if (result[valueEnd] === "'" && escapeCount % 2 === 0) {
                                    // Found unescaped quote
                                    break;
                                } else {
                                    escapeCount = 0;
                                    valueEnd++;
                                }
                            }
                            
                            if (valueEnd < result.length) {
                                jsonStr = result.substring(valueStart + 1, valueEnd);
                                // Unescape the string
                                jsonStr = jsonStr.replace(/\\'/g, "'").replace(/\\"/g, '"');
                                console.log("[QuestionNav] Extracted response field:", jsonStr);
                            }
                        }
                    }
                    
                    // Fallback: if extraction failed, try to find JSON object
                    if (jsonStr === result) {
                        const jsonStart = result.indexOf('{');
                        const jsonEnd = result.lastIndexOf('}');
                        
                        if (jsonStart !== -1 && jsonEnd !== -1) {
                            jsonStr = result.substring(jsonStart, jsonEnd + 1);
                            console.log("[QuestionNav] Using fallback extraction");
                        }
                    }
                    
                    // Parse the JSON response from the agent
                    const data = JSON.parse(jsonStr);
                    console.log("[QuestionNav] Parsed data:", data);
                    
                    // If should_route is true and we have products, show them directly!
                    if (data.products && data.products.length > 0) {
                        return (
                            <div className="space-y-4">
                                <div className="p-4 rounded-2xl bg-gradient-to-br from-green-900/40 to-emerald-900/40 border border-white/10">
                                    <div className="text-green-400 text-sm font-semibold mb-1">
                                        ✓ Discovery Complete
                                    </div>
                                    <div className="text-gray-300 text-xs">
                                        Showing results for: {data.accumulated_context || "Your selection"}
                                    </div>
                                </div>
                                <div className="px-2">
                                    <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                                        <TrendingUp className="text-neon-cyan w-5 h-5" />
                                        Discovered Products
                                    </h3>
                                    <ProductCarousel products={data.products} />
                                </div>
                            </div>
                        );
                    }

                    // If should_route is true but no products yet (legacy fallback), trigger routing
                    if (data.should_route && data.final_query) {
                        console.log("[QuestionNav] Routing to orchestrator (no products in response)");
                        setTimeout(() => {
                            handleSuggestionClick(data.final_query);
                        }, 500);
                        
                        return (
                            <div className="p-6 rounded-2xl bg-gradient-to-br from-green-900/40 to-emerald-900/40 border border-white/10">
                                <div className="text-center">
                                    <div className="text-green-400 text-lg font-semibold mb-2">
                                        ✓ Got it! Finding the best options for you...
                                    </div>
                                    <div className="text-gray-300 text-sm">
                                        {data.accumulated_context}
                                    </div>
                                </div>
                            </div>
                        );
                    }
                    
                    // Otherwise, display the questions for the current round
                    if (data.questions && data.questions.length > 0) {
                        console.log("[QuestionNav] Rendering QuestionFlowCard");
                        return (
                            <QuestionFlowCard
                                questions={data.questions}
                                round={data.round || 1}
                                accumulatedContext={data.accumulated_context || ""}
                                onQuestionSelect={(question) => {
                                    const nextQuery = `${args.user_query} | User selected: ${question.text} (${question.category})`;
                                    handleSuggestionClick(nextQuery);
                                }}
                            />
                        );
                    }
                } catch (e) {
                    console.error("Error parsing question navigation result:", e);
                    console.error("Result:", result);
                    
                    // Show error message to user
                    return (
                        <div className="p-6 rounded-2xl bg-gradient-to-br from-red-900/40 to-orange-900/40 border border-white/10">
                            <div className="text-center">
                                <div className="text-red-400 text-lg font-semibold mb-2">
                                    Unable to parse response
                                </div>
                                <div className="text-gray-300 text-sm">
                                    Please try again or contact support.
                                </div>
                            </div>
                        </div>
                    );
                }
            }
            return (<></>);
        },
    });

    // useCopilotAction({
    //   name: "get_gamified_challenges",
    //   description: "Find challenges to earn bonus PopCoins.",
    //   available: "disabled",
    //   parameters: [
    //     { name: "user_query", type: "string", required: true },
    //   ],
    //   render: ({ args, status, result }) => {
    //     return (
    //       <GenericToolCard
    //         user_query={args.user_query || ""}
    //         status={status}
    //         result={result}
    //         title="Challenge Arena"
    //         subtitle="Play & Earn"
    //         theme="violet"
    //         icon="game"
    //       />
    //     );
    //   },
    // });

    return (
        <div className="flex justify-center items-center h-full w-full copilot-custom-theme">
            <div className="h-full w-full rounded-lg flex flex-col overflow-hidden bg-card-bg/50 backdrop-blur-sm border border-white/5">

                {/* Fixed Header */}
                <div className="flex-none p-4 bg-gradient-to-r from-neon-purple/20 to-neon-blue/20 border-b border-white/10 flex justify-between items-center z-10 relative">
                    <div className="flex items-center gap-3">
                        <div className="relative">
                            <div className="w-10 h-10 rounded-full overflow-hidden border-2 border-neon-purple p-0.5">
                                <img src="/avatar_1.jpg" alt="AI" className="w-full h-full object-cover rounded-full" />
                            </div>
                            <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-card-bg"></div>
                        </div>
                        <div>
                            <h3 className="font-bold text-white text-sm flex items-center gap-1">
                                PoP AI Assistant <Sparkles size={12} className="text-yellow-400" />
                            </h3>
                            <p className="text-xs text-gray-400">Online</p>
                        </div>
                    </div>

                    <button
                        onClick={() => {
                            handleThreadChange();
                            setHasMessages(false);
                        }}
                        className="flex items-center gap-2 px-3 mr-12 py-1.5 rounded-full bg-white/10 hover:bg-white/20 border border-white/10 text-white transition-all text-xs font-medium active:scale-95 group"
                    >
                        <RotateCcw size={14} className="group-hover:rotate-[-45deg] transition-transform" />
                        New Chat
                    </button>
                </div>

                {/* Scrollable Chat Area */}
                <div className="flex-1 overflow-hidden relative">
                    {/* Voice Error Toast */}
                    {voiceError && (
                        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50 
                            bg-red-500/90 text-white px-4 py-2 rounded-lg shadow-lg 
                            backdrop-blur-sm border border-red-400/50 text-sm max-w-md text-center
                            animate-in fade-in slide-in-from-top-2 duration-300">
                            {voiceError}
                        </div>
                    )}
                    
                    {/* Voice Input Button - Positioned absolutely over the chat input */}
                    <div className="absolute right-15 bottom-6 z-50 pointer-events-none scale-80">
                        <div className="pointer-events-auto">
                            <VoiceInputButton 
                                onTranscript={handleVoiceTranscript}
                                onError={handleVoiceError}
                            />
                        </div>
                    </div>
                    
                    <CopilotChat
                        className="h-full max-w-6xl mx-auto [&_.copilotKitChat]:bg-transparent [&_.copilotKitChat]:shadow-none"
                        // labels={{ initial: "👋 Hi! I'm your PopCash Intelligence Orchestrator. How can I help you earn or spend PopCoins today?" }}
                        onSubmitMessage={() => setHasMessages(true)}
                        suggestions={!hasMessages ? suggestions.map(s => ({ message: s.message, title: s.title })) : []}
                        RenderSuggestionsList={({ suggestions: copilotSuggestions }) => (
                            <div className="w-full px-4 py-8">
                                <div className="w-full mx-auto">
                                    <div className="text-center mb-8">
                                        <p className="text-white text-xl">
                                            Quick Start 🚀
                                        </p>
                                        <p className="text-gray-400 text-xs">
                                            Select a suggestion below to get started
                                        </p>
                                    </div>
                                    
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {suggestions.map((suggestion, index) => (
                                            <SuggestionCard
                                                key={index}
                                                icon={suggestion.icon}
                                                title={suggestion.title}
                                                message={suggestion.message}
                                                gradient={suggestion.gradient}
                                                onClick={() => handleSuggestionClick(suggestion.message)}
                                            />
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}
                    />
                </div>
            </div>
        </div>
    );
};