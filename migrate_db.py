"""
Run this script to create new tables in Supabase.
You need your Supabase service_role key.

How to get your service_role key:
1. Go to https://supabase.com/dashboard
2. Select your project (zxxicqeaquitbrprlded)
3. Go to Project Settings -> API
4. Copy the service_role key
5. Run: python3 migrate_db.py YOUR_SERVICE_KEY
"""

import sys
import requests

SQL = """
CREATE TABLE IF NOT EXISTS public.surahs (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    kid_id INTEGER REFERENCES public.kids(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES public.parents(id) ON DELETE CASCADE,
    total_ayahs INTEGER NOT NULL,
    memorized_ayahs INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'In Progress',
    last_practiced_date TEXT,
    finished_date TEXT
);

CREATE TABLE IF NOT EXISTS public.reward_sessions (
    id SERIAL PRIMARY KEY,
    kid_id INTEGER REFERENCES public.kids(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES public.parents(id) ON DELETE CASCADE,
    month TEXT NOT NULL,
    total_points INTEGER NOT NULL DEFAULT 0,
    reward_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    paid BOOLEAN NOT NULL DEFAULT FALSE,
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.points_adjustments (
    id SERIAL PRIMARY KEY,
    person_id INTEGER NOT NULL,
    person_type TEXT NOT NULL CHECK (person_type IN ('kid', 'parent')),
    points INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 migrate_db.py YOUR_SERVICE_ROLE_KEY")
        print()
        print("SQL that will be executed:")
        print(SQL)
        sys.exit(1)

    service_key = sys.argv[1]
    url = "https://zxxicqeaquitbrprlded.supabase.co"

    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    }

    print("Creating tables...")

    for statement in SQL.split(";"):
        statement = statement.strip()
        if not statement:
            continue

        r = requests.post(
            f"{url}/rest/v1/sql",
            json={"query": statement + ";"},
            headers=headers
        )

        if r.status_code == 200:
            print(f"  ✅ {statement[:60]}...")
        elif "already exists" in r.text:
            print(f"  ⏭️  Already exists: {statement[:60]}...")
        else:
            print(f"  ❌ Error: {r.status_code} {r.text[:300]}")

    print()
    print("Done! Restart the app now.")


if __name__ == "__main__":
    main()
