#!/usr/bin/env python3
"""
Azure Key Vault Setup Script

This script helps you set up and manage secrets in Azure Key Vault
for the AI Assistant application.
"""

import asyncio
import argparse
import os
import sys
from typing import Dict, Optional

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from assistant.azure_keyvault import AzureKeyVaultClient


async def setup_secrets(key_vault_url: str, secrets: Dict[str, str]) -> None:
    """Set up secrets in Azure Key Vault."""
    print(f"🔐 Setting up secrets in Key Vault: {key_vault_url}")
    
    client = AzureKeyVaultClient(key_vault_url)
    
    if not client.is_available():
        print("❌ Key Vault client is not available. Please check your Azure credentials and Key Vault URL.")
        return
    
    for secret_name, secret_value in secrets.items():
        if not secret_value or secret_value == "PLACEHOLDER":
            print(f"⚠️  Skipping {secret_name} (no value provided)")
            continue
        
        print(f"📝 Setting secret: {secret_name}")
        success = await client.set_secret(secret_name, secret_value)
        
        if success:
            print(f"✅ Successfully set secret: {secret_name}")
        else:
            print(f"❌ Failed to set secret: {secret_name}")


async def list_secrets(key_vault_url: str) -> None:
    """List all secrets in Azure Key Vault."""
    print(f"📋 Listing secrets in Key Vault: {key_vault_url}")
    
    client = AzureKeyVaultClient(key_vault_url)
    
    if not client.is_available():
        print("❌ Key Vault client is not available. Please check your Azure credentials and Key Vault URL.")
        return
    
    secrets = await client.list_secrets()
    
    if secrets:
        print("🔑 Available secrets:")
        for secret_name in secrets:
            print(f"  - {secret_name}")
    else:
        print("📭 No secrets found in Key Vault")


async def get_secret(key_vault_url: str, secret_name: str) -> None:
    """Get a specific secret from Azure Key Vault."""
    print(f"🔍 Getting secret '{secret_name}' from Key Vault: {key_vault_url}")
    
    client = AzureKeyVaultClient(key_vault_url)
    
    if not client.is_available():
        print("❌ Key Vault client is not available. Please check your Azure credentials and Key Vault URL.")
        return
    
    secret_value = await client.get_secret(secret_name)
    
    if secret_value:
        # Don't print the actual value for security
        print(f"✅ Secret '{secret_name}' found (value hidden for security)")
        print(f"🔢 Value length: {len(secret_value)} characters")
    else:
        print(f"❌ Secret '{secret_name}' not found")


async def delete_secret(key_vault_url: str, secret_name: str) -> None:
    """Delete a secret from Azure Key Vault."""
    print(f"🗑️  Deleting secret '{secret_name}' from Key Vault: {key_vault_url}")
    
    # Confirm deletion
    confirm = input(f"Are you sure you want to delete '{secret_name}'? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Deletion cancelled")
        return
    
    client = AzureKeyVaultClient(key_vault_url)
    
    if not client.is_available():
        print("❌ Key Vault client is not available. Please check your Azure credentials and Key Vault URL.")
        return
    
    success = await client.delete_secret(secret_name)
    
    if success:
        print(f"✅ Successfully deleted secret: {secret_name}")
    else:
        print(f"❌ Failed to delete secret: {secret_name}")


def get_key_vault_url() -> Optional[str]:
    """Get Key Vault URL from environment or user input."""
    key_vault_url = os.getenv("AZURE_KEY_VAULT_URL")
    
    if not key_vault_url:
        key_vault_url = input("Enter your Azure Key Vault URL: ").strip()
    
    if not key_vault_url:
        print("❌ No Key Vault URL provided")
        return None
    
    return key_vault_url


def main():
    parser = argparse.ArgumentParser(description="Manage Azure Key Vault secrets for AI Assistant")
    parser.add_argument("action", choices=["setup", "list", "get", "delete"], 
                       help="Action to perform")
    parser.add_argument("--secret-name", help="Name of the secret (for get/delete actions)")
    parser.add_argument("--key-vault-url", help="Azure Key Vault URL")
    parser.add_argument("--asana-token", help="Asana access token")
    parser.add_argument("--github-token", help="GitHub access token")
    parser.add_argument("--openai-key", help="OpenAI API key")
    
    args = parser.parse_args()
    
    key_vault_url = args.key_vault_url or get_key_vault_url()
    if not key_vault_url:
        sys.exit(1)
    
    async def run():
        if args.action == "setup":
            # Collect secrets
            secrets = {}
            
            if args.asana_token:
                secrets["asana-access-token"] = args.asana_token
            elif input("Set Asana access token? (y/N): ").lower() == 'y':
                token = input("Enter Asana access token: ").strip()
                if token:
                    secrets["asana-access-token"] = token
            
            if args.github_token:
                secrets["github-token"] = args.github_token
            elif input("Set GitHub token? (y/N): ").lower() == 'y':
                token = input("Enter GitHub token: ").strip()
                if token:
                    secrets["github-token"] = token
            
            if args.openai_key:
                secrets["openai-api-key"] = args.openai_key
            elif input("Set OpenAI API key? (y/N): ").lower() == 'y':
                key = input("Enter OpenAI API key: ").strip()
                if key:
                    secrets["openai-api-key"] = key
            
            if secrets:
                await setup_secrets(key_vault_url, secrets)
            else:
                print("⚠️  No secrets to set up")
        
        elif args.action == "list":
            await list_secrets(key_vault_url)
        
        elif args.action == "get":
            if not args.secret_name:
                print("❌ --secret-name is required for get action")
                sys.exit(1)
            await get_secret(key_vault_url, args.secret_name)
        
        elif args.action == "delete":
            if not args.secret_name:
                print("❌ --secret-name is required for delete action")
                sys.exit(1)
            await delete_secret(key_vault_url, args.secret_name)
    
    # Check if Azure credentials are available
    print("🔐 Checking Azure authentication...")
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    
    if tenant_id and client_id:
        print(f"✅ Using service principal authentication (Tenant: {tenant_id[:8]}...)")
    else:
        print("ℹ️  Using default Azure credential (CLI, managed identity, etc.)")
    
    # Run the async function
    asyncio.run(run())


if __name__ == "__main__":
    main()