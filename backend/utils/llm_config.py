import os
from llama_index.llms.openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    """
    Returns a configured LLM instance based on environment variables.
    Supports either standard OpenAI API or an OpenAI-compatible vLLM endpoint (e.g., for Phi-4).
    """
    llm_binding = os.getenv("LLM_BINDING", "openai").lower()
    
    if llm_binding == "vllm":
        # Connect to a local or remote OpenAI-compatible vLLM endpoint
        model = os.getenv("LLM_MODEL", "microsoft/phi-4")
        api_base = os.getenv("VLLM_API_HOST", "http://localhost:8000/v1")
        # vLLM usually accepts a dummy key if auth is disabled
        api_key = os.getenv("VLLM_API_KEY", "dummy-key")
        
        return OpenAI(
            model=model,
            api_base=api_base,
            api_key=api_key,
            temperature=0
        )
    else:
        # Default standard OpenAI
        model = os.getenv("LLM_MODEL", "gpt-4o")
        # It picks up OPENAI_API_KEY automatically from environment
        return OpenAI(model=model, temperature=0)
