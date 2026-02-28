import os
import datetime
import threading
from typing import Any, AsyncGenerator, List, Optional

# ── Thread-local run_id ────────────────────────────────────────────────────────
# Set by AGUIChatWorkflow before every LLM call so llm_logger can attach the
# vllm_phi4 step to the matching voice-pipeline run JSON.
_run_id_local = threading.local()


def set_current_run_id(run_id: str | None) -> None:
    """Call this from AGUIChatWorkflow.chat() to bind a run_id to the current thread."""
    _run_id_local.run_id = run_id


def get_current_run_id() -> str | None:
    return getattr(_run_id_local, "run_id", None)

# Setup base logs directory relative to this file
# backend/utils/llm_logger.py -> backend/logs/model_interactions/
LOGS_BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs",
    "model_interactions",
)

# ── Session-level file ──────────────────────────────────────────────────────
# One file is created per backend session (at import time).
# All interactions are appended to this single file.
# Format: YYYY-MM-DD_HH-MM-SS_<model>.txt

_SESSION_FILE: str | None = None  # populated lazily on first call


def _ensure_log_dir():
    """Ensure the base logging directory exists."""
    os.makedirs(LOGS_BASE_DIR, exist_ok=True)


def _get_session_file(model_name: str) -> str:
    """
    Return the single session-level log file path.
    Created once per backend process (PID), reused for every subsequent call.
    PID is included so uvicorn reload=True (reloader + worker) each get separate files.
    """
    global _SESSION_FILE
    if _SESSION_FILE is None:
        _ensure_log_dir()
        safe_model = model_name.replace("/", "_").replace("\\", "_")
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        pid = os.getpid()
        _SESSION_FILE = os.path.join(LOGS_BASE_DIR, f"{ts}_pid{pid}_{safe_model}.txt")
        # Write session header
        try:
            with open(_SESSION_FILE, "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write(f"SESSION STARTED\n")
                f.write(f"Model:     {model_name}\n")
                f.write(f"PID:       {pid}\n")
                f.write(
                    f"Started:   {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write("=" * 60 + "\n\n")
        except Exception as e:
            print(f"[llm_logger] Failed to write session header: {e}")
    return _SESSION_FILE


# ── Serialisation helpers ───────────────────────────────────────────────────

def _messages_to_txt(messages) -> str:
    """Safely serialize LlamaIndex ChatMessage objects (or dicts) to text."""
    if not isinstance(messages, (list, tuple)):
        return str(messages)

    lines = []
    for msg in messages:
        try:
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
    if hasattr(response, "message"):
        msg = response.message
        role = str(getattr(msg, "role", "assistant"))
        content = str(getattr(msg, "content", ""))
        additional = getattr(msg, "additional_kwargs", {})
        tool_calls = additional.get("tool_calls", [])
        out = f"Role: {role}\nContent: {content}\n"
        if tool_calls:
            out += f"Tool Calls: {tool_calls}\n"
        return out
    if hasattr(response, "text"):
        return f"Text: {response.text}\n"
    return str(response)


# ── Core append writer ──────────────────────────────────────────────────────

def _log_interaction(file_path: str, type_label: str, messages, response=None, error=None):
    """Append one interaction block to the session log file."""
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write("-" * 60 + "\n")
            f.write(f"Type:      {type_label}\n")
            f.write(
                f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n"
            )
            f.write("-" * 60 + "\n\n")

            # Input messages
            f.write("--- INPUT ---\n")
            f.write(_messages_to_txt(messages))
            f.write("\n\n")

            # Output
            if response is not None:
                f.write("--- OUTPUT ---\n")
                f.write(_response_to_txt(response))
                f.write("\n")

            # Error
            if error is not None:
                f.write("--- ERROR ---\n")
                f.write(f"{type(error).__name__}: {str(error)}\n")

            f.write("\n")  # blank line between entries

    except Exception as e:
        print(f"[llm_logger] Failed to write log: {e}")


def _append_vllm_step(messages, response=None, error=None) -> None:
    """
    If a voice-pipeline run_id is bound to the current thread, load its
    existing run JSON and append the vllm_phi4 step, then flush to disk.
    """
    run_id = get_current_run_id()
    if not run_id:
        return
    try:
        from utils.run_logger import RunLogger
        rl = RunLogger.load_existing(run_id)
        if rl is None:
            return
        # Serialize input messages
        msgs_serialized = []
        for msg in (messages if isinstance(messages, (list, tuple)) else []):
            try:
                role = str(getattr(msg, "role", None) or msg.get("role", "unknown"))
                content = getattr(msg, "content", None)
                if content is None:
                    content = msg.get("content", str(msg))
                msgs_serialized.append({"role": role, "content": str(content)})
            except Exception:
                msgs_serialized.append({"raw": str(msg)})

        # Serialize output
        output_data = None
        if response is not None:
            output_data = {"raw": _response_to_txt(response)}

        error_str = f"{type(error).__name__}: {error}" if error else None

        rl.update_step(
            "vllm_phi4",
            input={"messages": msgs_serialized, "message_count": len(msgs_serialized)},
            output=output_data,
            error=error_str,
        )
        rl.finalize()
    except Exception as exc:
        print(f"[llm_logger] _append_vllm_step failed: {exc}")


# ── Wrapper ─────────────────────────────────────────────────────────────────

class LoggingLLMWrapper:
    """
    A transparent proxy around a LlamaIndex LLM that logs every
    chat / achat / complete / acomplete / astream_chat_with_tools call
    into a SINGLE session log file (appended, not overwritten).
    """

    def __init__(self, llm):
        object.__setattr__(self, "_llm", llm)
        model_name = getattr(llm, "model", None) or type(llm).__name__
        object.__setattr__(self, "_model_name", str(model_name))
        # Eagerly create the session file so the header appears at startup
        _get_session_file(str(model_name))

    # ------------------------------------------------------------------ #
    #  Transparent attribute pass-through                                  #
    # ------------------------------------------------------------------ #
    @property
    def __class__(self):
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
    def _file(self) -> str:
        """Return the shared session file path."""
        return _get_session_file(object.__getattribute__(self, "_model_name"))

    def chat(self, messages, **kwargs):
        llm = object.__getattribute__(self, "_llm")
        try:
            response = llm.chat(messages, **kwargs)
            _log_interaction(self._file(), "chat", messages, response=response)
            _append_vllm_step(messages, response=response)
            return response
        except Exception as e:
            _log_interaction(self._file(), "chat", messages, error=e)
            _append_vllm_step(messages, error=e)
            raise

    async def achat(self, messages, **kwargs):
        llm = object.__getattribute__(self, "_llm")
        try:
            response = await llm.achat(messages, **kwargs)
            _log_interaction(self._file(), "achat", messages, response=response)
            _append_vllm_step(messages, response=response)
            return response
        except Exception as e:
            _log_interaction(self._file(), "achat", messages, error=e)
            _append_vllm_step(messages, error=e)
            raise

    def complete(self, prompt, **kwargs):
        llm = object.__getattribute__(self, "_llm")
        fake_msgs = [{"role": "user", "content": str(prompt)}]
        try:
            response = llm.complete(prompt, **kwargs)
            _log_interaction(self._file(), "complete", fake_msgs, response=response)
            _append_vllm_step(fake_msgs, response=response)
            return response
        except Exception as e:
            _log_interaction(self._file(), "complete", fake_msgs, error=e)
            _append_vllm_step(fake_msgs, error=e)
            raise

    async def acomplete(self, prompt, **kwargs):
        llm = object.__getattribute__(self, "_llm")
        fake_msgs = [{"role": "user", "content": str(prompt)}]
        try:
            response = await llm.acomplete(prompt, **kwargs)
            _log_interaction(self._file(), "acomplete", fake_msgs, response=response)
            _append_vllm_step(fake_msgs, response=response)
            return response
        except Exception as e:
            _log_interaction(self._file(), "acomplete", fake_msgs, error=e)
            _append_vllm_step(fake_msgs, error=e)
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
        real_gen = await llm.astream_chat_with_tools(
            tools, chat_history=chat_history, **kwargs
        )

        file_path = self._file()
        messages = chat_history or []

        async def _logged_gen():
            last_resp = None
            error_caught = None
            try:
                async for chunk in real_gen:
                    last_resp = chunk
                    yield chunk
            except Exception as e:
                error_caught = e
                _log_interaction(file_path, "astream_chat_with_tools", messages, error=e)
                _append_vllm_step(messages, error=e)
                raise
            finally:
                if error_caught is None:
                    _log_interaction(
                        file_path,
                        "astream_chat_with_tools",
                        messages,
                        response=last_resp,
                    )
                    _append_vllm_step(messages, response=last_resp)

        return _logged_gen()


# ── Public API ──────────────────────────────────────────────────────────────

def apply_logging_to_llm(llm):
    """
    Returns a LoggingLLMWrapper around the provided LLM.
    All original attributes and methods are transparently proxied;
    chat / achat / complete / acomplete / astream_chat_with_tools are logged
    into a single session file.
    """
    return LoggingLLMWrapper(llm)
