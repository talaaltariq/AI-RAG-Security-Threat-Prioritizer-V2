"""ThreatIQ Database & State Refresh Script.

Completely wipes all ingested events, correlated incidents, score factors,
LLM explanations, RAG retrieval results, and analyst actions across all
detected ThreatIQ SQLite databases (root threatiq.db, backend/threatiq.db,
and any database referenced in DATABASE_URL).

Usage:
    python scripts/refresh_all_data.py
    python scripts/refresh_all_data.py [optional_path_to_threatiq.db]

After running this script:
    1. Start the backend (e.g. `python scripts/start_demo.py` or
       `uvicorn backend.main:app --reload`).
    2. Open the frontend and navigate to /setup.
    3. Upload your new event file and enter your API key.
    4. Click 'Run Analysis' to generate fresh stats on the dashboard.
"""

import os
import re
import socket
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Set

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

# Child tables first, parent tables last (foreign-key safe)
TABLES = [
    "analyst_actions",
    "rag_results",
    "llm_explanations",
    "score_factors",
    "events",
    "incidents",
]


def find_database_paths(custom_path: str | None = None) -> List[Path]:
    """Find all potential ThreatIQ SQLite database files in the repository."""
    discovered: Set[Path] = set()

    if custom_path:
        p = Path(custom_path).resolve()
        discovered.add(p)
        return list(discovered)

    # Standard locations
    candidates = [
        BACKEND_DIR / "threatiq.db",
        PROJECT_ROOT / "threatiq.db",
    ]

    # Parse DATABASE_URL from backend/.env or root .env
    for env_file in [BACKEND_DIR / ".env", PROJECT_ROOT / ".env"]:
        if env_file.exists():
            try:
                content = env_file.read_text(encoding="utf-8")
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("DATABASE_URL="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val.startswith("sqlite:///"):
                            rel_path = val.replace("sqlite:///", "")
                            if rel_path.startswith("./"):
                                # Relative to backend or root
                                candidates.append((BACKEND_DIR / rel_path).resolve())
                                candidates.append((PROJECT_ROOT / rel_path).resolve())
                            else:
                                candidates.append(Path(rel_path).resolve())
            except Exception:
                pass

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            discovered.add(candidate.resolve())

    return sorted(list(discovered))


def is_port_in_use(port: int = 8000, host: str = "127.0.0.1") -> bool:
    """Check if the backend port 8000 is currently occupied."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def clear_database(db_path: Path) -> Dict[str, int]:
    """Clear all event/incident data from the given SQLite database."""
    deleted_counts: Dict[str, int] = {}
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        # Enable FK enforcement so cascade or constraints behave properly
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Check which target tables exist in this DB
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}

        for table in TABLES:
            if table in existing_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                cursor.execute(f"DELETE FROM {table}")
                deleted_counts[table] = count
            else:
                deleted_counts[table] = 0

        # Reset pipeline_settings to defaults if present
        if "pipeline_settings" in existing_tables:
            cursor.execute("SELECT COUNT(*) FROM pipeline_settings")
            ps_count = cursor.fetchone()[0]
            if ps_count > 0:
                # Reset to canonical defaults
                cursor.execute("""
                    UPDATE pipeline_settings SET
                        anomaly_threshold = 0.5,
                        severity_critical_min = 80,
                        severity_high_min = 60,
                        severity_medium_min = 40,
                        severity_low_min = 20,
                        rag_top_k = 3,
                        rag_similarity_cutoff = 0.0,
                        enable_precaching = 1
                    WHERE id = 1
                """)

        conn.commit()

        # Vacuum to reclaim space and ensure clean state
        cursor.execute("VACUUM")
    finally:
        conn.close()

    # Clean up SQLite WAL / SHM files if present
    for suffix in ["-wal", "-shm"]:
        wal_file = Path(f"{db_path}{suffix}")
        if wal_file.exists():
            try:
                wal_file.unlink()
            except Exception:
                pass

    return deleted_counts


def main() -> int:
    print("=" * 64)
    print("         THREATIQ DATABASE & TELEMETRY REFRESH TOOL")
    print("=" * 64)

    custom_arg = sys.argv[1] if len(sys.argv) > 1 else None
    db_paths = find_database_paths(custom_arg)

    if not db_paths:
        print("[!] No threatiq.db SQLite database files found to reset.")
        print("    Your database is already clean or not yet created.")
        return 0

    # Warning if backend is currently running
    if is_port_in_use(8000):
        print("\n[NOTE] Port 8000 is currently active (FastAPI backend may be running).")
        print("       The database rows will be cleared, but remember to restart your")
        print("       backend process to reset any in-memory state as well.\n")

    total_cleared_events = 0
    total_cleared_incidents = 0

    for db_path in db_paths:
        rel_path = db_path.relative_to(PROJECT_ROOT) if db_path.is_relative_to(PROJECT_ROOT) else db_path
        print(f"\n[*] Resetting database: {rel_path}")
        try:
            counts = clear_database(db_path)
            for table, count in counts.items():
                print(f"    - {table:<20}: {count:>4} row(s) deleted")
            total_cleared_events += counts.get("events", 0)
            total_cleared_incidents += counts.get("incidents", 0)
        except Exception as err:
            print(f"    [ERROR] Failed to clear {rel_path}: {err}")

    print("\n" + "=" * 64)
    print("               DATABASE REFRESH COMPLETE")
    print("=" * 64)
    print(f"  Total events removed     : {total_cleared_events}")
    print(f"  Total incidents removed  : {total_cleared_incidents}")
    print("  Database state           : Completely empty (0 events, 0 incidents)")
    print("=" * 64)
    print("\n[HOW TO START FROM SCRATCH]:")
    print("  1. Start the backend:")
    print("     python scripts/start_demo.py")
    print("     (or: uvicorn backend.main:app --reload)")
    print("")
    print("  2. Open your frontend website:")
    print("     - Navigate to /setup (or click 'Setup' in the sidebar)")
    print("     - Tip: In browser devtools console, you can run:")
    print("       localStorage.clear()")
    print("       to see the initial 'First-Run Setup' welcome screen.")
    print("")
    print("  3. In Setup:")
    print("     - Step 1: Upload your new file (e.g. 50 events .json/.csv)")
    print("     - Step 2: Provide your Gemini API key & click 'Test Connection'")
    print("     - Step 3: Click 'Run Analysis'")
    print("")
    print("  4. Your dashboard will now display stats ONLY for your new file!")
    print("=" * 64 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
