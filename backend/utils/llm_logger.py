import os
import datetime
from functools import wraps

# Setup base logs directory relative to this file
# backend/utils/llm_logger.py -> backend/logs/model_interactions/
LOGS_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "model_interactions")

def _ensure_log_dir():
    """Ensure the base logging directory exists."""
    os.makedirs(LOGS_BASE_DIR, exist_ok=True)

def _get_txt_file_path() -> str:
    """Get a new text file path for the current interaction with a timestamp."""
    _ensure_log_dir()
    # Format: YYYY-MM-DD_HH-MM-SS-mmm.txt
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]
    return os.path.join(LOGS_BASE_DIR, f"{timestamp}_OpenAI.txt")

def _list_to_txt(messages):
    """Safely serialize LlamaIndex ChatMessage objects to text."""
    lines = []
    if not isinstance(messages, (list, tuple)):
        # If it's a single prompt string or basic object
        return str(messages)
        
    for msg in messages:
        try:
            role = getattr(msg, "role", str(type(msg)))
            content = getattr(msg, "content", str(msg))
            lines.append(f"Role: {role}\nContent: {content}\n")
        except Exception:
            lines.append(str(msg))
    return "\n".join(lines)

def _log_interaction(file_path, type_label, messages, response=None, error=None):
    """Write input, output, and/or error to a single txt file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("="*50 + "\n")
            f.write(f"Type: {type_label}\n")
            f.write(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n")
            f.write("="*50 + "\n\n")
            
            # Write input
            f.write("--- INPUT ---\n")
            f.write(_list_to_txt(messages))
            f.write("\n\n")
            
            # Write output
            if response:
                f.write("--- OUTPUT ---\n")
                if hasattr(response, "message"):
                    role = str(getattr(response.message, "role", "assistant"))
                    content = str(getattr(response.message, "content", ""))
                    f.write(f"Role: {role}\nContent: {content}\n")
                else:
                    f.write(str(response) + "\n")
                    
            if error:
                f.write("--- ERROR ---\n")
                f.write(f"{type(error).__name__}: {str(error)}\n")
                
    except Exception as e:
        print(f"Failed to log LLM interaction: {e}")

def apply_logging_to_llm(llm):
    """
    Wraps an LLM's chat and achat methods to intercept and log inputs/outputs.
    """
    # Keep references to original methods
    original_chat = getattr(llm, "chat", None)
    original_achat = getattr(llm, "achat", None)

    if original_chat:
        @wraps(original_chat)
        def logged_chat(messages, **kwargs):
            file_path = _get_txt_file_path()
            try:
                response = original_chat(messages, **kwargs)
                _log_interaction(file_path, "LLM (OpenAI)", messages, response=response)
                return response
            except Exception as e:
                _log_interaction(file_path, "LLM (OpenAI)", messages, error=e)
                raise
        object.__setattr__(llm, "chat", logged_chat)

    if original_achat:
        @wraps(original_achat)
        async def logged_achat(messages, **kwargs):
            file_path = _get_txt_file_path()
            try:
                response = await original_achat(messages, **kwargs)
                _log_interaction(file_path, "LLM (OpenAI)", messages, response=response)
                return response
            except Exception as e:
                _log_interaction(file_path, "LLM (OpenAI)", messages, error=e)
                raise
        object.__setattr__(llm, "achat", logged_achat)

    # We also might want to log complete / acomplete if used heavily by LlamaIndex internally
    original_complete = getattr(llm, "complete", None)
    original_acomplete = getattr(llm, "acomplete", None)
    
    if original_complete:
        @wraps(original_complete)
        def logged_complete(prompt, **kwargs):
            file_path = _get_txt_file_path()
            try:
                response = original_complete(prompt, **kwargs)
                # For `complete`, prompt is a string, response is a CompletionResponse
                _log_interaction(file_path, "LLM (OpenAI)", [{"role": "user", "content": str(prompt)}], response=response)
                return response
            except Exception as e:
                _log_interaction(file_path, "LLM (OpenAI)", [{"role": "user", "content": str(prompt)}], error=e)
                raise
        object.__setattr__(llm, "complete", logged_complete)
        
    if original_acomplete:
        @wraps(original_acomplete)
        async def logged_acomplete(prompt, **kwargs):
            file_path = _get_txt_file_path()
            try:
                response = await original_acomplete(prompt, **kwargs)
                _log_interaction(file_path, "LLM (OpenAI)", [{"role": "user", "content": str(prompt)}], response=response)
                return response
            except Exception as e:
                _log_interaction(file_path, "LLM (OpenAI)", [{"role": "user", "content": str(prompt)}], error=e)
                raise
        object.__setattr__(llm, "acomplete", logged_acomplete)
    
    return llm
