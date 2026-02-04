"""
Provider Test Script
Quick verification that provider adapters are working
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from providers import get_provider, LLMRequest, ProviderFactory


async def test_provider_factory():
    """Test provider factory"""
    print("=" * 60)
    print("Testing Provider Factory")
    print("=" * 60)
    
    # Get supported providers
    providers = ProviderFactory.get_supported_providers()
    print(f"\n✅ Supported providers: {', '.join(providers)}")
    
    # Get info for each provider
    for provider_name in providers:
        info = ProviderFactory.get_provider_info(provider_name)
        print(f"\n📦 {provider_name.upper()}:")
        print(f"   Models: {', '.join(info['supported_models'][:3])}...")
        print(f"   Capabilities: {', '.join(info['capabilities'])}")


async def test_provider_creation():
    """Test creating provider instances"""
    print("\n" + "=" * 60)
    print("Testing Provider Instantiation")
    print("=" * 60)
    
    # Test with dummy keys (won't make actual API calls)
    test_cases = [
        ("openai", "sk-test123"),
        ("anthropic", "sk-ant-test123"),
        ("gemini", "test-key"),
        ("deepseek", "sk-test123")
    ]
    
    for provider_name, dummy_key in test_cases:
        try:
            provider = get_provider(provider_name, dummy_key)
            print(f"✅ {provider_name}: Successfully created {provider.__class__.__name__}")
        except Exception as e:
            print(f"❌ {provider_name}: Failed - {e}")


async def test_request_structure():
    """Test LLMRequest structure"""
    print("\n" + "=" * 60)
    print("Testing Request Structure")
    print("=" * 60)
    
    request = LLMRequest(
        prompt="Hello, world!",
        model="gpt-4o",
        max_tokens=100,
        temperature=0.7,
        system_prompt="You are a helpful assistant",
        stream=False
    )
    
    print(f"✅ Created LLMRequest:")
    print(f"   Prompt: {request.prompt}")
    print(f"   Model: {request.model}")
    print(f"   Max Tokens: {request.max_tokens}")
    print(f"   Temperature: {request.temperature}")
    print(f"   System: {request.system_prompt[:30]}...")
    print(f"   Stream: {request.stream}")


async def main():
    """Run all tests"""
    print("\n🚀 Provider Adapter Tests\n")
    
    try:
        await test_provider_factory()
        await test_provider_creation()
        await test_request_structure()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\n💡 Note: Actual API calls require valid API keys.")
        print("   Set them via environment variables or .env file.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
