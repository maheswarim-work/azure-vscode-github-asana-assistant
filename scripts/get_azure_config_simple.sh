#!/bin/bash

# Simplified Azure Configuration Helper Script

echo "🔍 Azure Configuration Helper"
echo "============================"
echo ""

# Get current subscription and tenant info
echo "📋 Getting current Azure subscription info..."
SUBSCRIPTION_INFO=$(az account show)
TENANT_ID=$(echo $SUBSCRIPTION_INFO | jq -r '.tenantId')
SUBSCRIPTION_ID=$(echo $SUBSCRIPTION_INFO | jq -r '.id')
SUBSCRIPTION_NAME=$(echo $SUBSCRIPTION_INFO | jq -r '.name')

echo "✅ Current Azure Context:"
echo "   Subscription: $SUBSCRIPTION_NAME"
echo "   Subscription ID: $SUBSCRIPTION_ID"
echo "   Tenant ID: $TENANT_ID"
echo ""

# Prompt for app name
read -p "Enter a name for your service principal (default: ai-assistant-app): " APP_NAME
if [ -z "$APP_NAME" ]; then
    APP_NAME="ai-assistant-app"
fi

echo ""
echo "🔑 Creating Azure Service Principal..."
echo "App Name: $APP_NAME"

# Create service principal with proper scope
SP_OUTPUT=$(az ad sp create-for-rbac \
    --name "$APP_NAME" \
    --role "Contributor" \
    --scopes "/subscriptions/$SUBSCRIPTION_ID")

if [ $? -eq 0 ]; then
    CLIENT_ID=$(echo $SP_OUTPUT | jq -r '.appId')
    CLIENT_SECRET=$(echo $SP_OUTPUT | jq -r '.password')
    
    echo "✅ Service Principal created successfully!"
    echo "   Client ID: $CLIENT_ID"
    echo ""
else
    echo "❌ Failed to create service principal"
    echo "This might be because a service principal with this name already exists."
    echo "Try a different name or use the Azure Portal method."
    exit 1
fi

# Prompt for Key Vault name
echo "🔐 Key Vault Setup"
read -p "Enter a name for your Key Vault (must be globally unique, default: ai-assistant-kv-$(date +%s)): " KV_NAME
if [ -z "$KV_NAME" ]; then
    KV_NAME="ai-assistant-kv-$(date +%s)"
fi

# Prompt for resource group
read -p "Enter resource group name (default: ai-assistant-rg): " RG_NAME
if [ -z "$RG_NAME" ]; then
    RG_NAME="ai-assistant-rg"
fi

# Prompt for location
read -p "Enter Azure region (default: eastus): " LOCATION
if [ -z "$LOCATION" ]; then
    LOCATION="eastus"
fi

echo ""
echo "📦 Creating Azure resources..."

# Create resource group if it doesn't exist
echo "Creating resource group: $RG_NAME"
az group create --name "$RG_NAME" --location "$LOCATION" --output table

if [ $? -eq 0 ]; then
    echo "✅ Resource group ready"
else
    echo "⚠️  Resource group creation had issues, but continuing..."
fi

# Create Key Vault
echo ""
echo "Creating Key Vault: $KV_NAME"
KV_OUTPUT=$(az keyvault create \
    --name "$KV_NAME" \
    --resource-group "$RG_NAME" \
    --location "$LOCATION")

if [ $? -eq 0 ]; then
    KV_URL=$(echo $KV_OUTPUT | jq -r '.properties.vaultUri')
    echo "✅ Key Vault created successfully!"
    echo "   Vault URL: $KV_URL"
else
    echo "❌ Failed to create Key Vault"
    echo "The name '$KV_NAME' might not be unique. Try a different name."
    exit 1
fi

# Grant Key Vault permissions to service principal
echo ""
echo "Setting Key Vault permissions..."
az keyvault set-policy \
    --name "$KV_NAME" \
    --spn "$CLIENT_ID" \
    --secret-permissions get list set delete

if [ $? -eq 0 ]; then
    echo "✅ Key Vault permissions granted"
else
    echo "⚠️  Failed to set Key Vault permissions, but continuing..."
fi

echo ""
echo "🎉 Azure Configuration Complete!"
echo "================================"
echo ""
echo "📝 Your Azure configuration values:"
echo ""
echo "AZURE_TENANT_ID=$TENANT_ID"
echo "AZURE_CLIENT_ID=$CLIENT_ID"
echo "AZURE_CLIENT_SECRET=$CLIENT_SECRET"
echo "AZURE_KEY_VAULT_URL=$KV_URL"
echo ""

# Save to file
echo "💾 Saving configuration to azure_config.env..."
cat > azure_config.env << EOF
# Azure Configuration Generated on $(date)
AZURE_TENANT_ID=$TENANT_ID
AZURE_CLIENT_ID=$CLIENT_ID
AZURE_CLIENT_SECRET=$CLIENT_SECRET
AZURE_KEY_VAULT_URL=$KV_URL

# Additional Azure Information
AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID
AZURE_SUBSCRIPTION_NAME="$SUBSCRIPTION_NAME"
AZURE_RESOURCE_GROUP=$RG_NAME
AZURE_KEY_VAULT_NAME=$KV_NAME
AZURE_LOCATION=$LOCATION
EOF

echo "✅ Configuration saved to azure_config.env"
echo ""
echo "🔒 Important Security Notes:"
echo "   - Keep your CLIENT_SECRET secure and never commit it to version control"
echo "   - The service principal has Contributor access to your subscription"
echo "   - You can manage access in Azure Portal > Microsoft Entra ID > App registrations"
echo ""
echo "🚀 Next Steps:"
echo "   1. Copy the values above to your .env file"
echo "   2. Update USE_KEY_VAULT=true in your .env file"
echo "   3. Run: python scripts/setup_keyvault.py setup"
echo "   4. Add your API keys (Asana, GitHub, OpenAI) to Key Vault"
echo ""
echo "📋 Quick command to update your .env file:"
echo "   cat azure_config.env >> .env"
echo ""