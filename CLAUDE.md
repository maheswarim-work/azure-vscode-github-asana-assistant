# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project for an Azure VS Code GitHub Asana Assistant. The repository is currently in its initial state with minimal structure.

## Project Structure

Currently minimal - only contains:
- `README.md` - Basic project description
- `.gitignore` - Comprehensive Python gitignore template

## Development Setup

This is a Python project using modern tooling with pyproject.toml configuration.

```bash
# Virtual environment setup
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting and linting
black src/ tests/
ruff check src/ tests/
mypy src/

# Run the API server locally
python -m uvicorn src.assistant.api.main:app --reload

# Run Azure Functions locally
cd azure && func start
```

## Architecture Notes

This is an AI-powered assistant with the following structure:

```
src/assistant/
├── __init__.py
├── config.py              # Pydantic settings configuration
├── ai/
│   ├── __init__.py
│   └── assistant_core.py   # Core AI logic with OpenAI integration
├── integrations/
│   ├── __init__.py
│   ├── asana_client.py     # Asana API integration
│   ├── github_client.py    # GitHub API integration
│   └── vscode_integration.py # VSCode workspace management
└── api/
    ├── __init__.py
    └── main.py             # FastAPI REST API endpoints

azure/
├── function_app.py         # Azure Functions entry point
├── requirements.txt        # Azure Functions dependencies
├── host.json              # Functions runtime configuration
└── local.settings.json    # Local development settings

deploy/
├── bicep/
│   └── main.bicep         # Azure infrastructure as code
└── deploy.sh              # Deployment script
```

## Key Components

1. **AI Assistant Core** (`src/assistant/ai/assistant_core.py`): Main logic using OpenAI GPT for natural language processing
2. **Integration Modules**: Separate clients for Asana, GitHub, and VSCode operations
3. **FastAPI Server** (`src/assistant/api/main.py`): REST API with endpoints for all operations
4. **Azure Functions** (`azure/function_app.py`): Cloud deployment with serverless functions
5. **Infrastructure** (`deploy/bicep/main.bicep`): Azure resources including Key Vault for secrets

## Configuration

- Environment variables defined in `config.py` using Pydantic Settings
- Secrets managed via Azure Key Vault in production
- Local development uses `.env` file

## Azure Deployment

Deploy with: `./deploy/deploy.sh`

Creates:
- Azure Function App
- Key Vault for secure secret storage
- Application Insights for monitoring
- Storage Account for function runtime