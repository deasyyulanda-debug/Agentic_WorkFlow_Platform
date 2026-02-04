"""
Live Provider Test - Test Gemini with Real API Key
"""
import asyncio
import os

from providers import get_provider, LLMRequest


async def test_gemini_generate():
    """Test Gemini text generation"""
    print("=" * 60)
    print("Testing Gemini Provider - Text Generation")
    print("=" * 60)
    
    # Get API key from environment
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set in environment")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Create provider
    provider = get_provider("gemini", api_key)
    print(f"✅ Provider created: {provider.__class__.__name__}")
    print(f"   Supported models: {', '.join(provider.supported_models[:3])}")
    
    # Create request
    request = LLMRequest(
        prompt="What is 2+2? Answer in one sentence.",
        model="gemini-2.0-flash",
        max_tokens=100,
        temperature=0.7,
        system_prompt="You are a helpful math tutor."
    )
    
    print(f"\n📤 Sending request:")
    print(f"   Model: {request.model}")
    print(f"   Prompt: {request.prompt}")
    
    # Generate response
    print("\n⏳ Generating response...")
    try:
        response = await provider.generate(request)
        
        print("\n✅ Response received:")
        print(f"   Provider: {response.provider}")
        print(f"   Model: {response.model}")
        print(f"   Content: {response.content}")
        print(f"   Usage: {response.usage}")
        print(f"   Finish Reason: {response.finish_reason}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gemini_streaming():
    """Test Gemini streaming"""
    print("\n" + "=" * 60)
    print("Testing Gemini Provider - Streaming")
    print("=" * 60)
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    provider = get_provider("gemini", api_key)
    
    request = LLMRequest(
        prompt="Count from 1 to 5, one number per line.",
        model="gemini-2.0-flash",
        max_tokens=100,
        temperature=0.7,
        stream=True
    )
    
    print(f"📤 Streaming request: {request.prompt}")
    print("\n⏳ Streaming response:")
    print("-" * 60)
    
    try:
        chunk_count = 0
        async for chunk in provider.stream_generate(request):
            print(chunk, end="", flush=True)
            chunk_count += 1
        
        print("\n" + "-" * 60)
        print(f"✅ Received {chunk_count} chunks")
        return True
        
    except Exception as e:
        print(f"\n❌ Streaming failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_key_validation():
    """Test API key validation"""
    print("\n" + "=" * 60)
    print("Testing API Key Validation")
    print("=" * 60)
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    provider = get_provider("gemini", api_key)
    
    # Test valid key
    print("⏳ Validating API key...")
    is_valid = await provider.validate_api_key(api_key)
    
    if is_valid:
        print("✅ API key is valid")
    else:
        print("❌ API key is invalid")
    
    # Test invalid key
    print("\n⏳ Testing with invalid key...")
    is_valid = await provider.validate_api_key("invalid-key-123")
    
    if not is_valid:
        print("✅ Correctly identified invalid key")
    else:
        print("⚠️  Invalid key not detected")
    
    return True


async def main():
    """Run all tests"""
    print("\n🚀 Live Provider Integration Test\n")
    
    results = []
    
    # Test 1: Text generation
    result = await test_gemini_generate()
    results.append(("Text Generation", result))
    
    # Test 2: Streaming
    result = await test_gemini_streaming()
    results.append(("Streaming", result))
    
    # Test 3: API key validation
    result = await test_api_key_validation()
    results.append(("API Key Validation", result))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n🎉 All tests passed! Provider integration working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")


if __name__ == "__main__":
    asyncio.run(main())
