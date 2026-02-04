import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

print("=== Testing Workflow Execution API ===\n")

# Get workflows
print("1. Fetching workflows...")
response = requests.get(f"{BASE_URL}/workflows")
if response.status_code == 200:
    workflows = response.json()
    print(f"   ✓ Found {len(workflows)} workflows")
    
    if workflows:
        workflow = workflows[0]
        workflow_id = workflow['id']
        print(f"   Using workflow: {workflow['name']} (ID: {workflow_id[:8]}...)")
        
        # Execute workflow
        print("\n2. Executing workflow...")
        payload = {
            "workflow_id": workflow_id,
            "input_data": {},
            "mode": "test_run"
        }
        
        response = requests.post(
            f"{BASE_URL}/runs/execute-async",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 202:
            run = response.json()
            run_id = run['id']
            print(f"   ✓ Run created: {run_id[:8]}...")
            print(f"   Initial status: {run['status']}")
            
            # Monitor run status
            print("\n3. Monitoring run status...")
            for i in range(10):
                time.sleep(2)
                response = requests.get(f"{BASE_URL}/runs/{run_id}")
                if response.status_code == 200:
                    run = response.json()
                    status = run['status']
                    print(f"   [{i*2}s] Status: {status}")
                    
                    if status in ['completed', 'failed', 'cancelled']:
                        print(f"\n   ✓ Run finished with status: {status}")
                        if run.get('output_data'):
                            print(f"   Output: {json.dumps(run['output_data'], indent=2)}")
                        break
                else:
                    print(f"   ✗ Error fetching run: {response.status_code}")
                    break
        else:
            print(f"   ✗ Error: {response.text}")
else:
    print(f"   ✗ Error fetching workflows: {response.status_code}")
