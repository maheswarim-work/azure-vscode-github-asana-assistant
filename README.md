# Azure VSCode GitHub Asana Assistant

An AI-powered assistant that seamlessly integrates Asana task management, GitHub repositories, and VSCode development environment, deployed on Azure for scalable cloud access.

## Features

- **🎯 Asana Integration**: Create, update, and manage tasks and projects
- **🐙 GitHub Integration**: Handle issues, pull requests, and repository operations
- **🔧 VSCode Integration**: Manage workspaces, settings, and development environment
- **🤖 AI-Powered**: Natural language processing for intelligent automation
- **☁️ Azure Deployment**: Scalable cloud deployment with secure secret management
- **🔄 Real-time Sync**: Bidirectional synchronization between platforms
- **📝 Webhook Support**: Real-time updates from Asana and GitHub

## Quick Start

### 1. Setup API Keys

Create a `.env` file from the example:
```bash
cp .env.example .env
```

Update the following required API keys:
- **Asana**: Get your Personal Access Token from [Asana Developer Console](https://app.asana.com/0/developer-console)
- **GitHub**: Create a Personal Access Token with repo permissions
- **OpenAI**: Get your API key from [OpenAI Platform](https://platform.openai.com/)

⚠️ **Security Note**: Never commit your `.env` file or expose API keys in code. Use environment variables or Azure Key Vault in production.

### 2. Local Development

```bash
# Install dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Run the API server
python -m uvicorn src.assistant.api.main:app --reload

# Or use the Azure Functions runtime
cd azure && func start
```

### 3. Azure Deployment

```bash
# Deploy to Azure (requires Azure CLI)
./deploy/deploy.sh
```

## Usage Examples

### Deployed Azure Function App

The AI assistant is deployed as an Azure Function App. 

⚠️ **Security Note**: Azure Functions require authentication. Get your function key from:
```bash
az functionapp keys list --name YOUR_FUNCTION_APP_NAME --resource-group YOUR_RESOURCE_GROUP
```

### Natural Language Commands

```bash
# Process AI commands (replace YOUR_FUNCTION_KEY with actual key)
curl -X POST "https://YOUR_FUNCTION_APP.azurewebsites.net/api/command?code=YOUR_FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command": "Create a task for implementing user authentication"}'

# AI analyzes intent and routes to appropriate platform
curl -X POST "https://YOUR_FUNCTION_APP.azurewebsites.net/api/command?code=YOUR_FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command": "Show me all my overdue GitHub issues"}'

# Cross-platform automation
curl -X POST "https://YOUR_FUNCTION_APP.azurewebsites.net/api/command?code=YOUR_FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command": "Sync my sprint tasks from Asana to GitHub issues"}'
```

### Azure Function Endpoints

```bash
# Health check
curl "https://YOUR_FUNCTION_APP.azurewebsites.net/api/health?code=YOUR_FUNCTION_KEY"

# Get status from all platforms
curl "https://YOUR_FUNCTION_APP.azurewebsites.net/api/status?code=YOUR_FUNCTION_KEY"

# Direct platform sync
curl -X POST "https://YOUR_FUNCTION_APP.azurewebsites.net/api/sync?code=YOUR_FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "source_platform": "asana",
    "target_platform": "github", 
    "source_id": "task_gid",
    "additional_params": {"repo_name": "my-repository"}
  }'

# Webhook endpoints for real-time updates
POST /api/webhooks/asana
POST /api/webhooks/github
```

### Example AI Command Processing

The AI assistant understands natural language and automatically:

1. **Analyzes Intent**: "Create a GitHub issue for the login bug" → Intent: create_github_issue
2. **Extracts Parameters**: title="login bug", type="issue", platform="github"  
3. **Routes Action**: Calls GitHub integration to create issue
4. **Returns Result**: Structured response with success/failure and details

```json
{
  "success": true,
  "intent": {
    "intent": "create_github_issue",
    "platform": "github", 
    "action": "create_issue",
    "parameters": {"title": "login bug"},
    "confidence": 0.95
  },
  "result": {
    "issue_number": 42,
    "url": "https://github.com/user/repo/issues/42"
  },
  "timestamp": "2025-07-19T21:48:31.021156"
}
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Asana       │    │     GitHub      │    │     VSCode      │
│   Integration   │    │   Integration   │    │   Integration   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      AI Assistant Core    │
                    │    (OpenAI Integration)   │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      FastAPI Server      │
                    │    (REST API Endpoints)   │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    Azure Functions       │
                    │   (Cloud Deployment)     │
                    └───────────────────────────┘
```

## Development Commands

```bash
# Run tests
pytest

# Code formatting
black src/ tests/

# Linting
ruff check src/ tests/

# Type checking
mypy src/

# Install pre-commit hooks
pre-commit install
```

## API Documentation

Once running, visit:
- Local: http://localhost:8000/docs
- Azure: https://your-function-app.azurewebsites.net/api/docs

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

### Azure Key Vault Integration

The application uses Azure Key Vault for secure secret management with automatic fallback to environment variables.

#### Setup Key Vault Secrets

**Option 1: Interactive Setup Script (Recommended)**
```bash
# Set up all secrets interactively
python scripts/setup_keyvault.py setup

# Or provide secrets as arguments
python scripts/setup_keyvault.py setup \
  --key-vault-url https://your-keyvault.vault.azure.net/ \
  --asana-token "your-asana-token" \
  --github-token "your-github-token" \
  --openai-key "your-openai-key"
```

**Option 2: Azure CLI**
```bash
az keyvault secret set --vault-name your-keyvault --name asana-access-token --value "your-token"
az keyvault secret set --vault-name your-keyvault --name github-token --value "your-token"
az keyvault secret set --vault-name your-keyvault --name openai-api-key --value "your-key"
```

#### Manage Key Vault Secrets
```bash
# List all secrets
python scripts/setup_keyvault.py list

# Get a specific secret (value hidden for security)
python scripts/setup_keyvault.py get --secret-name asana-access-token

# Delete a secret
python scripts/setup_keyvault.py delete --secret-name old-secret
```

#### Key Vault Authentication

The application supports multiple authentication methods:

1. **Service Principal** (Recommended for production)
   ```bash
   export AZURE_TENANT_ID="your-tenant-id"
   export AZURE_CLIENT_ID="your-client-id"
   export AZURE_CLIENT_SECRET="your-client-secret"
   ```

2. **Azure CLI** (For local development)
   ```bash
   az login
   ```

3. **Managed Identity** (Automatic in Azure Functions)

#### Fallback Behavior

- **Key Vault Available**: Secrets are retrieved from Key Vault with caching
- **Key Vault Unavailable**: Falls back to environment variables
- **Local Development**: Use `USE_KEY_VAULT=false` to disable Key Vault

## Integration Examples

### Asana ↔ GitHub Sync

Automatically sync tasks and issues:
- Create GitHub issues from Asana tasks
- Update task status when issues are closed
- Sync comments and attachments

### VSCode Workspace Management

- Auto-configure project settings
- Install recommended extensions
- Setup debugging configurations
- Manage git workflows

## Security

### API Key Management
- **Local Development**: Use `.env` file (never commit this file)
- **Production**: Use Azure Key Vault for secure secret storage
- **CI/CD**: Use GitHub Secrets or Azure DevOps variable groups

### Best Practices
- Rotate API keys regularly
- Use least-privilege access for tokens
- Monitor API usage for unusual activity
- Enable 2FA on all integrated accounts

### Secure Files (Auto-ignored)
The following files are automatically ignored by git:
- **Environment files**: `.env`, `.env.*`, `.env.local`, `.env.prod`, etc. (except `.env.example`)
- **Azure configs**: `azure_config.env`, `azure_config_*.env`, `.azure/`, `azure.json`
- **Certificates**: `*.key`, `*.pem`, `*.p12`, `*.pfx`, `*.credentials`
- **Secret files**: `secrets.json`, `config.json`
- **Local settings**: `local.settings.json` (except the Azure template)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

⚠️ **Important**: Never commit sensitive information like API keys, tokens, or credentials.

## License

MIT License - see LICENSE file for details.
