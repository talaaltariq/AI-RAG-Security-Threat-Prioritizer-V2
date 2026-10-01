"""Reset the ThreatIQ demo database to an empty state (Phase 20).

Delegates to scripts/refresh_all_data.py to ensure all SQLite database
instances (in backend/ and project root) are cleanly wiped.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.refresh_all_data import main

if __name__ == "__main__":
    sys.exit(main())
