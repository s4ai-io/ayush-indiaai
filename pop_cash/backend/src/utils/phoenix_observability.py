from phoenix.otel import register
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from openinference.instrumentation.openai import OpenAIInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
import phoenix as px

# Global flag to prevent double instrumentation
_phoenix_initialized = False

def setup_phoenix(project_name: str = "default"):
    """
    Configures and initializes the Phoenix tracer for observability.
    
    Args:
        project_name (str): The name of the project in Phoenix. Defaults to "default".
    """
    global _phoenix_initialized
    
    if _phoenix_initialized:
        print("[DEBUG] Phoenix already initialized, skipping setup")
        return None
    
    
    # Configure the Phoenix tracer
    tracer_provider = register(
        project_name=project_name
    )
    
    # Set as global tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    # Instrument OpenAI first (most important for token tracking)
    try:
        OpenAIInstrumentor().instrument(
            tracer_provider=tracer_provider,
            skip_dep_check=True
        )
        print("[DEBUG] ✅ OpenAI instrumentation enabled")
    except Exception as e:
        print(f"[DEBUG] ⚠️ OpenAI instrumentation failed: {e}")
    
    # Instrument LlamaIndex with tracer provider
    try:
        LlamaIndexInstrumentor().instrument(
            tracer_provider=tracer_provider,
            skip_dep_check=True
        )
        print("[DEBUG] ✅ LlamaIndex instrumentation enabled")
    except Exception as e:
        print(f"[DEBUG] ⚠️ LlamaIndex instrumentation failed: {e}")
    
    _phoenix_initialized = True
    try:
        px.launch_app()
        
    except Exception as e:
        print(f"[DEBUG] ⚠️ Phoenix launch failed: {e}")


    print(f"[DEBUG] Phoenix initialized for project: {project_name}")
    print(f"[DEBUG] Traces will be sent to: http://localhost:4317 (gRPC)")
    print(f"[DEBUG] Global tracer provider set")
    return tracer_provider

def close_phoenix():
    try:
        global _phoenix_initialized
        if _phoenix_initialized:
            px.close_app()
            _phoenix_initialized = False
    except Exception as e:
        print(f"[DEBUG] ⚠️ Phoenix close failed: {e}")
