import asyncio
import json
import time
from datetime import datetime, timezone

import aiohttp
import modal

from typing import Any, Dict, List

import tiktoken  # Add this import
VLLM_COMMIT="75531a6c134282f940c86461b3c40996b4136793"
VLLM_URL = "--extra-index-url https://wheels.vllm.ai/" + VLLM_COMMIT


vllm_image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.8.1-devel-ubuntu22.04",
        add_python="3.12",
    )
    .entrypoint([])
    .apt_install("git")
    .apt_install("wget")
    .uv_pip_install(
        "vllm==0.7.2",
        "uv",
        "huggingface_hub[hf_transfer]==0.34.4",
        "flashinfer-python==0.5.3",
        pre=True,
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1",
    "VLLM_USE_FLASHINFER_MOE_FP8": "1",
          "VLLM_LOGGING_LEVEL":"DEBUG"})
)

# Phi-4 model from Microsoft
MODEL_NAME = "microsoft/phi-4"
MODEL_REVISION = None  # Use latest version, or specify a commit hash if needed
# MODEL_NAME = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16" 
# use full commit hash from the main branch

hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)

# vllm_image = vllm_image.env({"VLLM_USE_V1": "1"})

FAST_BOOT = True  # slower boots but faster inference
MAX_INPUTS = 2  # how many requests can one replica handle? tune carefully!
CUDA_GRAPH_CAPTURE_SIZES = [  # 1, 2, 4, ... MAX_INPUTS
    1 << i for i in range((MAX_INPUTS).bit_length())
]


app = modal.App("s4ai-phi4-inference")

N_GPU = 2
MINUTES = 60  # seconds
VLLM_PORT = 8000


@app.function(
    image=vllm_image,
    gpu=f"L40S:{N_GPU}",
    scaledown_window=10 * MINUTES,  # how long should we stay up with no requests?
    timeout=30 * MINUTES,  # how long should we wait for container start?
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/root/.cache/vllm": vllm_cache_vol,
    },
)
@modal.concurrent(max_inputs=MAX_INPUTS)
@modal.web_server(port=VLLM_PORT, startup_timeout=30 * MINUTES)
def serve():
    import subprocess



    cmd = [
    "vllm",
    "serve",
    "--uvicorn-log-level=info",
    MODEL_NAME,
    "--served-model-name", MODEL_NAME,
    "--host", "0.0.0.0",
    "--port", str(VLLM_PORT),
    "--trust-remote-code", 

    # Performance optimizations
    "--max-model-len", "16384",  # Phi-4 has 16K context window
    "--gpu-memory-utilization", "0.95",
    "--tensor-parallel-size", str(N_GPU),
    
    # Reduce memory pressure
    "--disable-log-requests",
    "--max-num-seqs", "128",  # Limit concurrent sequences
    
    # Enable optimizations
    "--enable-chunked-prefill",
    
    # Enable tool/function calling support
    "--enable-auto-tool-choice",
    "--tool-call-parser", "hermes",  
]

    # enforce-eager disables both Torch compilation and CUDA graph capture
    # default is no-enforce-eager. see the --compilation-config flag for tighter control
    cmd += ["--enforce-eager" if FAST_BOOT else "--no-enforce-eager"]

    if not FAST_BOOT:  # CUDA graph capture is only used with `--enforce-eager`
        cmd += [
            "-O.cudagraph_capture_sizes="
            + str(CUDA_GRAPH_CAPTURE_SIZES).replace(" ", "")
        ]

    # assume multiple GPUs are for splitting up large matrix multiplications
    # cmd += ["--tensor-parallel-size", str(N_GPU)]

    print(cmd)

    subprocess.Popen(" ".join(cmd), shell=True)


# @app.local_entrypoint()
# async def test(test_timeout=30 * MINUTES, user_content=None, twice=True):
#     url = serve.get_web_url()
#     print(url)
#     system_prompt = {
#         "role": "system",
#         "content": f"""You are ChatModal, a large language model trained by Modal.
#         Knowledge cutoff: 2024-06
#         Current date: {datetime.now(timezone.utc).date()}
#         Reasoning: low
#         \\# Valid channels: analysis, commentary, final. Channel must be included for every message.
#         Calls to these tools must go to the commentary channel: 'functions'.""",
#     }

