
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
            }),
            registration_agent: new LlamaIndexAgent({
                url: "http://127.0.0.1:8000/api/copilot/registration/run",
            }),
        },
    });

    const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
        runtime,
        serviceAdapter: new ExperimentalEmptyAdapter(),
        endpoint: "/api/copilotkit",
    });

    return handleRequest(request);
}
