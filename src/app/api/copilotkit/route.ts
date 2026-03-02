// Allow up to AGENT_TIMEOUT_SECONDS — matches vLLM HTTP timeout and workflow timeout.
// Without this Next.js terminates the SSE connection mid-stream (SocketError).
import { AGENT_TIMEOUT_SECONDS } from '@/lib/config';
export const maxDuration = AGENT_TIMEOUT_SECONDS;
export const runtime = "nodejs";

import {
    CopilotRuntime,
    ExperimentalEmptyAdapter,
    copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { LlamaIndexAgent } from "@ag-ui/llamaindex";
import { NextRequest } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
    const runtime = new CopilotRuntime({
        agents: {
            consultation_agent: new LlamaIndexAgent({
                url: `${BACKEND}/api/copilot/consultation/run`,
            }) as any,
            registration_agent: new LlamaIndexAgent({
                url: `${BACKEND}/api/copilot/registration/run`,
            }) as any,
            doctor_agent: new LlamaIndexAgent({
                url: `${BACKEND}/api/copilot/doctor/run`,
            }) as any,
            treatment_agent: new LlamaIndexAgent({
                url: `${BACKEND}/api/copilot/treatment/run`,
            }) as any,
        },
    });

    const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
        runtime,
        serviceAdapter: new ExperimentalEmptyAdapter(),
        endpoint: "/api/copilotkit",
    });

    return handleRequest(request);
}
