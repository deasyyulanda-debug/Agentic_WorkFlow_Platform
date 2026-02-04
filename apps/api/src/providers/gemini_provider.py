"""
Google Gemini Provider Adapter
Implements LLMProvider interface for Google Generative AI API
"""
from typing import AsyncIterator
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from .base import LLMProvider, LLMRequest, LLMResponse, BaseProvider, ModelCapability
from core.exceptions import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderResponseError
)


class GeminiProvider(BaseProvider):
    """Google Gemini API adapter"""
    
    def __init__(self, api_key: str, timeout: int = 60):
        super().__init__(api_key, timeout)
        genai.configure(api_key=api_key)
        self._name = "gemini"
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def supported_models(self) -> list[str]:
        return [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "gemini-2.0-flash-exp",
            "gemini-exp-1206"
        ]
    
    @property
    def capabilities(self) -> list[ModelCapability]:
        return [
            ModelCapability.TEXT_GENERATION,
            ModelCapability.STREAMING,
            ModelCapability.VISION
        ]
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate completion from Gemini"""
        try:
            # Create model
            model = genai.GenerativeModel(
                model_name=request.model,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # Build prompt (combine system + user)
            prompt_parts = []
            if request.system_prompt:
                prompt_parts.append(f"System: {request.system_prompt}\n\n")
            prompt_parts.append(request.prompt)
            full_prompt = "".join(prompt_parts)
            
            # Generate config
            generation_config = {
                "temperature": request.temperature,
            }
            if request.max_tokens:
                generation_config["max_output_tokens"] = request.max_tokens
            
            # Make API call
            response = await model.generate_content_async(
                full_prompt,
                generation_config=generation_config
            )
            
            # Extract content
            content = response.text if hasattr(response, "text") else ""
            
            # Extract usage (if available)
            usage = {}
            if hasattr(response, "usage_metadata"):
                usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count
                }
            
            return LLMResponse(
                content=content,
                model=request.model,
                provider=self.name,
                usage=usage,
                finish_reason=response.candidates[0].finish_reason.name if response.candidates else None,
                metadata={}
            )
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Map Gemini errors to our exceptions
            if "api key" in error_msg or "authentication" in error_msg or "401" in error_msg:
                raise ProviderAuthenticationError(self.name)
            elif "quota" in error_msg or "rate limit" in error_msg or "429" in error_msg:
                raise ProviderRateLimitError(self.name)
            elif "timeout" in error_msg:
                raise ProviderTimeoutError(self.name)
            else:
                raise ProviderResponseError(self.name, str(e))
    
    async def stream_generate(self, request: LLMRequest) -> AsyncIterator[str]:
        """Stream completion from Gemini"""
        try:
            # Create model (add models/ prefix if not present)
            model_name = request.model if request.model.startswith("models/") else f"models/{request.model}"
            model = genai.GenerativeModel(
                model_name=model_name,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # Build prompt
            prompt_parts = []
            if request.system_prompt:
                prompt_parts.append(f"System: {request.system_prompt}\n\n")
            prompt_parts.append(request.prompt)
            full_prompt = "".join(prompt_parts)
            
            # Generate config
            generation_config = {
                "temperature": request.temperature,
            }
            if request.max_tokens:
                generation_config["max_output_tokens"] = request.max_tokens
            
            # Make streaming API call
            response = await model.generate_content_async(
                full_prompt,
                generation_config=generation_config,
                stream=True
            )
            
            # Yield chunks
            async for chunk in response:
                if hasattr(chunk, "text"):
                    yield chunk.text
                    
        except Exception as e:
            error_msg = str(e).lower()
            
            if "api key" in error_msg or "authentication" in error_msg:
                raise ProviderAuthenticationError(self.name)
            elif "quota" in error_msg or "rate limit" in error_msg:
                raise ProviderRateLimitError(self.name)
            elif "timeout" in error_msg:
                raise ProviderTimeoutError(self.name)
            else:
                raise ProviderResponseError(self.name, str(e))
    
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate Gemini API key"""
        try:
            # Configure with test key
            genai.configure(api_key=api_key)
            
            # Try to list models (lightweight operation)
            models = genai.list_models()
            list(models)  # Consume iterator to trigger API call
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if "api key" in error_msg or "authentication" in error_msg:
                return False
            # Other errors don't necessarily mean invalid key
            return True
