#!/usr/bin/env python3
"""
Build SQLite database from JSON test fixtures.

Usage:
    python -m tests.json_infra.build_fixture_db
"""

import sys
from pathlib import Path

from tests.json_infra.helpers.fixture_db import FixtureDatabase

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def main() -> None:
    """Build fixture DB."""
    db_path = "tests/json_infra/fixtures.db"
    db = FixtureDatabase(db_path)
    db.initialize_schema()
    db.load_all_state_tests()
    db.load_all_blockchain_tests()
    db.close()


if __name__ == "__main__":
    main()
