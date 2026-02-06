import sqlite3

db_path = "apps/api/data/db/workflows.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, provider, encrypted_value, is_active, last_tested_at, test_status FROM settings")
rows = cursor.fetchall()

print("Settings in database:")
print("=" * 80)
for row in rows:
    setting_id, provider, encrypted_value, is_active, last_tested, test_status = row
    print(f"\nProvider: {provider}")
    print(f"  ID: {setting_id}")
    print(f"  Active: {bool(is_active)}")
    print(f"  encrypted_value: '{encrypted_value}'")
    print(f"  encrypted_value length: {len(encrypted_value) if encrypted_value else 0}")
    print(f"  Last tested: {last_tested}")
    print(f"  Test status: {test_status}")

conn.close()
