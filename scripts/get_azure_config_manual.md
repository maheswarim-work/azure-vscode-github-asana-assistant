# Manual Azure Configuration Guide

If you prefer to get Azure credentials manually through the Azure Portal, follow these steps:

## 🔍 Getting Azure Tenant ID

### Method 1: Azure Portal
1. Go to [Azure Portal](https://portal.azure.com)
2. Search for "Azure Active Directory" or "Microsoft Entra ID"
3. In the Overview section, copy the **Tenant ID**

### Method 2: Azure CLI
```bash
az account show --query tenantId --output tsv
```

## 🔑 Creating Service Principal (App Registration)

### Azure Portal Method:
1. Go to **Azure Active Directory** > **App registrations**
2. Click **"New registration"**
3. Enter name: `ai-assistant-app`
4. Leave other settings as default, click **"Register"**
5. Copy the **Application (client) ID** - this is your `AZURE_CLIENT_ID`

### Create Client Secret:
1. In your app registration, go to **Certificates & secrets**
2. Click **"New client secret"**
3. Add description: `AI Assistant Secret`
4. Choose expiration (e.g., 24 months)
5. Click **"Add"**
6. **IMMEDIATELY copy the secret value** - this is your `AZURE_CLIENT_SECRET`
   ⚠️ **Important**: You can't see this value again after leaving the page!

### Grant Permissions:
1. Go to **Subscriptions** in Azure Portal
2. Select your subscription
3. Go to **Access control (IAM)**
4. Click **"Add role assignment"**
5. Select **"Contributor"** role
6. Assign to your service principal (search by the app name)

## 🔐 Creating Key Vault

### Azure Portal Method:
1. Search for **"Key vaults"** in Azure Portal
2. Click **"Create"**
3. Fill in:
   - **Resource group**: Create new or use existing (e.g., `ai-assistant-rg`)
   - **Key vault name**: Choose unique name (e.g., `ai-assistant-kv-123`)
   - **Region**: Choose your preferred region (e.g., `East US`)
4. Click **"Review + create"** then **"Create"**

### Get Key Vault URL:
1. Go to your created Key Vault
2. In the Overview section, copy the **Vault URI**
3. This is your `AZURE_KEY_VAULT_URL`

### Grant Access to Service Principal:
1. In your Key Vault, go to **Access policies**
2. Click **"Add Access Policy"**
3. Configure permissions:
   - **Secret permissions**: Get, List, Set, Delete
4. **Select principal**: Search for your service principal name
5. Click **"Add"** then **"Save"**

## 📝 Example Values

After completing the steps above, your values should look like:

```env
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
AZURE_CLIENT_ID=87654321-4321-4321-4321-210987654321
AZURE_CLIENT_SECRET=abcd1234~efgh5678_ijkl9012mnop3456
AZURE_KEY_VAULT_URL=https://ai-assistant-kv-123.vault.azure.net/
```

## 🚀 Quick Setup Script

For automated setup, run:
```bash
./scripts/get_azure_config.sh
```

This script will:
- Create the service principal
- Create a Key Vault
- Set up permissions
- Generate the configuration values for you

## 🔒 Security Best Practices

1. **Never commit secrets to version control**
2. **Use Key Vault for production secrets**
3. **Rotate client secrets regularly**
4. **Use least-privilege access**
5. **Monitor access logs**

## ❓ Troubleshooting

### Common Issues:

**"Insufficient privileges to complete the operation"**
- You need Owner or User Access Administrator role on the subscription

**"The vault name is not available"**
- Key Vault names must be globally unique, try a different name

**"Authentication failed"**
- Verify your service principal credentials are correct
- Check that the service principal has proper permissions

### Getting Help:
- Azure CLI: `az help`
- Azure Portal: Use the help chat icon
- Documentation: [Azure Key Vault docs](https://docs.microsoft.com/en-us/azure/key-vault/)