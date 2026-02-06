"""
DeepSeek Provider Adapter
Implements LLMProvider interface for DeepSeek API (OpenAI-compatible)
"""
from typing import AsyncIterator
from openai import AsyncOpenAI
import openai

from .base import LLMProvider, LLMRequest, LLMResponse, BaseProvider, ModelCapability
from core.exceptions import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderResponseError
)


class DeepSeekProvider(BaseProvider):
    """DeepSeek API adapter (uses OpenAI-compatible API)"""
    
    def __init__(self, api_key: str, timeout: int = 60):
        super().__init__(api_key, timeout)
        # DeepSeek uses OpenAI-compatible API with custom base URL
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            timeout=timeout
        )
        self._name = "deepseek"
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def supported_models(self) -> list[str]:
        return [
            "deepseek-chat",
            "deepseek-coder"
        ]
    
    @property
    def capabilities(self) -> list[ModelCapability]:
        return [
            ModelCapability.TEXT_GENERATION,
            ModelCapability.STREAMING,
            ModelCapability.FUNCTION_CALLING
        ]
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate completion from DeepSeek"""
        try:
            # Build messages (same as OpenAI)
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
    
    async def stream_generate(self, request: LLMRequest) -> AsyncIterator[str]:
        """Stream completion from DeepSeek"""
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
        """Validate DeepSeek API key"""
        try:
            # Try to list models
            temp_client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com",
                timeout=5
            )
            await temp_client.models.list()
            return True
        except openai.AuthenticationError:
            return False
        except Exception:
            # Other errors don't necessarily mean invalid key
            return True
