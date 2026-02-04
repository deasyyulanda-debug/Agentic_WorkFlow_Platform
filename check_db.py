import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('apps/api/data/db/workflows.db')
c = conn.cursor()

# Get latest 3 runs
print("=" * 60)
print("LATEST RUNS IN DATABASE")
print("=" * 60)
c.execute('''SELECT id, status, run_mode, validation_result, created_at 
             FROM runs ORDER BY created_at DESC LIMIT 3''')
rows = c.fetchall()

for i, row in enumerate(rows, 1):
    print(f"\n{i}. Run ID: {row[0][:20]}...")
    print(f"   Status: {row[1]}")
    print(f"   Mode: {row[2]}")
    print(f"   Created: {row[4]}")
    
    if row[3]:
        vr = json.loads(row[3])
        print(f"   ✅ HAS validation_result!")
        print(f"   Keys: {list(vr.keys())[:5]}")
        # Show a preview of content if it exists
        if isinstance(vr, dict):
            for key in ['content', 'output', 'response', 'result']:
                if key in vr:
                    val = str(vr[key])[:80]
                    print(f"   {key}: {val}...")
                    break
    else:
        print(f"   ❌ validation_result is NULL")

conn.close()
