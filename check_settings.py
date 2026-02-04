import requests

response = requests.get("http://localhost:8000/api/v1/settings")
if response.status_code == 200:
    settings = response.json()
    print(f"Total settings: {len(settings)}")
    for s in settings:
        print(f"  - {s['provider']}: active={s['is_active']}, key={'*' * 10 if s.get('api_key') else 'NOT SET'}")
        
    active = [s for s in settings if s['is_active']]
    if active:
        print(f"\n✓ Active provider found: {active[0]['provider']}")
    else:
        print("\n✗ NO ACTIVE PROVIDER! This will cause execution to fail.")
else:
    print(f"Error: {response.status_code}")
