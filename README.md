# Agentic Infrastructure Platform

A bounded, tool-using assistant for Jira, GitHub, and Confluence. It accepts a natural-language request through a terminal chat or FastAPI, asks a configurable Hydra/LiteLLM or Groq model to choose tools, validates the proposed action, and runs the integration through MCP servers.

Start with the [Project Guide](PROJECT_GUIDE.md) for the architecture, setup, configuration, files, supported actions, and known limitations.

## Quick start

1. Install Python 3.10 or newer and create/activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and fill in the values for the services you will use. Keep `.env` private.
4. Start the terminal interface with `python -m app.chat`, or the HTTP API with `uvicorn app.main:app --reload`.

Set `LLM_PROVIDER=hydra` or `LLM_PROVIDER=groq` in `.env` to select the model provider. The application process must be running to receive requests and execute tools. Continue.dev is a separate client; this project connects to Hydra using the endpoint and model alias configured in its own `.env`.
