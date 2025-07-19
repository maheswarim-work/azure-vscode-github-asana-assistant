#!/bin/bash

# Azure deployment script for the AI Assistant

set -e

# Configuration
RESOURCE_GROUP_NAME="asana-github-assistant-rg"
LOCATION="eastus"
APP_NAME="asana-github-assistant"

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

# Create resource group
echo "📦 Creating resource group: $RESOURCE_GROUP_NAME"
az group create \
    --name $RESOURCE_GROUP_NAME \
    --location $LOCATION

# Deploy the Bicep template
echo "🏗️  Deploying Azure resources..."
DEPLOYMENT_OUTPUT=$(az deployment group create \
    --resource-group $RESOURCE_GROUP_NAME \
    --template-file deploy/bicep/main.bicep \
    --parameters appName=$APP_NAME \
    --query 'properties.outputs' \
    --output json)

# Extract outputs
FUNCTION_APP_NAME=$(echo $DEPLOYMENT_OUTPUT | jq -r '.functionAppName.value')
FUNCTION_APP_URL=$(echo $DEPLOYMENT_OUTPUT | jq -r '.functionAppUrl.value')
KEY_VAULT_NAME=$(echo $DEPLOYMENT_OUTPUT | jq -r '.keyVaultName.value')

echo "✅ Azure resources deployed successfully!"
echo "📱 Function App Name: $FUNCTION_APP_NAME"
echo "🌐 Function App URL: $FUNCTION_APP_URL"
echo "🔐 Key Vault Name: $KEY_VAULT_NAME"

# Update Key Vault secrets
echo "🔑 Setting up Key Vault secrets..."
echo "You can either:"
echo "1. Use the interactive setup script: python scripts/setup_keyvault.py setup --key-vault-url https://$KEY_VAULT_NAME.vault.azure.net/"
echo "2. Use Azure CLI commands:"
echo "   az keyvault secret set --vault-name $KEY_VAULT_NAME --name asana-access-token --value 'YOUR_ASANA_TOKEN'"
echo "   az keyvault secret set --vault-name $KEY_VAULT_NAME --name github-token --value 'YOUR_GITHUB_TOKEN'"
echo "   az keyvault secret set --vault-name $KEY_VAULT_NAME --name openai-api-key --value 'YOUR_OPENAI_API_KEY'"

# Create function app settings for Key Vault references
echo "🔗 Configuring Key Vault references and settings..."
az functionapp config appsettings set \
    --name $FUNCTION_APP_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --settings \
    "USE_KEY_VAULT=true" \
    "AZURE_KEY_VAULT_URL=https://$KEY_VAULT_NAME.vault.azure.net/" \
    "ASANA_ACCESS_TOKEN=@Microsoft.KeyVault(VaultName=$KEY_VAULT_NAME;SecretName=asana-access-token)" \
    "GITHUB_TOKEN=@Microsoft.KeyVault(VaultName=$KEY_VAULT_NAME;SecretName=github-token)" \
    "OPENAI_API_KEY=@Microsoft.KeyVault(VaultName=$KEY_VAULT_NAME;SecretName=openai-api-key)"

# Deploy the function code
echo "📦 Building and deploying function code..."
cd azure
zip -r ../function-app.zip . -x "*.pyc" "__pycache__/*"
cd ..

az functionapp deployment source config-zip \
    --resource-group $RESOURCE_GROUP_NAME \
    --name $FUNCTION_APP_NAME \
    --src function-app.zip

# Clean up
rm function-app.zip

echo ""
echo "🎉 Deployment completed successfully!"
echo "🌐 Your AI Assistant is available at: $FUNCTION_APP_URL"
echo "📚 API Documentation available at: $FUNCTION_APP_URL/docs"
echo ""
echo "Next steps:"
echo "1. Update the Key Vault secrets with your API keys"
echo "2. Test the endpoints using the provided examples"
echo "3. Set up webhooks in Asana and GitHub (optional)"