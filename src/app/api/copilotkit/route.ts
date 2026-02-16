
import {
    CopilotRuntime,
    ExperimentalEmptyAdapter,
    copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { LlamaIndexAgent } from "@ag-ui/llamaindex";
import { NextRequest } from "next/server";

export async function POST(request: NextRequest) {
    const runtime = new CopilotRuntime({
        agents: {
            ehr_agent: new LlamaIndexAgent({
                url: "http://127.0.0.1:8000/api/copilot/ehr/run",
            }) as any,
            registration_agent: new LlamaIndexAgent({
                url: "http://127.0.0.1:8000/api/copilot/registration/run",
            }) as any,
            doctor_agent: new LlamaIndexAgent({
                url: "http://127.0.0.1:8000/api/copilot/doctor/run",
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
