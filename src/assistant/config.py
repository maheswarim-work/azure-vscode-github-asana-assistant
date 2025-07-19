import asyncio
import os
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Azure Configuration (for Key Vault access)
    azure_tenant_id: Optional[str] = None
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_key_vault_url: Optional[str] = None
    
    # Fallback API Keys (for local development without Key Vault)
    asana_access_token: Optional[str] = None
    github_token: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Database
    database_url: str = "sqlite:///./assistant.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    
    # AI Configuration
    openai_model: str = "gpt-4"
    max_tokens: int = 2000
    temperature: float = 0.7
    
    # Integration Settings
    asana_workspace_gid: Optional[str] = None
    github_organization: Optional[str] = None
    default_project_path: str = "./projects"
    
    # Key Vault Configuration
    use_key_vault: bool = True
    key_vault_secret_prefix: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class SecureSettings:
    """Settings class with Azure Key Vault integration for secure secret management."""
    
    def __init__(self):
        self.base_settings = Settings()
        self._key_vault_client = None
        self._secrets_cache: Dict[str, str] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize the Key Vault client if configured."""
        if not self._initialized:
            if self.base_settings.use_key_vault and self.base_settings.azure_key_vault_url:
                try:
                    from .azure_keyvault import AzureKeyVaultClient
                    self._key_vault_client = AzureKeyVaultClient(self.base_settings.azure_key_vault_url)
                    logger.info("Key Vault integration enabled")
                except ImportError:
                    logger.warning("Azure Key Vault dependencies not available, using environment variables")
                except Exception as e:
                    logger.error(f"Failed to initialize Key Vault: {str(e)}")
            else:
                logger.info("Key Vault integration disabled, using environment variables")
            
            self._initialized = True
    
    async def get_secret(self, secret_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
        """Get a secret from Key Vault or fallback to environment variable."""
        await self.initialize()
        
        # Try Key Vault first
        if self._key_vault_client and self._key_vault_client.is_available():
            try:
                vault_secret_name = f"{self.base_settings.key_vault_secret_prefix}{secret_name}"
                secret_value = await self._key_vault_client.get_secret(vault_secret_name)
                if secret_value:
                    return secret_value
            except Exception as e:
                logger.warning(f"Failed to get secret from Key Vault: {str(e)}")
        
        # Fallback to environment variable
        env_var = fallback_env_var or secret_name.upper().replace("-", "_")
        return os.getenv(env_var) or getattr(self.base_settings, env_var.lower(), None)
    
    async def get_asana_access_token(self) -> Optional[str]:
        """Get Asana access token from Key Vault or environment."""
        return await self.get_secret("asana-access-token", "ASANA_ACCESS_TOKEN")
    
    async def get_github_token(self) -> Optional[str]:
        """Get GitHub token from Key Vault or environment."""
        return await self.get_secret("github-token", "GITHUB_TOKEN")
    
    async def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from Key Vault or environment."""
        return await self.get_secret("openai-api-key", "OPENAI_API_KEY")
    
    async def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """Set a secret in Key Vault."""
        await self.initialize()
        
        if self._key_vault_client and self._key_vault_client.is_available():
            vault_secret_name = f"{self.base_settings.key_vault_secret_prefix}{secret_name}"
            return await self._key_vault_client.set_secret(vault_secret_name, secret_value)
        
        logger.warning("Key Vault not available, cannot set secret")
        return False
    
    def __getattr__(self, name: str) -> Any:
        """Delegate non-secret attributes to base settings."""
        return getattr(self.base_settings, name)


# Global settings instance
settings = SecureSettings()