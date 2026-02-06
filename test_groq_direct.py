"""
Direct test of Groq API
"""
import asyncio
import httpx
import sys
import os
import sqlite3

# Add src to path
sys.path.insert(0, 'apps/api/src')

async def test_groq():
    print("=" * 60)
    print("Testing Groq API Directly")
    print("=" * 60)
    
    # Get Groq API key from database
    print("\n1. Fetching Groq settings from database...")
    db_path = "apps/api/data/db/workflows.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, provider, encrypted_value, is_active FROM settings WHERE provider = 'GROQ'")
    row = cursor.fetchone()
    
    if not row:
        print("❌ No Groq settings found in database!")
        conn.close()
        return
    
    setting_id, provider, encrypted_value, is_active = row
    print(f"✓ Groq settings found")
    print(f"  ID: {setting_id}")
    print(f"  Provider: {provider}")
    print(f"  Active: {bool(is_active)}")
    print(f"  Has encrypted value: {'Yes' if encrypted_value else 'No'}")
    
    if not encrypted_value:
        print("❌ No API key configured for Groq!")
        conn.close()
        return
    
    conn.close()
    
    # Decrypt the API key
    print("\n2. Decrypting API key...")
    from core.security import init_security, get_secret_manager
    import os
    
    # Get secret key from environment or use default
    secret_key = os.getenv('SECRET_KEY', 'test-secret-key-min-32-chars-long-for-fernet-encryption')
    
    # Initialize security
    init_security(secret_key)
    secret_manager = get_secret_manager()
    
    try:
        groq_key = secret_manager.decrypt(encrypted_value)
        print(f"✓ API key decrypted (length: {len(groq_key)})")
    except Exception as e:
        print(f"❌ Failed to decrypt: {e}")
        return
    
    # Test API call directly with httpx
    print("\n3. Testing Groq API call...")
    print("   URL: https://api.groq.com/openai/v1/chat/completions")
    print("   Model: llama-3.3-70b-versatile")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "user", "content": "Say 'Hello from Groq!' in exactly 5 words."}
                    ],
                    "max_tokens": 50,
                    "temperature": 0.7
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            print(f"\n✓ SUCCESS!")
            print(f"  Status: {response.status_code}")
            print(f"  Model: {result.get('model')}")
            print(f"  Tokens: {result.get('usage', {}).get('total_tokens', 0)}")
            print(f"  Response: {result['choices'][0]['message']['content']}")
            print(f"  Finish reason: {result['choices'][0]['finish_reason']}")
            
        except httpx.HTTPStatusError as e:
            print(f"\n❌ HTTP Error: {e.response.status_code}")
            print(f"  Response: {e.response.text}")
            return
        except Exception as e:
            print(f"\n❌ Request failed: {e}")
            import traceback
            traceback.print_exc()
            return
    
    print("\n" + "=" * 60)
    print("✓ Groq API is working correctly!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_groq())
