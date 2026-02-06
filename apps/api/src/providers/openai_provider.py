"""
OpenAI Provider Adapter
Implements LLMProvider interface for OpenAI API
"""
from typing import AsyncIterator, Dict, Any
import openai
from openai import AsyncOpenAI

from .base import LLMProvider, LLMRequest, LLMResponse, BaseProvider, ModelCapability
from core.exceptions import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderResponseError
)


class OpenAIProvider(BaseProvider):
    """OpenAI API adapter"""
    
    def __init__(self, api_key: str, timeout: int = 60):
        super().__init__(api_key, timeout)
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self._name = "openai"
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def supported_models(self) -> list[str]:
        return [
            "o3-deep-research-2025-06-26",
            "gpt-5.2-pro-2025-12-11",
            "gpt-5.2-2025-12-11",
            "o4-mini-deep-research-2025-06-26",
            "gpt-5.2-codex",
            "gpt-5-mini-2025-08-07"
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
        """Generate completion from OpenAI"""
        try:
            # Build messages
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=request.model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=False
            )
            
            # Extract response
            choice = response.choices[0]
            content = choice.message.content or ""
            
            return LLMResponse(
                content=content,
                model=response.model,
                provider=self.name,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                finish_reason=choice.finish_reason,
                metadata={"id": response.id}
            )
            
        except openai.AuthenticationError as e:
            raise ProviderAuthenticationError(self.name)
        except openai.RateLimitError as e:
            # Extract retry_after if available
            retry_after = getattr(e, "retry_after", None)
            raise ProviderRateLimitError(self.name, retry_after)
        except openai.APITimeoutError as e:
            raise ProviderTimeoutError(self.name)
        except openai.APIError as e:
            raise ProviderResponseError(self.name, str(e))
        except Exception as e:
            raise ProviderResponseError(self.name, f"Unexpected error: {str(e)}")
    
    async def stream_generate(self, request: LLMRequest) -> AsyncIterator[str]:
        """Stream completion from OpenAI"""
        try:
            # Build messages
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            # Make streaming API call
            stream = await self.client.chat.completions.create(
                model=request.model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=True
            )
            
            # Yield chunks as they arrive
            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
                        
        except openai.AuthenticationError:
            raise ProviderAuthenticationError(self.name)
        except openai.RateLimitError as e:
            retry_after = getattr(e, "retry_after", None)
            raise ProviderRateLimitError(self.name, retry_after)
        except openai.APITimeoutError:
            raise ProviderTimeoutError(self.name)
        except openai.APIError as e:
            raise ProviderResponseError(self.name, str(e))
        except Exception as e:
            raise ProviderResponseError(self.name, f"Unexpected error: {str(e)}")
    
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate OpenAI API key"""
        try:
            # Try to list models (lightweight operation)
            temp_client = AsyncOpenAI(api_key=api_key, timeout=5)
            await temp_client.models.list()
            return True
        except openai.AuthenticationError:
            return False
        except Exception:
            # Other errors don't necessarily mean invalid key
            return True
