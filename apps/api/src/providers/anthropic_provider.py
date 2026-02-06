"""
Anthropic Provider Adapter
Implements LLMProvider interface for Anthropic Claude API
"""
from typing import AsyncIterator
import anthropic
from anthropic import AsyncAnthropic

from .base import LLMProvider, LLMRequest, LLMResponse, BaseProvider, ModelCapability
from core.exceptions import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderResponseError
)


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API adapter"""
    
    def __init__(self, api_key: str, timeout: int = 60):
        super().__init__(api_key, timeout)
        self.client = AsyncAnthropic(api_key=api_key, timeout=timeout)
        self._name = "anthropic"
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def supported_models(self) -> list[str]:
        return [
            "claude-3-5-haiku-20241022",
            "claude-opus-4-20250514",
            "claude-sonnet-4-20250514"
        ]
    
    @property
    def capabilities(self) -> list[ModelCapability]:
        return [
            ModelCapability.TEXT_GENERATION,
            ModelCapability.STREAMING,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.VISION
        ]
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate completion from Anthropic"""
        try:
            # Anthropic uses system parameter separately
            kwargs = {
                "model": request.model,
                "max_tokens": request.max_tokens or 4096,  # Required for Anthropic
                "temperature": request.temperature,
                "messages": [{"role": "user", "content": request.prompt}]
            }
            
            if request.system_prompt:
                kwargs["system"] = request.system_prompt
            
            # Make API call
            response = await self.client.messages.create(**kwargs)
            
            # Extract content
            content = ""
            for block in response.content:
                if block.type == "text":
                    content += block.text
            
            return LLMResponse(
                content=content,
                model=response.model,
                provider=self.name,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                finish_reason=response.stop_reason,
                metadata={"id": response.id}
            )
            
        except anthropic.AuthenticationError:
            raise ProviderAuthenticationError(self.name)
        except anthropic.RateLimitError as e:
            # Try to extract retry_after from headers
            retry_after = None
            if hasattr(e, "response") and e.response:
                retry_after = e.response.headers.get("retry-after")
            raise ProviderRateLimitError(self.name, retry_after)
        except anthropic.APITimeoutError:
            raise ProviderTimeoutError(self.name)
        except anthropic.APIError as e:
            raise ProviderResponseError(self.name, str(e))
        except Exception as e:
            raise ProviderResponseError(self.name, f"Unexpected error: {str(e)}")
    
    async def stream_generate(self, request: LLMRequest) -> AsyncIterator[str]:
        """Stream completion from Anthropic"""
        try:
            kwargs = {
                "model": request.model,
                "max_tokens": request.max_tokens or 4096,
                "temperature": request.temperature,
                "messages": [{"role": "user", "content": request.prompt}]
            }
            
            if request.system_prompt:
                kwargs["system"] = request.system_prompt
            
            # Make streaming API call
            async with self.client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except anthropic.AuthenticationError:
            raise ProviderAuthenticationError(self.name)
        except anthropic.RateLimitError as e:
            retry_after = None
            if hasattr(e, "response") and e.response:
                retry_after = e.response.headers.get("retry-after")
            raise ProviderRateLimitError(self.name, retry_after)
        except anthropic.APITimeoutError:
            raise ProviderTimeoutError(self.name)
        except anthropic.APIError as e:
            raise ProviderResponseError(self.name, str(e))
        except Exception as e:
            raise ProviderResponseError(self.name, f"Unexpected error: {str(e)}")
    
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate Anthropic API key"""
        try:
            # Make a minimal test request
            temp_client = AsyncAnthropic(api_key=api_key, timeout=5)
            await temp_client.messages.create(
                model="claude-3-haiku-20240307",  # Fastest/cheapest model
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except anthropic.AuthenticationError:
            return False
        except Exception:
            # Other errors don't necessarily mean invalid key
            return True
