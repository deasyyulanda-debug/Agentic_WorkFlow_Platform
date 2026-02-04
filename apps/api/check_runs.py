import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/db/agentic_platform.db')
cursor = conn.cursor()

cursor.execute('SELECT id, workflow_id, status, mode, created_at FROM runs ORDER BY created_at DESC LIMIT 10')

print('\n=== RECENT RUNS ===')
print(f"{'ID':<40} | {'Status':<10} | {'Mode':<10} | {'Created'}")
print('-' * 100)

for row in cursor.fetchall():
    run_id = row[0][:8] + '...'
    status = row[2]
    mode = row[3]
    created = row[4]
    print(f"{run_id:<40} | {status:<10} | {mode:<10} | {created}")

conn.close()
