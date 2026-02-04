"""
Base Provider Interface - LLM Provider Protocol
Defines the contract that all provider adapters must implement
"""
from typing import Protocol, Dict, Any, Optional, AsyncIterator
from enum import Enum


class ModelCapability(str, Enum):
    """LLM model capabilities"""
    TEXT_GENERATION = "text_generation"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"


class LLMRequest:
    """
    Normalized request structure for LLM providers.
    Abstracts away provider-specific differences.
    """
    
    def __init__(
        self,
        prompt: str,
        model: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        stream: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.prompt = prompt
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system_prompt = system_prompt
        self.stream = stream
        self.metadata = metadata or {}


class LLMResponse:
    """
    Normalized response structure from LLM providers.
    Provides consistent interface regardless of provider.
    """
    
    def __init__(
        self,
        content: str,
        model: str,
        provider: str,
        usage: Optional[Dict[str, int]] = None,
        finish_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.model = model
        self.provider = provider
        self.usage = usage or {}  # {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.finish_reason = finish_reason
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "metadata": self.metadata
        }


class LLMProvider(Protocol):
    """
    Protocol for LLM provider adapters.
    All provider implementations must conform to this interface.
    
    Design pattern: Adapter Pattern
    - Normalizes different provider APIs into consistent interface
    - Enables swapping providers without changing business logic
    """
    
    @property
    def name(self) -> str:
        """Provider name (e.g., 'openai', 'anthropic')"""
        ...
    
    @property
    def supported_models(self) -> list[str]:
        """List of supported model identifiers"""
        ...
    
    @property
    def capabilities(self) -> list[ModelCapability]:
        """List of supported capabilities"""
        ...
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate completion from LLM.
        
        Args:
            request: Normalized LLM request
            
        Returns:
            Normalized LLM response
            
        Raises:
            ProviderAuthenticationError: Invalid API key
            ProviderRateLimitError: Rate limit exceeded
            ProviderTimeoutError: Request timed out
            ProviderResponseError: Invalid response from provider
        """
        ...
    
    async def stream_generate(self, request: LLMRequest) -> AsyncIterator[str]:
        """
        Stream completion from LLM (token by token).
        
        Args:
            request: Normalized LLM request (with stream=True)
            
        Yields:
            Content chunks as they arrive
            
        Raises:
            Same as generate()
        """
        ...
    
    async def validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key without making expensive requests.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if valid, False otherwise
        """
        ...
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        ...


class BaseProvider:
    """
    Base class for provider implementations.
    Provides common functionality like token estimation and error handling.
    """
    
    def __init__(self, api_key: str, timeout: int = 60):
        """
        Args:
            api_key: Provider API key
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
    
    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation (4 chars ≈ 1 token).
        Provider-specific implementations may override with better methods.
        """
        return len(text) // 4
    
    def _build_error_context(self, error: Exception) -> Dict[str, Any]:
        """Build error context for logging"""
        return {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "provider": self.name
        }
