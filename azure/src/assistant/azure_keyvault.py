import os
import asyncio
from typing import Optional, Dict, Any
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential
import logging

logger = logging.getLogger(__name__)


class AzureKeyVaultClient:
    """Azure Key Vault client for secure secret management."""
    
    def __init__(self, key_vault_url: Optional[str] = None):
        self.key_vault_url = key_vault_url or os.getenv("AZURE_KEY_VAULT_URL")
        self.client: Optional[SecretClient] = None
        self._secrets_cache: Dict[str, str] = {}
        
        if self.key_vault_url:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Key Vault client with appropriate credentials."""
        try:
            # Try different authentication methods
            credential = self._get_credential()
            self.client = SecretClient(vault_url=self.key_vault_url, credential=credential)
            logger.info("Azure Key Vault client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure Key Vault client: {str(e)}")
            self.client = None
    
    def _get_credential(self):
        """Get the appropriate Azure credential."""
        # Check if we have explicit service principal credentials
        tenant_id = os.getenv("AZURE_TENANT_ID")
        client_id = os.getenv("AZURE_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")
        
        if tenant_id and client_id and client_secret:
            logger.info("Using ClientSecretCredential for Key Vault access")
            return ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        else:
            # Use DefaultAzureCredential for managed identity or CLI
            logger.info("Using DefaultAzureCredential for Key Vault access")
            return DefaultAzureCredential()
    
    async def get_secret(self, secret_name: str, use_cache: bool = True) -> Optional[str]:
        """Get a secret from Azure Key Vault."""
        if not self.client:
            logger.warning("Key Vault client not initialized, falling back to environment variable")
            return os.getenv(secret_name.upper().replace("-", "_"))
        
        # Check cache first
        if use_cache and secret_name in self._secrets_cache:
            return self._secrets_cache[secret_name]
        
        try:
            # Run in thread pool since Azure SDK is not async
            loop = asyncio.get_event_loop()
            secret = await loop.run_in_executor(
                None, 
                lambda: self.client.get_secret(secret_name)
            )
            
            secret_value = secret.value
            if use_cache:
                self._secrets_cache[secret_name] = secret_value
            
            logger.info(f"Successfully retrieved secret: {secret_name}")
            return secret_value
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret '{secret_name}': {str(e)}")
            # Fallback to environment variable
            return os.getenv(secret_name.upper().replace("-", "_"))
    
    async def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """Set a secret in Azure Key Vault."""
        if not self.client:
            logger.error("Key Vault client not initialized")
            return False
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: self.client.set_secret(secret_name, secret_value)
            )
            
            # Update cache
            self._secrets_cache[secret_name] = secret_value
            logger.info(f"Successfully set secret: {secret_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set secret '{secret_name}': {str(e)}")
            return False
    
    async def delete_secret(self, secret_name: str) -> bool:
        """Delete a secret from Azure Key Vault."""
        if not self.client:
            logger.error("Key Vault client not initialized")
            return False
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: self.client.begin_delete_secret(secret_name)
            )
            
            # Remove from cache
            self._secrets_cache.pop(secret_name, None)
            logger.info(f"Successfully deleted secret: {secret_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete secret '{secret_name}': {str(e)}")
            return False
    
    async def list_secrets(self) -> list:
        """List all secret names in the Key Vault."""
        if not self.client:
            logger.error("Key Vault client not initialized")
            return []
        
        try:
            loop = asyncio.get_event_loop()
            secrets = await loop.run_in_executor(
                None, 
                lambda: list(self.client.list_properties_of_secrets())
            )
            
            return [secret.name for secret in secrets]
            
        except Exception as e:
            logger.error(f"Failed to list secrets: {str(e)}")
            return []
    
    def clear_cache(self):
        """Clear the secrets cache."""
        self._secrets_cache.clear()
        logger.info("Secrets cache cleared")
    
    def is_available(self) -> bool:
        """Check if Key Vault is available and configured."""
        return self.client is not None


# Global Key Vault client instance
key_vault_client = AzureKeyVaultClient()