#     if user_content is None:
#         user_content = "Explain what the Singular Value Decomposition is."

#     messages = [  # OpenAI chat format
#         system_prompt,
#         {"role": "user", "content": user_content},
#     ]

#     async with aiohttp.ClientSession(base_url=url) as session:
#         print(f"Running health check for server at {url}")
#         async with session.get("/health", timeout=test_timeout - 1 * MINUTES) as resp:
#             up = resp.status == 200
#         assert up, f"Failed health check for server at {url}"
#         print(f"Successful health check for server at {url}")

#         print(f"Sending messages to {url}:", *messages, sep="\n\t")
#         await _send_request(session, "llm", messages)

#         if twice:
#             messages[0]["content"] += "\nTalk like a pirate, matey."
#             print(f"Re-sending messages to {url}:", *messages, sep="\n\t")
#             await _send_request(session, "llm", messages)


async def _send_request(
    session: aiohttp.ClientSession, model: str, messages: list
) -> None:
    """Send request with error handling"""
    payload: dict[str, Any] = {"messages": messages, "model": model, "stream": True}
    headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}

    t = time.perf_counter()
    
    try:
        async with session.post(
            "/v1/chat/completions", json=payload, headers=headers, timeout=10 * MINUTES
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                print(f"❌ HTTP Error {resp.status}: {error_text}")
                return
            
            async for raw in resp.content:
                try:
                    line = raw.decode().strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        line = line[len("data: ") :]

                    # Add JSON parsing protection
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON decode error on line: {line[:100]}... Error: {e}")
                        continue  # Skip malformed chunks
                    
                    if chunk.get("object") != "chat.completion.chunk":
                        print(f"⚠️ Unexpected chunk object: {chunk.get('object')}")
                        continue
                    
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                        
                    delta = choices[0].get("delta", {})

                    if "content" in delta:
                        print(delta["content"], end="")
                    elif "reasoning_content" in delta:
                        print(delta["reasoning_content"], end="")
                        
                except Exception as chunk_error:
                    print(f"⚠️ Error processing chunk: {chunk_error}")
                    continue  # Skip problematic chunks
                    
    except aiohttp.ClientError as e:
        print(f"❌ Network error: {str(e)}")
        return
    except asyncio.TimeoutError:
        print("❌ Request timeout")
        return
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return
    
    print("")
    print(f"Time to Last Token: {time.perf_counter() - t:.2f} seconds")

async def _send_request_with_response(
    session: aiohttp.ClientSession, model: str, messages: list
) -> str:
    """Send request and return the complete response content"""
    payload: dict[str, Any] = {"messages": messages, "model": model, "stream": True}
    headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}

    response_content = ""
    t = time.perf_counter()
    
    async with session.post(
        "/v1/chat/completions", json=payload, headers=headers, timeout=10 * MINUTES
    ) as resp:
        async for raw in resp.content:
            resp.raise_for_status()
            line = raw.decode().strip()
            if not line or line == "data: [DONE]":
                continue
            if line.startswith("data: "):
                line = line[len("data: ") :]

            chunk = json.loads(line)
            assert chunk["object"] == "chat.completion.chunk"
            delta = chunk["choices"][0]["delta"]

            if "content" in delta:
                content = delta["content"]
                print(content, end="")  # Still print for real-time display
                response_content += content  # Capture for return
            elif "reasoning_content" in delta:
                reasoning = delta["reasoning_content"]
                print(reasoning, end="")
                response_content += reasoning
            else:
                raise ValueError(f"Unsupported response delta: {delta}")
    
    print("")  # New line after response
    print(f"Time to Last Token: {time.perf_counter() - t:.2f} seconds")
    
    return response_content

