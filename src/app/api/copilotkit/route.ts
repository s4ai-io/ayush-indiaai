// Allow up to 300 seconds — matches vLLM HTTP timeout and workflow timeout.
// Without this Next.js terminates the SSE connection mid-stream (SocketError).
export const maxDuration = 300;
export const runtime = "nodejs";

import {
    CopilotRuntime,
    ExperimentalEmptyAdapter,
    copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { LlamaIndexAgent } from "@ag-ui/llamaindex";
import { NextRequest } from "next/server";

const BACKEND = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
    // Forward the caller's auth cookie so the backend RBAC middleware can
    // authorize the agent runs (registration → receptionist, treatment → doctor).
    const cookie = request.headers.get('cookie') ?? '';
    const authHeaders = cookie ? { Cookie: cookie } : undefined;

    const runtime = new CopilotRuntime({
        agents: {
            consultation_agent: new LlamaIndexAgent({
                url: `${BACKEND}/api/copilot/consultation/run`,
                headers: authHeaders,
            }) as any,
            registration_agent: new LlamaIndexAgent({
                url: `${BACKEND}/api/copilot/registration/run`,
                headers: authHeaders,
            }) as any,
            doctor_agent: new LlamaIndexAgent({
                url: `${BACKEND}/api/copilot/doctor/run`,
                headers: authHeaders,
            }) as any,
            treatment_agent: new LlamaIndexAgent({
                url: `${BACKEND}/api/copilot/treatment/run`,
                headers: authHeaders,
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
