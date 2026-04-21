#!/usr/bin/env python3
"""
One-time script: ALTER TABLE project_chapters — add 4 BGM fields

Wave 4 Pipeline Integration (TASK-MUREKA-PIPELINE-INTEGRATION Step 8)

Adds:
  - bgm_url         VARCHAR(500)  NULL
  - bgm_volume      FLOAT         DEFAULT 1.0
  - bgm_meta_version VARCHAR(50)  NULL
  - credits_used    INT           DEFAULT 0

Uses .env MySQL credentials (shared Aliyun MySQL).
"""

import os
import sys

# Load env from .env file in project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, ".env")

# Simple .env parser (avoid dotenv dependency)
env_vars = {}
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip()

# Extract MySQL connection params
MYSQL_HOST = env_vars.get("MYSQL_HOST") or "101.132.69.232"
MYSQL_PORT = int(env_vars.get("MYSQL_PORT") or "3306")
MYSQL_USER = env_vars.get("MYSQL_USER") or "root"
MYSQL_DATABASE = env_vars.get("MYSQL_DATABASE") or "prefacestory"
MYSQL_PASSWORD = env_vars.get("MYSQL_PASSWORD") or ""

# If DATABASE_URL exists, parse it
database_url = env_vars.get("DATABASE_URL", "")
if database_url and "mysql" in database_url:
    # mysql+aiomysql://user:pass@host:port/db
    import re
    m = re.match(r"mysql[^:]*://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)", database_url)
    if m:
        MYSQL_USER = m.group(1)
        MYSQL_PASSWORD = m.group(2)
        MYSQL_HOST = m.group(3)
        MYSQL_PORT = int(m.group(4))
        MYSQL_DATABASE = m.group(5)

print(f"Connecting to MySQL: {MYSQL_USER}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")

try:
    import pymysql
except ImportError:
    print("ERROR: pymysql not installed. Run: pip install pymysql")
    sys.exit(1)

conn = pymysql.connect(
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE,
    charset="utf8mb4",
)
cursor = conn.cursor()

# Check current columns first
cursor.execute("DESCRIBE project_chapters;")
existing_columns = {row[0] for row in cursor.fetchall()}
print(f"\nExisting columns: {sorted(existing_columns)}")

bgm_columns = {
    "bgm_url": "ADD COLUMN bgm_url VARCHAR(500) NULL",
    "bgm_volume": "ADD COLUMN bgm_volume FLOAT DEFAULT 1.0",
    "bgm_meta_version": "ADD COLUMN bgm_meta_version VARCHAR(50) NULL",
    "credits_used": "ADD COLUMN credits_used INT DEFAULT 0",
}

# Only add columns that don't already exist
to_add = [(col, sql) for col, sql in bgm_columns.items() if col not in existing_columns]

if not to_add:
    print("\n✅ All 4 BGM columns already exist — nothing to do.")
else:
    print(f"\nAdding {len(to_add)} column(s): {[col for col, _ in to_add]}")
    alter_parts = ", ".join(sql for _, sql in to_add)
    alter_sql = f"ALTER TABLE project_chapters {alter_parts};"
    print(f"SQL: {alter_sql}")
    cursor.execute(alter_sql)
    conn.commit()
    print("✅ ALTER TABLE executed successfully.")

# Verify
cursor.execute("DESCRIBE project_chapters;")
rows = cursor.fetchall()
print("\n=== project_chapters columns (after) ===")
for row in rows:
    marker = " ← NEW" if row[0] in bgm_columns and row[0] not in existing_columns else ""
    print(f"  {row[0]:35s} {row[1]}{marker}")

cursor.close()
conn.close()
print("\nDone.")
