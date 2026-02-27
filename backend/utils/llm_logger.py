import os
import datetime
from typing import Any, AsyncGenerator, List, Optional

# Setup base logs directory relative to this file
# backend/utils/llm_logger.py -> backend/logs/model_interactions/
LOGS_BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs",
    "model_interactions",
)


def _ensure_log_dir():
    """Ensure the base logging directory exists."""
    os.makedirs(LOGS_BASE_DIR, exist_ok=True)


def _get_txt_file_path() -> str:
    """Get a new text file path for the current interaction with a timestamp."""
    _ensure_log_dir()
    # Format: YYYY-MM-DD_HH-MM-SS-mmm.txt
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]
    return os.path.join(LOGS_BASE_DIR, f"{timestamp}_OpenAI.txt")


def _messages_to_txt(messages) -> str:
    """Safely serialize LlamaIndex ChatMessage objects (or dicts) to text."""
    if not isinstance(messages, (list, tuple)):
        return str(messages)

    lines = []
    for msg in messages:
        try:
            # LlamaIndex ChatMessage
            role = getattr(msg, "role", None) or msg.get("role", "unknown")
            content = getattr(msg, "content", None)
            if content is None:
                content = msg.get("content", str(msg))
            lines.append(f"Role: {role}\nContent: {content}\n")
        except Exception:
            lines.append(str(msg))
    return "\n".join(lines)


def _response_to_txt(response) -> str:
    """Safely serialize a ChatResponse or CompletionResponse to text."""
    if response is None:
        return "(no response)"
    # ChatResponse: has .message (ChatMessage) with .role and .content
    if hasattr(response, "message"):
        msg = response.message
        role = str(getattr(msg, "role", "assistant"))
        content = str(getattr(msg, "content", ""))
        # Also capture tool calls if present
        additional = getattr(msg, "additional_kwargs", {})
        tool_calls = additional.get("tool_calls", [])
        out = f"Role: {role}\nContent: {content}\n"
        if tool_calls:
            out += f"Tool Calls: {tool_calls}\n"
        return out
    # CompletionResponse: has .text
    if hasattr(response, "text"):
        return f"Text: {response.text}\n"
    return str(response)


def _log_interaction(file_path, type_label, messages, response=None, error=None):
    """Write input, output, and/or error to a single txt file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write(f"Type:      {type_label}\n")
            f.write(
                f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n"
            )
            f.write("=" * 60 + "\n\n")

            # Write input
            f.write("--- INPUT ---\n")
            f.write(_messages_to_txt(messages))
            f.write("\n\n")

            # Write output
            if response is not None:
                f.write("--- OUTPUT ---\n")
                f.write(_response_to_txt(response))
                f.write("\n")

            if error is not None:
                f.write("--- ERROR ---\n")
                f.write(f"{type(error).__name__}: {str(error)}\n")

    except Exception as e:
        print(f"[llm_logger] Failed to write log: {e}")


class LoggingLLMWrapper:
    """
    A transparent proxy around a LlamaIndex LLM that logs every
    chat / achat / complete / acomplete / astream_chat_with_tools call.

    We use a proxy instead of monkey-patching because LlamaIndex LLMs are
    Pydantic BaseModel subclasses; direct attribute assignment is silently
    ignored (or raises) on those classes.
    """

    def __init__(self, llm):
        # Store the real LLM under a private name so __getattr__ passes
        # everything else through transparently.
        object.__setattr__(self, "_llm", llm)

    # ------------------------------------------------------------------ #
    #  Transparent attribute pass-through                                  #
    # ------------------------------------------------------------------ #
    @property
    def __class__(self):
        # Make isinstance() checks work as if we are the real LLM
        return type(object.__getattribute__(self, "_llm"))

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_llm"), name)

    def __setattr__(self, name, value):
        if name == "_llm":
            object.__setattr__(self, name, value)
        else:
            setattr(object.__getattribute__(self, "_llm"), name, value)

    # ------------------------------------------------------------------ #
    #  Logged methods                                                       #
    # ------------------------------------------------------------------ #
    def chat(self, messages, **kwargs):
        llm = object.__getattribute__(self, "_llm")
        file_path = _get_txt_file_path()
        try:
            response = llm.chat(messages, **kwargs)
            _log_interaction(file_path, "chat", messages, response=response)
            return response
        except Exception as e:
            _log_interaction(file_path, "chat", messages, error=e)
            raise

    async def achat(self, messages, **kwargs):
        llm = object.__getattribute__(self, "_llm")
        file_path = _get_txt_file_path()
        try:
            response = await llm.achat(messages, **kwargs)
            _log_interaction(file_path, "achat", messages, response=response)
            return response
        except Exception as e:
            _log_interaction(file_path, "achat", messages, error=e)
            raise

    def complete(self, prompt, **kwargs):
        llm = object.__getattribute__(self, "_llm")
        file_path = _get_txt_file_path()
        fake_msgs = [{"role": "user", "content": str(prompt)}]
        try:
            response = llm.complete(prompt, **kwargs)
            _log_interaction(file_path, "complete", fake_msgs, response=response)
            return response
        except Exception as e:
            _log_interaction(file_path, "complete", fake_msgs, error=e)
            raise

    async def acomplete(self, prompt, **kwargs):
        llm = object.__getattribute__(self, "_llm")
        file_path = _get_txt_file_path()
        fake_msgs = [{"role": "user", "content": str(prompt)}]
        try:
            response = await llm.acomplete(prompt, **kwargs)
            _log_interaction(file_path, "acomplete", fake_msgs, response=response)
            return response
        except Exception as e:
            _log_interaction(file_path, "acomplete", fake_msgs, error=e)
            raise

    async def astream_chat_with_tools(self, tools, chat_history=None, **kwargs):
        """
        Wraps the streaming astream_chat_with_tools call.

        LlamaIndex callers do:
            resp_gen = await llm.astream_chat_with_tools(...)
            async for chunk in resp_gen: ...

        So this method must be a regular `async def` that *returns* an async
        generator — NOT itself an async generator (which you cannot `await`).
        """
        llm = object.__getattribute__(self, "_llm")
        # Get the real async-generator object from the underlying LLM
        real_gen = await llm.astream_chat_with_tools(
            tools, chat_history=chat_history, **kwargs
        )

        file_path = _get_txt_file_path()
        messages = chat_history or []

        async def _logged_gen():
            last_resp = None
            error_caught = None
            try:
                async for chunk in real_gen:
                    last_resp = chunk  # last chunk contains the fully assembled response
                    yield chunk
            except Exception as e:
                error_caught = e
                _log_interaction(
                    file_path, "astream_chat_with_tools", messages, error=e
                )
                raise
            finally:
                if error_caught is None:
                    _log_interaction(
                        file_path,
                        "astream_chat_with_tools",
                        messages,
                        response=last_resp,
                    )

        return _logged_gen()


def apply_logging_to_llm(llm):
    """
    Returns a LoggingLLMWrapper around the provided LLM.
    All original attributes and methods are transparently proxied;
    chat / achat / complete / acomplete / astream_chat_with_tools are logged.
    """
    return LoggingLLMWrapper(llm)
