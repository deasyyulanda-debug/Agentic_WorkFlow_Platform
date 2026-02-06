"""
Standalone script to list all available models from each provider
Run: python list_provider_models.py
"""
import sys
import os

# Add the API source to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api', 'src'))

from providers.openai_provider import OpenAIProvider
from providers.anthropic_provider import AnthropicProvider
from providers.gemini_provider import GeminiProvider
from providers.deepseek_provider import DeepSeekProvider
from providers.openrouter_provider import OpenRouterProvider
from providers.groq_provider import GroqProvider

def list_all_models():
    """List all models from all providers"""
    
    providers = {
        "OpenAI": OpenAIProvider("dummy_key", 30),
        "Anthropic": AnthropicProvider("dummy_key", 30),
        "Gemini": GeminiProvider("dummy_key", 30),
        "DeepSeek": DeepSeekProvider("dummy_key", 30),
        "OpenRouter": OpenRouterProvider("dummy_key", 30),
        "Groq": GroqProvider("dummy_key", 30)
    }
    
    print("\n" + "="*80)
    print("AVAILABLE MODELS BY PROVIDER")
    print("="*80 + "\n")
    
    for name, provider in providers.items():
        print(f"📦 {name}")
        print("-" * 80)
        models = provider.supported_models
        for i, model in enumerate(models, 1):
            print(f"  {i:2d}. {model}")
        print(f"\n  Total: {len(models)} models")
        print()
    
    print("="*80)
    print(f"TOTAL MODELS ACROSS ALL PROVIDERS: {sum(len(p.supported_models) for p in providers.values())}")
    print("="*80 + "\n")

if __name__ == "__main__":
    list_all_models()
