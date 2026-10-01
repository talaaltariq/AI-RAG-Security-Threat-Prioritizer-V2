"""ThreatIQ Root Reset Entry Point.

Convenience entry point to run `python reset.py` from the project root.
Delegates to `scripts/refresh_all_data.py`.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.refresh_all_data import main

if __name__ == "__main__":
    sys.exit(main())
