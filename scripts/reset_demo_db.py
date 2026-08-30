"""Reset the ThreatIQ demo database to an empty state (Phase 20).

Deletes every incident and all related rows (events, score factors, RAG
results, LLM explanations, analyst actions) so the demo can start from an
empty dashboard and be practiced repeatedly:

    venv\\Scripts\\python.exe scripts\\reset_demo_db.py
    venv\\Scripts\\python.exe scripts\\reset_demo_db.py path\\to\\threatiq.db

The default target is backend/threatiq.db, the database the backend uses
when started with ``cd backend && uvicorn main:app --reload`` (the
DATABASE_URL in backend/.env is the CWD-relative ``sqlite:///./threatiq.db``).
Stop the backend before running this script so no connection holds the
SQLite file open.
"""

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "backend" / "threatiq.db"

# Child tables first, parent table last (foreign-key safe).
TABLES = [
    "analyst_actions",
    "rag_results",
    "llm_explanations",
    "score_factors",
    "events",
    "incidents",
]


def main() -> int:
    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB_PATH
    if not db_path.exists():
        print(f"Nothing to reset: {db_path} does not exist (already clean).")
        return 0

    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.cursor()
        for table in TABLES:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            cursor.execute(f"DELETE FROM {table}")
            print(f"  cleared {table}: {count} row(s) deleted")
        connection.commit()
    finally:
        connection.close()

    print(f"Demo database reset: {db_path} (dashboard will show 0 incidents).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
