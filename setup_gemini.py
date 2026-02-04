import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

print("=== Deleting and Recreating Gemini Provider ===\n")

# 1. Get existing settings
response = requests.get(f"{BASE_URL}/settings")
if response.status_code == 200:
    settings = response.json()
    gemini = [s for s in settings if s['provider'] == 'gemini']
    
    if gemini:
        gemini_id = gemini[0]['id']
        print(f"Found existing Gemini provider: {gemini_id[:8]}...")
        
        # Delete it
        response = requests.delete(f"{BASE_URL}/settings/{gemini_id}")
        if response.status_code == 204:
            print("✓ Deleted existing provider")
        else:
            print(f"✗ Failed to delete: {response.status_code}")
            exit(1)

# 2. Prompt for API key
print("\nEnter your Google Gemini API key:")
api_key = input("> ").strip()

if not api_key:
    print("✗ API key is required!")
    exit(1)

# 3. Create new provider
payload = {
    "provider": "gemini",
    "api_key": api_key,
    "is_active": True
}

print(f"\nCreating new Gemini provider...")
response = requests.post(
    f"{BASE_URL}/settings",
    json=payload,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 201:
    setting = response.json()
    print(f"✓ Provider created successfully!")
    print(f"   ID: {setting['id']}")
    print(f"   Provider: {setting['provider']}")
    print(f"   Active: {setting['is_active']}")
    
    # Test it
    print(f"\nTesting connection...")
    response = requests.post(f"{BASE_URL}/settings/{setting['id']}/test")
    if response.status_code == 200:
        print("✓ Connection test PASSED!")
    else:
        print(f"✗ Connection test FAILED: {response.text}")
else:
    print(f"✗ Failed to create: {response.status_code}")
    print(response.text)
