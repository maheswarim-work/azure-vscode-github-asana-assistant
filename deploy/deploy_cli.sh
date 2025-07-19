#!/bin/bash

# Azure CLI deployment script for the AI Assistant

set -e

# Configuration
RESOURCE_GROUP_NAME="ai-assistant-rg"
LOCATION="eastus"
APP_NAME="asana-github-assistant-$(date +%s | tail -c 6)"
STORAGE_NAME="storage$(date +%s | tail -c 10)"
EXISTING_KV_NAME="aiassistantkv57994"

echo "🚀 Starting Azure deployment with Azure CLI..."
echo "App Name: $APP_NAME"
echo "Storage Name: $STORAGE_NAME"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    exit 1
fi

# Login check
echo "🔐 Checking Azure login status..."
if ! az account show &> /dev/null; then
    echo "Please login to Azure..."
    az login
fi

# Create storage account
echo "💾 Creating storage account: $STORAGE_NAME"
az storage account create \
    --name $STORAGE_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --location $LOCATION \
    --sku Standard_LRS \
    --kind StorageV2

# Create Function App with consumption plan
echo "⚡ Creating Function App: $APP_NAME"
az functionapp create \
    --resource-group $RESOURCE_GROUP_NAME \
    --consumption-plan-location $LOCATION \
    --runtime python \
    --runtime-version 3.11 \
    --functions-version 4 \
    --name $APP_NAME \
    --storage-account $STORAGE_NAME \
    --os-type Linux \
    --disable-app-insights false

# Get Function App details
echo "📋 Getting Function App details..."
FUNCTION_APP_PRINCIPAL_ID=$(az functionapp identity show \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --query principalId \
    --output tsv)

FUNCTION_APP_URL="https://$APP_NAME.azurewebsites.net"

echo "✅ Function App created successfully!"
echo "📱 Function App Name: $APP_NAME"
echo "🌐 Function App URL: $FUNCTION_APP_URL"
echo "🆔 Principal ID: $FUNCTION_APP_PRINCIPAL_ID"

# Configure Key Vault access
echo "🔗 Configuring Key Vault access..."
az role assignment create \
    --assignee "$FUNCTION_APP_PRINCIPAL_ID" \
    --role "Key Vault Secrets User" \
    --scope "/subscriptions/$(az account show --query id --output tsv)/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.KeyVault/vaults/$EXISTING_KV_NAME"

# Configure app settings
echo "⚙️  Configuring Function App settings..."
az functionapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --settings \
    "USE_KEY_VAULT=true" \
    "AZURE_KEY_VAULT_URL=https://$EXISTING_KV_NAME.vault.azure.net/" \
    "ASANA_ACCESS_TOKEN=@Microsoft.KeyVault(VaultName=$EXISTING_KV_NAME;SecretName=asana-access-token)" \
    "GITHUB_TOKEN=@Microsoft.KeyVault(VaultName=$EXISTING_KV_NAME;SecretName=github-token)" \
    "OPENAI_API_KEY=@Microsoft.KeyVault(VaultName=$EXISTING_KV_NAME;SecretName=openai-api-key)" \
    "OPENAI_MODEL=gpt-4" \
    "MAX_TOKENS=2000" \
    "TEMPERATURE=0.7"

# Build and deploy function code
echo "📦 Building and deploying function code..."

# Create deployment package
TEMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TEMP_DIR"

# Copy essential files
cp -r src/ $TEMP_DIR/
cp -r azure/ $TEMP_DIR/
cp pyproject.toml $TEMP_DIR/ || true

cd $TEMP_DIR

# Create requirements.txt for Azure Functions
cat > requirements.txt << 'EOF'
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
httpx>=0.25.0
python-dotenv>=1.0.0
openai>=1.0.0
asana>=3.2.0
PyGithub>=1.59.0
azure-functions>=1.18.0
azure-identity>=1.15.0
azure-keyvault-secrets>=4.7.0
pydantic-settings>=2.1.0
EOF

# Copy function app files to root
cp azure/* . 2>/dev/null || true

# Create deployment zip
echo "Creating deployment package..."
zip -r ../function-app.zip . -x "*.pyc" "__pycache__/*" "tests/*" "*.git*" "azure/*"

cd ..

# Deploy using zip
echo "🚀 Deploying function code..."
az functionapp deployment source config-zip \
    --resource-group $RESOURCE_GROUP_NAME \
    --name $APP_NAME \
    --src function-app.zip

# Wait for deployment to complete
echo "⏳ Waiting for deployment to complete..."
sleep 30

# Clean up
rm -rf $TEMP_DIR function-app.zip

echo ""
echo "🎉 Deployment completed successfully!"
echo "=================================="
echo "🌐 Your AI Assistant is available at: $FUNCTION_APP_URL"
echo "📚 API Documentation: $FUNCTION_APP_URL/api/docs"
echo ""
echo "🔑 Next Steps:"
echo "1. Add your API keys to Key Vault:"
echo "   python scripts/setup_keyvault.py setup --key-vault-url https://$EXISTING_KV_NAME.vault.azure.net/"
echo ""
echo "2. Test the health endpoint:"
echo "   curl $FUNCTION_APP_URL/api/health"
echo ""
echo "3. Test a command:"
echo "   curl -X POST $FUNCTION_APP_URL/api/command -H 'Content-Type: application/json' -d '{\"command\": \"Hello!\"}'"
echo ""
echo "📋 Function App Details:"
echo "   Name: $APP_NAME"
echo "   Resource Group: $RESOURCE_GROUP_NAME"
echo "   Key Vault: $EXISTING_KV_NAME"
echo "   Storage Account: $STORAGE_NAME"
echo ""