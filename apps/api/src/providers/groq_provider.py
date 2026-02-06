"""
Groq Provider Adapter
Implements LLMProvider interface for Groq API
Groq provides ultra-fast inference with LPU technology
"""
from typing import AsyncIterator, Dict, Any
import httpx

from .base import LLMProvider, LLMRequest, LLMResponse, BaseProvider, ModelCapability
from core.exceptions import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderResponseError
)


class GroqProvider(BaseProvider):
    """Groq API adapter"""
    
    BASE_URL = "https://api.groq.com/openai/v1"
    
    def __init__(self, api_key: str, timeout: int = 60):
        super().__init__(api_key, timeout)
        self._name = "groq"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def supported_models(self) -> list[str]:
        """Groq supported models"""
        return [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant"
        ]
    
    @property
    def capabilities(self) -> list[ModelCapability]:
        return [
            ModelCapability.TEXT_GENERATION,
            ModelCapability.STREAMING,
            ModelCapability.FUNCTION_CALLING
        ]
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate completion from Groq"""
        try:
            # Build messages
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            # Build request payload (Groq uses OpenAI-compatible API)
            payload = {
                "model": request.model,
                "messages": messages,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "stream": False
            }
            
            # Make API call
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
            
            # Extract response
            choice = data["choices"][0]
            content = choice["message"]["content"] or ""
            usage = data.get("usage", {})
            
            return LLMResponse(
                content=content,
                model=data.get("model", request.model),
                provider=self.name,
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                },
                finish_reason=choice.get("finish_reason"),
                metadata={
                    "id": data.get("id"),
                    "x_groq": data.get("x_groq", {})  # Groq-specific metadata
                }
            )
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ProviderAuthenticationError(self.name)
            elif e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After")
                raise ProviderRateLimitError(self.name, retry_after)
            else:
                error_detail = e.response.text
                raise ProviderResponseError(self.name, f"HTTP {e.response.status_code}: {error_detail}")
        except httpx.TimeoutException:
            raise ProviderTimeoutError(self.name)
        except Exception as e:
            raise ProviderResponseError(self.name, f"Unexpected error: {str(e)}")
    
    async def stream_generate(self, request: LLMRequest) -> AsyncIterator[str]:
        """Stream completion from Groq"""
        try:
            # Build messages
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            # Build request payload with streaming
            payload = {
                "model": request.model,
                "messages": messages,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "stream": True
            }
            
            # Make streaming API call
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.BASE_URL}/chat/completions",
                    headers=self.headers,
                    json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            if data_str == "[DONE]":
                                break
                            try:
                                import json
                                data = json.loads(data_str)
                                if data["choices"]:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue
                                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ProviderAuthenticationError(self.name)
            elif e.response.status_code == 429:
                raise ProviderRateLimitError(self.name)
            else:
                raise ProviderResponseError(self.name, str(e))
        except httpx.TimeoutException:
            raise ProviderTimeoutError(self.name)
        except Exception as e:
            raise ProviderResponseError(self.name, f"Unexpected error: {str(e)}")
    
    async def validate_credentials(self) -> bool:
        """Validate API key by making a test request"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.BASE_URL}/models",
                    headers=self.headers
                )
                return response.status_code == 200
        except:
            return False
    
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate Groq API key"""
        try:
            # Test with models endpoint (lightweight operation)
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.BASE_URL}/models",
                    headers=headers
                )
                return response.status_code == 200
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return False
            # Other errors don't necessarily mean invalid key
            return True
        except Exception:
            # Other errors don't necessarily mean invalid key
            return True
