# PopCash Backend - Intelligence Orchestrator

The PopCash backend is a high-performance FastAPI application that serves as the "Intelligence Orchestrator" for the entire platform. It leverages LlamaIndex and OpenAI to coordinate specialized AI agents that provide smart financial insights and gamified rewards management.

## 🏗️ Technology Stack

- **Framework**: FastAPI (Python)
- **AI Orchestration**: LlamaIndex
- **LLM**: OpenAI (GPT-4o-mini)
- **Data Modeling**: Pydantic
- **Data Storage**: CSV-based datasets (16 core entities)

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.9 or higher
- OpenAI API Key

### 2. Install Dependencies
The backend uses `uv` for lightning-fast dependency management. Navigate to the `backend` directory and run:

```bash
uv sync
```
This will automatically create a virtual environment and install all dependencies from `pyproject.toml`.

### 3. Configure Environment
Create a `.env` file from the sample and add your API key:

```bash
cp .env.sample .env
```

Edit the `.env` file:
```env
LLM_BINDING=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_HOST=https://api.openai.com/v1
OPENAI_API_KEY=your_openai_api_key_here
```

## ▶️ Running the Server

```bash
uv run python main.py
```

The backend server will start at: **http://localhost:9000**

## 📂 Project Structure

- `agents/`: Contains AI agent implementations, tools, and data models.
- `dataset/`: Storage for the 16 CSV entities used for data retrieval.
- `main.py`: Entry point for the FastAPI application and agent orchestration.

## 🔌 API Endpoints

- **GET `/health`**: Check system status.
- **POST `/run`**: Main interaction endpoint for the AI agents.
- **`/docs`**: Interactive Swagger UI documentation.
