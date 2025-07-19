#!/bin/bash

# Simple Azure deployment script for the AI Assistant

set -e

# Configuration - Use existing resource group to avoid quota issues
RESOURCE_GROUP_NAME="ai-assistant-rg"
LOCATION="eastus"
APP_NAME="asana-github-assistant"
EXISTING_KV_NAME="aiassistantkv57994"
EXISTING_KV_RG="ai-assistant-rg"

echo "🚀 Starting Azure deployment..."

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    exit 1
fi

# Login to Azure (if not already logged in)
echo "🔐 Checking Azure login status..."
if ! az account show &> /dev/null; then
    echo "Please login to Azure..."
    az login
fi

# Use existing resource group
echo "📦 Using existing resource group: $RESOURCE_GROUP_NAME"

# Deploy the Bicep template
echo "🏗️  Deploying Azure resources..."
DEPLOYMENT_OUTPUT=$(az deployment group create \
    --resource-group $RESOURCE_GROUP_NAME \
    --template-file deploy/bicep/main_fixed.bicep \
    --parameters appName=$APP_NAME \
    --query 'properties.outputs' \
    --output json)

# Extract outputs
FUNCTION_APP_NAME=$(echo $DEPLOYMENT_OUTPUT | jq -r '.functionAppName.value')
FUNCTION_APP_URL=$(echo $DEPLOYMENT_OUTPUT | jq -r '.functionAppUrl.value')
FUNCTION_APP_PRINCIPAL_ID=$(echo $DEPLOYMENT_OUTPUT | jq -r '.functionAppPrincipalId.value')

echo "✅ Azure resources deployed successfully!"
echo "📱 Function App Name: $FUNCTION_APP_NAME"
echo "🌐 Function App URL: $FUNCTION_APP_URL"

# Configure Key Vault access for the Function App
echo "🔗 Configuring Key Vault access for Function App..."
az role assignment create \
    --assignee "$FUNCTION_APP_PRINCIPAL_ID" \
    --role "Key Vault Secrets User" \
    --scope "/subscriptions/$(az account show --query id --output tsv)/resourceGroups/$EXISTING_KV_RG/providers/Microsoft.KeyVault/vaults/$EXISTING_KV_NAME"

# Configure Function App settings with Key Vault references
echo "⚙️  Configuring Function App settings..."
az functionapp config appsettings set \
    --name $FUNCTION_APP_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --settings \
    "USE_KEY_VAULT=true" \
    "AZURE_KEY_VAULT_URL=https://$EXISTING_KV_NAME.vault.azure.net/" \
    "ASANA_ACCESS_TOKEN=@Microsoft.KeyVault(VaultName=$EXISTING_KV_NAME;SecretName=asana-access-token)" \
    "GITHUB_TOKEN=@Microsoft.KeyVault(VaultName=$EXISTING_KV_NAME;SecretName=github-token)" \
    "OPENAI_API_KEY=@Microsoft.KeyVault(VaultName=$EXISTING_KV_NAME;SecretName=openai-api-key)"

# Build and deploy the function code
echo "📦 Building and deploying function code..."

# Create a temporary directory for deployment
TEMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TEMP_DIR"

# Copy source code to temp directory
cp -r src/ $TEMP_DIR/
cp -r azure/ $TEMP_DIR/
cp pyproject.toml $TEMP_DIR/

# Create requirements.txt from pyproject.toml for Azure Functions
cd $TEMP_DIR
echo "Creating requirements.txt for Azure Functions..."
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

# Create the deployment package
echo "Creating deployment package..."
zip -r ../function-app.zip . -x "*.pyc" "__pycache__/*" "tests/*" "*.git*"

cd ..

# Deploy the function code
echo "🚀 Deploying function code to Azure..."
az functionapp deployment source config-zip \
    --resource-group $RESOURCE_GROUP_NAME \
    --name $FUNCTION_APP_NAME \
    --src function-app.zip

# Clean up
rm -rf $TEMP_DIR function-app.zip

echo ""
echo "🎉 Deployment completed successfully!"
echo "=================================="
echo "🌐 Your AI Assistant is available at: $FUNCTION_APP_URL"
echo "📚 API Documentation: $FUNCTION_APP_URL/api/docs"
echo ""
echo "🔑 Next Steps:"
echo "1. Add your API keys to Key Vault using: python scripts/setup_keyvault.py setup"
echo "2. Test the endpoints"
echo "3. Configure webhooks (optional)"
echo ""
echo "📋 Function App Details:"
echo "   Name: $FUNCTION_APP_NAME"
echo "   Resource Group: $RESOURCE_GROUP_NAME"
echo "   Key Vault: $EXISTING_KV_NAME"
echo ""