"""
Provider Factory - Creates provider instances
Implements Factory pattern for provider instantiation
"""
from typing import Optional
from enum import Enum

from .base import LLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .deepseek_provider import DeepSeekProvider
from .openrouter_provider import OpenRouterProvider
from .groq_provider import GroqProvider
from core.exceptions import ValidationError


class ProviderType(str, Enum):
    """Supported provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"
    GROQ = "groq"


class ProviderFactory:
    """
    Factory for creating provider instances.
    
    Design pattern: Factory Pattern
    - Centralizes provider creation logic
    - Encapsulates provider-specific instantiation
    """
    
    # Registry of provider classes
    _PROVIDERS = {
        ProviderType.OPENAI: OpenAIProvider,
        ProviderType.ANTHROPIC: AnthropicProvider,
        ProviderType.GEMINI: GeminiProvider,
        ProviderType.DEEPSEEK: DeepSeekProvider,
        ProviderType.OPENROUTER: OpenRouterProvider,
        ProviderType.GROQ: GroqProvider
    }
    
    @classmethod
    def create(
        cls,
        provider_type: str,
        api_key: str,
        timeout: int = 60
    ) -> LLMProvider:
        """
        Create a provider instance.
        
        Args:
            provider_type: Provider type (openai, anthropic, gemini, deepseek)
            api_key: API key for the provider
            timeout: Request timeout in seconds
            
        Returns:
            Configured provider instance
            
        Raises:
            ValidationError: If provider_type is not supported
        """
        # Normalize provider type
        try:
            provider_enum = ProviderType(provider_type.lower())
        except ValueError:
            supported = ", ".join([p.value for p in ProviderType])
            raise ValidationError(
                f"Unsupported provider: {provider_type}. Supported: {supported}",
                field="provider"
            )
        
        # Get provider class and instantiate
        provider_class = cls._PROVIDERS[provider_enum]
        return provider_class(api_key=api_key, timeout=timeout)
    
    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported provider names"""
        return [p.value for p in ProviderType]
    
    @classmethod
    def get_provider_info(cls, provider_type: str) -> dict:
        """
        Get information about a provider.
        
        Args:
            provider_type: Provider type
            
        Returns:
            Dictionary with provider information
        """
        try:
            provider_enum = ProviderType(provider_type.lower())
        except ValueError:
            raise ValidationError(f"Unknown provider: {provider_type}")
        
        # Create temporary instance with dummy key to get metadata
        provider_class = cls._PROVIDERS[provider_enum]
        temp_provider = provider_class(api_key="dummy", timeout=1)
        
        return {
            "name": temp_provider.name,
            "supported_models": temp_provider.supported_models,
            "capabilities": [c.value for c in temp_provider.capabilities]
        }


# Convenience function for common use case
def get_provider(provider_type: str, api_key: str, timeout: int = 60) -> LLMProvider:
    """
    Get a configured provider instance.
    
    Args:
        provider_type: Provider type (openai, anthropic, gemini, deepseek)
        api_key: API key for the provider
        timeout: Request timeout in seconds
        
    Returns:
        Configured provider instance
    """
    return ProviderFactory.create(provider_type, api_key, timeout)
