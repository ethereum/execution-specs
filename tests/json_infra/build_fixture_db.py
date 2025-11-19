#!/usr/bin/env python3
"""
Build SQLite database from JSON test fixtures.

Usage:
    python -m tests.json_infra.build_fixture_db
"""

from tests.json_infra.helpers.fixture_db import FixtureDatabase


def main() -> None:
    """Build fixture DB."""
    db_path = "tests/json_infra/fixtures.db"
    print(f"Building fixture database at {db_path}")
    db = FixtureDatabase(db_path)
    db.initialize_schema()
    print("Loading state tests...")
    db.load_all_state_tests()
    print("Loading blockchain tests...")
    db.load_all_blockchain_tests()
    stats = db.get_statistics()
    print(f"Database built with {stats['total_tests']} total tests")
    db.close()


if __name__ == "__main__":
    main()