# Add this enhanced version at the top of your file
class PersistentConversationManager:
    def __init__(self, max_tokens=7500):
        self.max_tokens = max_tokens
        self.conversation_history = []
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.encoding = None
    
    def count_tokens(self, text: str) -> int:
        if self.encoding:
            return len(self.encoding.encode(text))
        return len(text) // 4
    
    def count_message_tokens(self, message: Dict[str, Any]) -> int:
        tokens = self.count_tokens(message["content"])
        tokens += 4  # Message formatting
        if message["role"] == "system":
            tokens += 2
        return tokens
    
    def add_message(self, message: Dict[str, Any]):
        """Add a message to conversation history"""
        self.conversation_history.append(message)
        self._truncate_if_needed()
    
    def add_messages(self, messages: List[Dict[str, Any]]):
        """Add multiple messages"""
        self.conversation_history.extend(messages)
        self._truncate_if_needed()
    
    def _truncate_if_needed(self):
        """Internal method to truncate when needed"""
        total_tokens = sum(self.count_message_tokens(msg) for msg in self.conversation_history)
        
        if total_tokens <= self.max_tokens:
            return
        
        print(f"Auto-truncating conversation: {total_tokens} -> target {self.max_tokens} tokens")
        
        # Keep system messages
        system_msgs = [msg for msg in self.conversation_history if msg["role"] == "system"]
        other_msgs = [msg for msg in self.conversation_history if msg["role"] != "system"]
        
        # Rebuild conversation
        kept_messages = system_msgs.copy()
        current_tokens = sum(self.count_message_tokens(msg) for msg in system_msgs)
        
        # Add from most recent backwards
        for msg in reversed(other_msgs):
            msg_tokens = self.count_message_tokens(msg)
            if current_tokens + msg_tokens > self.max_tokens:
                break
            current_tokens += msg_tokens
            kept_messages.insert(-len(system_msgs) if system_msgs else 0, msg)
        
        self.conversation_history = kept_messages
        final_tokens = sum(self.count_message_tokens(msg) for msg in self.conversation_history)
        print(f"Conversation truncated to {len(self.conversation_history)} messages ({final_tokens} tokens)")
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get current conversation messages"""
        return self.conversation_history.copy()
    
    def clear(self):
        """Clear conversation history"""
        self.conversation_history = []

# Use it like this in a modified test function:
@app.local_entrypoint()
async def test(test_timeout=30 * MINUTES, user_content=None, twice=True):
    # Create persistent conversation manager
    conv_manager = PersistentConversationManager(max_tokens=32000)
    
    url = serve.get_web_url()
    print(url)
    
    # Add system prompt
    system_prompt = {
        "role": "system",
        "content": f"""You are ChatModal, a helpful AI assistant powered by Microsoft's Phi-4 model.
        Knowledge cutoff: 2024-06
        Current date: {datetime.now(timezone.utc).date()}""",
    }
    conv_manager.add_message(system_prompt)

    if user_content is None:
        user_content = "Explain what the Singular Value Decomposition is."
    
    # Add user message
    conv_manager.add_message({"role": "user", "content": user_content})

    async with aiohttp.ClientSession(base_url=url) as session:
        print(f"Running health check for server at {url}")
        async with session.get("/health", timeout=test_timeout - 1 * MINUTES) as resp:
            up = resp.status == 200
        assert up, f"Failed health check for server at {url}"
        print(f"Successful health check for server at {url}")

        # Get truncated messages and send
        messages = conv_manager.get_messages()
        print(f"Sending {len(messages)} messages to {url}")
        response_content = await _send_request_with_response(session, "llm", messages)
        
        # Add assistant response to conversation
        if response_content:
            conv_manager.add_message({"role": "assistant", "content": response_content})

        if twice:
            # Add another user message
            conv_manager.add_message({"role": "user", "content": "Talk like a pirate, matey."})
            
            messages = conv_manager.get_messages()
            print(f"Re-sending {len(messages)} messages to {url}")
            await _send_request(session, "llm", messages)


# modal deploy gpt_oss_inference.py
# modal run gpt_oss_inference.py
