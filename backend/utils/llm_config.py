import os
import json
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional, Sequence
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import LLMMetadata
from llama_index.core.llms.llm import LLM
from llama_index.core.tools import BaseTool
from dotenv import load_dotenv
from utils.llm_logger import apply_logging_to_llm

load_dotenv()


def get_llm():
    """
    Returns a configured LLM instance based on environment variables.
    Supports either standard OpenAI API or an OpenAI-compatible vLLM endpoint (e.g., for Phi-4).
    """
    llm_binding = os.getenv("LLM_BINDING", "openai").lower()

    if llm_binding == "vllm":
        model = os.getenv("LLM_MODEL", "microsoft/phi-4")
        api_base = os.getenv("VLLM_API_HOST", "http://localhost:8000/v1")
        api_key = os.getenv("VLLM_API_KEY", "dummy-key")

        class VLLMOpenAI(OpenAI):
            """
            Patched OpenAI wrapper for vLLM models (e.g. Phi-4) that don't
            reliably invoke tools when tool_choice='auto'.

            Fix: always send tool_choice='required' when tools are provided,
            so the model is forced to pick a tool rather than narrating the call.
            """

            @property
            def metadata(self) -> LLMMetadata:
                return LLMMetadata(
                    context_window=128000,
                    num_output=self.max_tokens or -1,
                    is_chat_model=True,
                    is_function_calling_model=True,
                    model_name=self.model,
                )

            def _prepare_chat_with_tools(
                self,
                tools: List[BaseTool],
                user_msg: Optional[Any] = None,
                chat_history: Optional[Any] = None,
                verbose: bool = False,
                allow_parallel_tool_calls: bool = False,
                tool_choice: Optional[Any] = "auto",
                **kwargs: Any,
            ) -> Dict[str, Any]:
                """Force tool_choice='required' when tools are present."""
                result = super()._prepare_chat_with_tools(
                    tools=tools,
                    user_msg=user_msg,
                    chat_history=chat_history,
                    verbose=verbose,
                    allow_parallel_tool_calls=allow_parallel_tool_calls,
                    tool_choice=tool_choice,
                    **kwargs,
                )
                # Override: force model to ALWAYS call a tool when tools are present
                # Phi-4 ignores tool_choice="auto" and narrates instead of calling tools.
                # "required" forces it to emit proper tool_calls in the API response.
                if tools:
                    result["tool_choice"] = "required"
                return result

        # Cap output tokens to keep responses fast.
        # Agents only need short tool-call JSON + brief chat replies.
        # Override via LLM_MAX_TOKENS env var if a specific task needs more.
        # max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1024"))

        llm = VLLMOpenAI(
            model=model,
            api_base=api_base,
            api_key=api_key,
            temperature=0,
            # max_tokens=max_tokens,
            timeout=300.0,  # 5 min — Phi-4 on Modal can be slow (cold start + large model)
        )
    else:
        # Default standard OpenAI
        model = os.getenv("LLM_MODEL", "gpt-4o")
        llm = OpenAI(model=model, temperature=0)

    return apply_logging_to_llm(llm)
