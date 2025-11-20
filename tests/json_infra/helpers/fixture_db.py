"""
SQLite database backend for JSON test fixtures.

Provides faster test collection by pre-parsing and indexing JSON test fixtures.
"""

import hashlib
import json
import os
import sqlite3
from glob import glob
from typing import Any, Dict, Generator, Optional

from ethereum_spec_tools.evm_tools.statetest import read_test_cases

from .. import FORKS
from .exceptional_test_patterns import (
    exceptional_blockchain_test_patterns,
    exceptional_state_test_patterns,
)


class FixtureDatabase:
    """Manages SQLite database for JSON test fixtures."""

    def __init__(self, db_path: str = "tests/json_infra/fixtures.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Connect to database with optimized settings."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            # Performance optimizations
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.conn.execute("PRAGMA temp_store=MEMORY")
            self.conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
        return self.conn

    def initialize_schema(self) -> None:
        """Create database tables and indexes."""
        conn = self.connect()

        # Main test fixtures table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS test_fixtures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_key TEXT NOT NULL,
                test_type TEXT NOT NULL,
                fork TEXT NOT NULL,
                source_file TEXT NOT NULL,
                test_index INTEGER DEFAULT 0,
                test_data TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                is_slow INTEGER DEFAULT 0,
                is_bigmem INTEGER DEFAULT 0,
                is_expected_fail INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(test_key, fork, test_type, test_index, source_file)
            )
        """
        )

        # Indexes for fast lookups
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_test_type_fork
            ON test_fixtures(test_type, fork)
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_fork
            ON test_fixtures(fork)
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_source_file
            ON test_fixtures(source_file)
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_file_hash
            ON test_fixtures(file_hash)
        """
        )

        # Metadata table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fixture_metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()

    def compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file."""
        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def is_file_cached(self, file_path: str, fork: str | None = None) -> bool:
        """
        Check if file is already in database and unchanged.

        Args:
            file_path: Path to the file to check
            fork: Optional fork name. If provided, checks if file
                  is cached for this specific fork.
                  If not provided, checks if file is cached for any fork.

        """
        if not os.path.exists(file_path):
            return False

        file_hash = self.compute_file_hash(file_path)
        conn = self.connect()

        if fork is not None:
            # Check if file is cached for this specific fork
            cursor = conn.execute(
                "SELECT 1 FROM test_fixtures WHERE source_file = ? AND file_hash = ? AND fork = ? LIMIT 1",  # noqa: E501
                (file_path, file_hash, fork),
            )
        else:
            # Check if file is cached for any fork
            cursor = conn.execute(
                "SELECT 1 FROM test_fixtures WHERE source_file = ? AND file_hash = ? LIMIT 1",  # noqa: E501
                (file_path, file_hash),
            )
        return cursor.fetchone() is not None

    def load_state_test_file(
        self, file_path: str, json_fork: str, eels_fork: str
    ) -> int:
        """Load a state test JSON file into the database."""
        if self.is_file_cached(file_path, fork=json_fork):
            return 0  # Already loaded

        try:
            test_cases = read_test_cases(file_path)
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            return 0

        file_hash = self.compute_file_hash(file_path)
        test_patterns = exceptional_state_test_patterns(json_fork, eels_fork)

        records = []
        for test_case in test_cases:
            if test_case.fork_name != json_fork:
                continue

            is_slow = any(p.search(test_case.key) for p in test_patterns.slow)
            is_bigmem = False

            # Store minimal data needed for test case dict
            test_data = {
                "test_file": test_case.path,
                "test_key": test_case.key,
                "index": test_case.index,
                "json_fork": json_fork,
            }

            records.append(
                (
                    test_case.key,
                    "state",
                    json_fork,
                    file_path,
                    test_case.index,
                    json.dumps(test_data),
                    file_hash,
                    int(is_slow),
                    int(is_bigmem),
                    0,
                )
            )

        if records:
            conn = self.connect()
            conn.executemany(
                """INSERT OR REPLACE INTO test_fixtures
                   (test_key, test_type, fork, source_file, test_index,
                    test_data, file_hash, is_slow, is_bigmem, is_expected_fail)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                records,
            )
            conn.commit()

        return len(records)

    def load_blockchain_test_file(
        self, file_path: str, json_fork: str, eels_fork: str
    ) -> int:
        """Load a blockchain test JSON file into the database."""
        if self.is_file_cached(file_path, fork=json_fork):
            return 0

        try:
            with open(file_path, "r") as fp:
                data = json.load(fp)
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            return 0

        file_hash = self.compute_file_hash(file_path)
        test_patterns = exceptional_blockchain_test_patterns(
            json_fork, eels_fork
        )

        records = []
        found_keys = []
        for key, test in data.items():
            if "network" not in test:
                continue
            if test["network"] == json_fork:
                found_keys.append(key)

        for test_key in found_keys:
            identifier = f"({file_path}|{test_key})"

            # Check if expected to fail
            if any(x.search(identifier) for x in test_patterns.expected_fail):
                continue

            is_slow = any(x.search(identifier) for x in test_patterns.slow)
            is_bigmem = any(
                x.search(identifier) for x in test_patterns.big_memory
            )

            test_data = {
                "test_file": file_path,
                "test_key": test_key,
                "json_fork": json_fork,
                "eels_fork": eels_fork,
            }

            records.append(
                (
                    test_key,
                    "blockchain",
                    json_fork,
                    file_path,
                    0,
                    json.dumps(test_data),
                    file_hash,
                    int(is_slow),
                    int(is_bigmem),
                    0,
                )
            )

        if records:
            conn = self.connect()
            conn.executemany(
                """INSERT OR REPLACE INTO test_fixtures
                   (test_key, test_type, fork, source_file, test_index,
                    test_data, file_hash, is_slow, is_bigmem, is_expected_fail)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                records,
            )
            conn.commit()

        return len(records)

    def load_generic_test_file(self, file_path: str, test_type: str) -> int:
        """Load a generic test JSON file (TransactionTests, RLPTests, etc.)."""
        if self.is_file_cached(file_path, fork="all"):
            return 0

        try:
            with open(file_path, "r") as fp:
                data = json.load(fp)
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            return 0

        file_hash = self.compute_file_hash(file_path)
        records = []

        # Handle case where JSON root is a list (some test files)
        if isinstance(data, list):
            return 0

        # These test types don't have fork-specific versions
        # Each key in the JSON is a test case
        for test_key, test_data in data.items():
            if not isinstance(test_data, dict):
                continue

            test_data_dict = {
                "test_file": file_path,
                "test_key": test_key,
                "test_type": test_type,
            }

            records.append(
                (
                    test_key,
                    test_type,
                    "all",  # These tests apply to all forks
                    file_path,
                    0,
                    json.dumps(test_data_dict),
                    file_hash,
                    0,  # is_slow
                    0,  # is_bigmem
                    0,  # is_expected_fail
                )
            )

        if records:
            conn = self.connect()
            conn.executemany(
                """INSERT OR REPLACE INTO test_fixtures
                   (test_key, test_type, fork, source_file, test_index,
                    test_data, file_hash, is_slow, is_bigmem, is_expected_fail)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                records,
            )
            conn.commit()

        return len(records)

    def load_all_state_tests(self) -> Dict[str, int]:
        """
        Load all state test fixtures for all forks.

        Optimized to parse each file only once and extract tests for all forks.
        """
        # First pass: collect all unique files across all forks
        all_files = set()
        for _, config in FORKS.items():
            test_dirs = config["state_test_dirs"]
            for test_dir in test_dirs:
                if not os.path.exists(test_dir):
                    continue
                json_files = glob(
                    os.path.join(test_dir, "**/*.json"), recursive=True
                )
                for full_path in json_files:
                    all_files.add(full_path)

        print(
            f"Processing {len(all_files)} unique state "
            "test files across all forks..."
        )

        # Second pass: process each file once and extract tests for all forks
        stats = dict.fromkeys(FORKS, 0)
        processed = 0

        for file_path in all_files:
            if self.is_file_cached(file_path):
                # File already processed for all forks
                continue

            try:
                test_cases = read_test_cases(file_path)
            except Exception as e:
                print(f"Warning: Failed to parse {file_path}: {e}")
                continue

            file_hash = self.compute_file_hash(file_path)

            # Group test cases by fork
            tests_by_fork: dict[Any, Any] = {}
            for test_case in test_cases:
                fork = test_case.fork_name
                if fork not in tests_by_fork:
                    tests_by_fork[fork] = []
                tests_by_fork[fork].append(test_case)

            # Insert tests for each fork found in this file
            conn = self.connect()
            for json_fork, test_cases_for_fork in tests_by_fork.items():
                if json_fork not in FORKS:
                    continue

                eels_fork = FORKS[json_fork]["eels_fork"]
                test_patterns = exceptional_state_test_patterns(
                    json_fork, eels_fork
                )

                records = []
                for test_case in test_cases_for_fork:
                    is_slow = any(
                        p.search(test_case.key) for p in test_patterns.slow
                    )
                    is_bigmem = False

                    test_data = {
                        "test_file": test_case.path,
                        "test_key": test_case.key,
                        "index": test_case.index,
                        "json_fork": json_fork,
                    }

                    records.append(
                        (
                            test_case.key,
                            "state",
                            json_fork,
                            file_path,
                            test_case.index,
                            json.dumps(test_data),
                            file_hash,
                            int(is_slow),
                            int(is_bigmem),
                            0,
                        )
                    )

                if records:
                    conn.executemany(
                        """INSERT OR REPLACE INTO test_fixtures
                           (test_key, test_type, fork, source_file, test_index,
                            test_data, file_hash, is_slow, is_bigmem,
                            is_expected_fail)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        records,
                    )
                    stats[json_fork] += len(records)

            conn.commit()
            processed += 1
            if processed % 1000 == 0:
                print(f"  Processed {processed}/{len(all_files)} files...")

        # Print summary
        for fork, count in sorted(stats.items()):
            if count > 0:
                print(f"Loaded {count} state tests for {fork}")

        return stats

    def load_all_blockchain_tests(self) -> Dict[str, int]:
        """
        Load all blockchain test fixtures for all forks.

        Optimized to parse each file only once and extract tests for all forks.
        """
        # First pass: collect all unique files across all forks
        all_files = set()
        for _, config in FORKS.items():
            test_dirs = config["blockchain_test_dirs"]
            for test_dir in test_dirs:
                if not os.path.exists(test_dir):
                    continue
                json_files = glob(
                    os.path.join(test_dir, "**/*.json"), recursive=True
                )
                for full_path in json_files:
                    # Skip pre_alloc directories - they contain
                    # metadata, not tests
                    if "/pre_alloc/" not in full_path:
                        all_files.add(full_path)

        print(
            f"Processing {len(all_files)} unique blockchain test "
            "files across all forks..."
        )

        # Second pass: process each file once and extract tests for all forks
        stats = dict.fromkeys(FORKS, 0)
        processed = 0

        for file_path in all_files:
            if self.is_file_cached(file_path):
                # File already processed for all forks
                continue

            try:
                with open(file_path, "r") as fp:
                    data = json.load(fp)
            except Exception as e:
                print(f"Warning: Failed to parse {file_path}: {e}")
                continue

            file_hash = self.compute_file_hash(file_path)

            # Group tests by network (fork)
            tests_by_fork: dict[Any, Any] = {}
            for key, test in data.items():
                if not isinstance(test, dict):
                    continue
                if "network" not in test:
                    continue

                network = test["network"]
                if network not in tests_by_fork:
                    tests_by_fork[network] = []
                tests_by_fork[network].append(key)

            # Insert tests for each fork found in this file
            conn = self.connect()
            for json_fork, test_keys in tests_by_fork.items():
                if json_fork not in FORKS:
                    continue

                eels_fork = FORKS[json_fork]["eels_fork"]
                test_patterns = exceptional_blockchain_test_patterns(
                    json_fork, eels_fork
                )

                # Skip files that are marked as expected_fail for this fork
                if any(
                    x.search(file_path) for x in test_patterns.expected_fail
                ):
                    continue

                records = []
                for test_key in test_keys:
                    identifier = f"({file_path}|{test_key})"

                    # Check if test case is expected to fail
                    if any(
                        x.search(identifier)
                        for x in test_patterns.expected_fail
                    ):
                        continue

                    is_slow = any(
                        x.search(identifier) for x in test_patterns.slow
                    )
                    is_bigmem = any(
                        x.search(identifier) for x in test_patterns.big_memory
                    )

                    test_data = {
                        "test_file": file_path,
                        "test_key": test_key,
                        "json_fork": json_fork,
                        "eels_fork": eels_fork,
                    }

                    records.append(
                        (
                            test_key,
                            "blockchain",
                            json_fork,
                            file_path,
                            0,
                            json.dumps(test_data),
                            file_hash,
                            int(is_slow),
                            int(is_bigmem),
                            0,
                        )
                    )

                if records:
                    conn.executemany(
                        """INSERT OR REPLACE INTO test_fixtures
                           (test_key, test_type, fork, source_file, test_index,
                            test_data, file_hash, is_slow, is_bigmem,
                            is_expected_fail)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        records,
                    )
                    stats[json_fork] += len(records)

            conn.commit()
            processed += 1
            if processed % 1000 == 0:
                print(f"  Processed {processed}/{len(all_files)} files...")

        # Print summary
        for fork, count in sorted(stats.items()):
            if count > 0:
                print(f"Loaded {count} blockchain tests for {fork}")

        return stats

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        conn = self.connect()

        cursor = conn.execute("SELECT COUNT(*) as total FROM test_fixtures")
        total = cursor.fetchone()["total"]

        cursor = conn.execute(
            """
            SELECT test_type, fork, COUNT(*) as count
            FROM test_fixtures
            GROUP BY test_type, fork
            ORDER BY test_type, fork
        """
        )
        by_type_fork = [dict(row) for row in cursor.fetchall()]

        return {"total_tests": total, "by_type_and_fork": by_type_fork}

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


