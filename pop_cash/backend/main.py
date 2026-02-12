import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
import os
from src.utils.phoenix_observability import setup_phoenix, close_phoenix 
load_dotenv(override=True)
print(os.environ['OPENAI_API_KEY'])
from src.agent import agentic_chat_router
from src.clinical_agent import clinical_agent_router
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starting up: Connecting to Phoenix...")
    setup_phoenix('PopCash')
    yield
    print("Application shutting down: Closing Phoenix connection...")
    close_phoenix()

app = FastAPI(lifespan=lifespan)
app.include_router(agentic_chat_router)
app.include_router(clinical_agent_router, prefix="/api/copilot/clinical")


def main():
    
    uvicorn.run("main:app", host="127.0.0.1", port=9000, reload=True)


if __name__ == "__main__":
    main()

