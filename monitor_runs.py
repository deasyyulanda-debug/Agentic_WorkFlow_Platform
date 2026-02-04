import sqlite3
import time
from datetime import datetime

# Try to find the database
db_paths = [
    'data/db/agentic_platform.db',
    'apps/api/data/db/agentic_platform.db',
    'C:/Users/amitt/Agentic_WorkFlow_Platform/data/db/agentic_platform.db'
]

conn = None
for path in db_paths:
    try:
        conn = sqlite3.connect(path)
        print(f"✓ Found database at: {path}\n")
        break
    except:
        continue

if not conn:
    print("✗ Could not find database")
    exit(1)

cursor = conn.cursor()

# Check if runs table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='runs'")
if not cursor.fetchone():
    print("✗ No 'runs' table found")
    exit(1)

print("=== MONITORING RUNS (press Ctrl+C to stop) ===\n")
print(f"{'Time':<12} | {'Run ID':<10} | {'Status':<12} | {'Mode':<12}")
print('-' * 80)

last_count = 0
while True:
    cursor.execute('SELECT COUNT(*) FROM runs')
    count = cursor.fetchone()[0]
    
    if count != last_count:
        cursor.execute('SELECT id, status, mode, created_at FROM runs ORDER BY created_at DESC LIMIT 1')
        row = cursor.fetchone()
        if row:
            now = datetime.now().strftime('%H:%M:%S')
            run_id = row[0][:8]
            status = row[1]
            mode = row[2]
            print(f"{now:<12} | {run_id:<10} | {status:<12} | {mode:<12}")
        last_count = count
    
    time.sleep(1)