class FixtureQuery:
    """Query layer for database-backed test fixtures."""

    def __init__(self, db_path: str = "tests/json_infra/fixtures.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Connect to database."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def fetch_state_tests(self, fork: str) -> Generator[Dict, None, None]:
        """Fetch state tests for a specific fork."""
        conn = self.connect()
        cursor = conn.execute(
            """SELECT test_data, is_slow, is_bigmem
               FROM test_fixtures
               WHERE test_type = 'state' AND fork = ?
               ORDER BY source_file, test_index""",
            (fork,),
        )

        for row in cursor:
            test_data = json.loads(row["test_data"])
            yield {
                "data": test_data,
                "is_slow": bool(row["is_slow"]),
                "is_bigmem": bool(row["is_bigmem"]),
            }

    def fetch_blockchain_tests(self, fork: str) -> Generator[Dict, None, None]:
        """Fetch blockchain tests for a specific fork."""
        conn = self.connect()
        cursor = conn.execute(
            """SELECT test_data, is_slow, is_bigmem
               FROM test_fixtures
               WHERE test_type = 'blockchain' AND fork = ?
               ORDER BY source_file""",
            (fork,),
        )

        for row in cursor:
            test_data = json.loads(row["test_data"])
            yield {
                "data": test_data,
                "is_slow": bool(row["is_slow"]),
                "is_bigmem": bool(row["is_bigmem"]),
            }

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
