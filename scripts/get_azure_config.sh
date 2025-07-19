#!/bin/bash

# Azure Configuration Helper Script
# This script helps you obtain the Azure credentials needed for the AI Assistant

echo "🔍 Azure Configuration Helper"
echo "============================"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first:"
    echo "   https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in
echo "🔐 Checking Azure login status..."
if ! az account show &> /dev/null; then
    echo "Please login to Azure..."
    az login
fi

# Get current subscription and tenant info
echo "📋 Getting current Azure subscription info..."
SUBSCRIPTION_INFO=$(az account show --output json)
TENANT_ID=$(echo $SUBSCRIPTION_INFO | jq -r '.tenantId')
SUBSCRIPTION_ID=$(echo $SUBSCRIPTION_INFO | jq -r '.id')
SUBSCRIPTION_NAME=$(echo $SUBSCRIPTION_INFO | jq -r '.name')

echo "✅ Current Azure Context:"
echo "   Subscription: $SUBSCRIPTION_NAME"
echo "   Subscription ID: $SUBSCRIPTION_ID"
echo "   Tenant ID: $TENANT_ID"
echo ""

# Prompt for app name
read -p "Enter a name for your service principal (e.g., 'ai-assistant-app'): " APP_NAME
if [ -z "$APP_NAME" ]; then
    APP_NAME="ai-assistant-app"
fi

echo ""
echo "🔑 Creating Azure Service Principal..."
echo "App Name: $APP_NAME"

# Create service principal
SP_OUTPUT=$(az ad sp create-for-rbac \
    --name "$APP_NAME" \
    --role "Contributor" \
    --scopes "/subscriptions/$SUBSCRIPTION_ID" \
    --output json)

if [ $? -eq 0 ]; then
    CLIENT_ID=$(echo $SP_OUTPUT | jq -r '.appId')
    CLIENT_SECRET=$(echo $SP_OUTPUT | jq -r '.password')
    
    echo "✅ Service Principal created successfully!"
    echo ""
else
    echo "❌ Failed to create service principal"
    exit 1
fi

# Prompt for Key Vault name
echo "🔐 Key Vault Setup"
read -p "Enter a name for your Key Vault (must be globally unique): " KV_NAME
if [ -z "$KV_NAME" ]; then
    KV_NAME="ai-assistant-kv-$(date +%s)"
fi

# Prompt for resource group
read -p "Enter resource group name (or press Enter to create 'ai-assistant-rg'): " RG_NAME
if [ -z "$RG_NAME" ]; then
    RG_NAME="ai-assistant-rg"
fi

# Prompt for location
read -p "Enter Azure region (e.g., 'eastus', 'westus2'): " LOCATION
if [ -z "$LOCATION" ]; then
    LOCATION="eastus"
fi

echo ""
echo "📦 Creating Azure resources..."

# Create resource group if it doesn't exist
echo "Creating resource group: $RG_NAME"
az group create --name "$RG_NAME" --location "$LOCATION" --output none

if [ $? -eq 0 ]; then
    echo "✅ Resource group created/verified"
else
    echo "⚠️  Resource group may already exist"
fi

# Create Key Vault
echo "Creating Key Vault: $KV_NAME"
KV_OUTPUT=$(az keyvault create \
    --name "$KV_NAME" \
    --resource-group "$RG_NAME" \
    --location "$LOCATION" \
    --output json)

if [ $? -eq 0 ]; then
    KV_URL=$(echo $KV_OUTPUT | jq -r '.properties.vaultUri')
    echo "✅ Key Vault created successfully!"
else
    echo "❌ Failed to create Key Vault (name might not be unique)"
    echo "Try a different name or use an existing Key Vault"
    exit 1
fi

# Grant Key Vault permissions to service principal
echo "Setting Key Vault permissions..."
az keyvault set-policy \
    --name "$KV_NAME" \
    --spn "$CLIENT_ID" \
    --secret-permissions get list set delete \
    --output none

if [ $? -eq 0 ]; then
    echo "✅ Key Vault permissions granted"
else
    echo "⚠️  Failed to set Key Vault permissions"
fi

echo ""
echo "🎉 Azure Configuration Complete!"
echo "================================"
echo ""
echo "📝 Add these values to your .env file:"
echo ""
echo "AZURE_TENANT_ID=$TENANT_ID"
echo "AZURE_CLIENT_ID=$CLIENT_ID"
echo "AZURE_CLIENT_SECRET=$CLIENT_SECRET"
echo "AZURE_KEY_VAULT_URL=$KV_URL"
echo ""
echo "💾 Saving configuration to azure_config.env..."

# Save to file
cat > azure_config.env << EOF
# Azure Configuration Generated on $(date)
AZURE_TENANT_ID=$TENANT_ID
AZURE_CLIENT_ID=$CLIENT_ID
AZURE_CLIENT_SECRET=$CLIENT_SECRET
AZURE_KEY_VAULT_URL=$KV_URL

# Resource Information
AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID
AZURE_RESOURCE_GROUP=$RG_NAME
AZURE_KEY_VAULT_NAME=$KV_NAME
EOF

echo "✅ Configuration saved to azure_config.env"
echo ""
echo "🔒 Important Security Notes:"
echo "   - Keep your CLIENT_SECRET secure and never commit it to version control"
echo "   - The service principal has Contributor access to your subscription"
echo "   - You can revoke access anytime in the Azure Portal > Azure Active Directory > App registrations"
echo ""
echo "🚀 Next Steps:"
echo "   1. Copy the values above to your .env file"
echo "   2. Run: python scripts/setup_keyvault.py setup"
echo "   3. Add your API keys (Asana, GitHub, OpenAI) to Key Vault"
echo ""