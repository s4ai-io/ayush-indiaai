import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";

export default function MobileLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <div className="flex justify-center min-h-screen bg-zinc-950 font-sans antialiased overflow-hidden">
            <div className="w-full max-w-lg h-[100dvh] bg-black text-white relative shadow-2xl transform-gpu ring-1 ring-white/10">
                <div className="absolute inset-0 overflow-y-auto custom-scrollbar overflow-x-hidden">
                    <CopilotKit runtimeUrl="/api/copilotkit"
                        showDevConsole={false}
                        enableInspector={false}
                        agent="sample_agent">

                        {children}
                    </CopilotKit>
                </div>
            </div>
        </div>
    );
}
