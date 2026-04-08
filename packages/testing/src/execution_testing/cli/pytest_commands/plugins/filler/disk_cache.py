"""Disk-based cache for t8n outputs that persists across fill runs."""

import hashlib
import json
import logging
import pickle
import re
import sqlite3
import zlib
from pathlib import Path
from typing import Any, Dict

from execution_testing.base_types import Bytes
from execution_testing.client_clis.cli_types import (
    LazyAllocJson,
    LazyAllocStr,
    Result,
    TransitionToolOutput,
    TransitionToolRequest,
)
from execution_testing.client_clis.transition_tool import model_dump_config

logger = logging.getLogger(__name__)


def fork_name_to_module(fork_name: str) -> str:
    """
    Convert a PascalCase fork name to its snake_case module/directory name.

    E.g. "ArrowGlacier" -> "arrow_glacier", "BPO1" -> "bpo1".
    """
    # Handle BPO forks: "BPO1" -> "bpo1"
    if fork_name.upper().startswith("BPO"):
        return fork_name.lower()
    # Standard PascalCase to snake_case
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", fork_name)
    return s.lower()


def hash_files(directory: Path) -> bytes:
    """
    Hash all .py files in a directory tree.

    Return raw SHA-256 digest bytes. Files are sorted by relative path
    for determinism.
    """
    h = hashlib.sha256()
    for py_file in sorted(directory.rglob("*.py")):
        h.update(str(py_file.relative_to(directory)).encode())
        h.update(py_file.read_bytes())
    return h.digest()


def compute_shared_spec_hash(ethereum_root: Path) -> bytes:
    """
    Hash all shared spec modules (everything in src/ethereum/ except forks/).

    Return raw SHA-256 digest bytes.
    """
    h = hashlib.sha256()
    for py_file in sorted(ethereum_root.rglob("*.py")):
        rel = py_file.relative_to(ethereum_root)
        if rel.parts and rel.parts[0] == "forks":
            continue
        h.update(str(rel).encode())
        h.update(py_file.read_bytes())
    return h.digest()


def compute_fork_spec_hash(
    fork_name: str,
    ethereum_root: Path,
    shared_hash: bytes,
) -> str:
    """
    Compute a spec hash for a given fork.

    Combine the shared modules hash with the fork-specific directory hash.
    Return a hex string (truncated to 16 chars for directory names).
    """
    module_name = fork_name_to_module(fork_name)
    fork_dir = ethereum_root / "forks" / module_name
    h = hashlib.sha256()
    h.update(shared_hash)
    if fork_dir.is_dir():
        h.update(hash_files(fork_dir))
    return h.hexdigest()[:16]


def compute_content_hash(
    request_data: TransitionToolRequest,
    state_test: bool,
) -> str:
    """
    Compute a content hash for a t8n call.

    Hash the context (fork, chain_id, reward), alloc, env, txs,
    and blob_params. Uses raw alloc representations when available
    to avoid expensive model_dump() calls.
    """
    h = hashlib.sha256()

    def feed(data: bytes) -> None:
        """Update hash with length-prefixed data to prevent collisions."""
        h.update(len(data).to_bytes(4, "big"))
        h.update(data)

    def feed_json_sorted(obj: Any) -> None:
        """Serialize to sorted JSON then feed to hash."""
        feed(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode())

    # State context (fork, chain_id, reward) — fixed fields, no dicts
    feed(request_data.state.model_dump_json(**model_dump_config).encode())
    # Alloc: use pre-computed state_root for LazyAlloc (free),
    # fall back to sorted serialization for genesis Alloc (block 0).
    alloc = request_data.input.alloc
    if isinstance(alloc, (LazyAllocStr, LazyAllocJson)):
        feed(bytes(alloc.state_root()))
    else:
        assert hasattr(alloc, "model_dump")
        feed_json_sorted(alloc.model_dump(mode="json", **model_dump_config))
    # Env — contains dict fields (blockHashes), must sort keys
    feed_json_sorted(
        request_data.input.env.model_dump(mode="json", **model_dump_config)
    )
    # Txs — fixed fields per tx, but sort for safety
    for tx in request_data.input.txs:
        feed_json_sorted(tx.model_dump(mode="json", **model_dump_config))
    # Blob params
    if request_data.input.blob_params is not None:
        feed_json_sorted(
            request_data.input.blob_params.model_dump(
                mode="json", **model_dump_config
            )
        )
    feed(b"\x01" if state_test else b"\x00")
    return h.hexdigest()


def serialize_output(output: TransitionToolOutput) -> bytes:
    """
    Serialize a TransitionToolOutput to pickle bytes.

    Build a plain dict of strings/dicts (no Pydantic models) then pickle
    it. This is portable across Python versions since we only pickle
    primitive types.
    """
    if isinstance(output.alloc, LazyAllocStr):
        alloc_str = output.alloc.raw
    elif isinstance(output.alloc, LazyAllocJson):
        alloc_str = json.dumps(
            output.alloc.raw, sort_keys=True, separators=(",", ":")
        )
    else:
        alloc_str = output.alloc.get().model_dump_json(**model_dump_config)

    data = {
        "alloc": alloc_str,
        "result": output.result.model_dump(mode="json", **model_dump_config),
        "body": output.body.hex() if output.body else None,
    }
    return pickle.dumps(data, protocol=5)


def deserialize_output(
    data: Dict[str, Any],
    context: Any | None = None,
) -> TransitionToolOutput:
    """Deserialize a dict back to a TransitionToolOutput."""
    result = Result.model_validate(obj=data["result"], context=context)
    # alloc is always stored as a JSON string in serialize_output
    alloc = LazyAllocStr(raw=data["alloc"], _state_root=result.state_root)
    body = Bytes(bytes.fromhex(data["body"])) if data.get("body") else None
    return TransitionToolOutput(alloc=alloc, result=result, body=body)


SCHEMA = """
CREATE TABLE IF NOT EXISTS cache (
    spec_hash    TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    data         BLOB NOT NULL,
    PRIMARY KEY (spec_hash, content_hash)
) WITHOUT ROWID
"""


class DiskCache:
    """
    Content-addressed SQLite cache for t8n outputs.

    Cache entries are keyed by (spec_hash, content_hash) where:
    - spec_hash identifies the EELS source code version for a fork
    - content_hash identifies the specific t8n call inputs

    Uses WAL mode for safe concurrent access under xdist.
    Entries are pickle-serialized plain dicts (portable across
    Python versions).
    """

    def __init__(
        self,
        db_path: Path,
        exception_mapper_context: Any | None = None,
    ) -> None:
        """Initialize the disk cache."""
        self.db_path = db_path
        self.exception_mapper_context = exception_mapper_context
        self.spec_hashes: Dict[str, str] = {}
        self.shared_hash: bytes | None = None
        self.ethereum_root: Path | None = None
        self.hits = 0
        self.misses = 0
        self.connection: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        """Lazy connection initialization with WAL mode."""
        if self.connection is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(
                str(self.db_path),
                timeout=10.0,
                isolation_level=None,  # autocommit
            )
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.execute("PRAGMA cache_size=-2000")
            self.connection.execute("PRAGMA mmap_size=0")
            self.connection.execute(SCHEMA)
        return self.connection

    def close(self) -> None:
        """Close the database connection."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def set_ethereum_root(self, ethereum_root: Path) -> None:
        """
        Set the ethereum package root for spec hash computation.

        Compute the shared modules hash once upfront.
        """
        self.ethereum_root = ethereum_root
        self.shared_hash = compute_shared_spec_hash(ethereum_root)
        logger.debug(
            "Disk cache: computed shared spec hash from %s",
            ethereum_root,
        )

    def get_spec_hash(self, fork: Any) -> str:
        """
        Get the spec hash for a fork, computing it on first access.

        For transition forks (e.g. ShanghaiToCancunAtTime15k), hash
        both the source and target fork directories.
        """
        fork_name = fork.name()
        if fork_name not in self.spec_hashes:
            assert self.ethereum_root is not None
            assert self.shared_hash is not None
            h = hashlib.sha256()
            h.update(self.shared_hash)
            if hasattr(fork, "transitions_from"):
                from_name = fork.transitions_from().name()
                to_name = fork.transitions_to().name()
                from_dir = (
                    self.ethereum_root
                    / "forks"
                    / fork_name_to_module(from_name)
                )
                to_dir = (
                    self.ethereum_root / "forks" / fork_name_to_module(to_name)
                )
                if from_dir.is_dir():
                    h.update(hash_files(from_dir))
                if to_dir.is_dir():
                    h.update(hash_files(to_dir))
            else:
                fork_dir = (
                    self.ethereum_root
                    / "forks"
                    / fork_name_to_module(fork_name)
                )
                if fork_dir.is_dir():
                    h.update(hash_files(fork_dir))
            self.spec_hashes[fork_name] = h.hexdigest()[:16]
        return self.spec_hashes[fork_name]

    def lookup(
        self,
        fork: Any,
        request_data: TransitionToolRequest,
        state_test: bool,
    ) -> tuple[TransitionToolOutput | None, str, str]:
        """
        Look up a cached result by fork and t8n inputs.

        Return (result_or_none, spec_hash, content_hash). The caller
        passes spec_hash and content_hash back to store() on a miss.
        """
        spec_hash = self.get_spec_hash(fork)
        content_hash = compute_content_hash(request_data, state_test)
        return (
            self.get(spec_hash, content_hash),
            spec_hash,
            content_hash,
        )

    def store(
        self,
        spec_hash: str,
        content_hash: str,
        output: TransitionToolOutput,
    ) -> None:
        """Store a computed result in the disk cache."""
        self.set(spec_hash, content_hash, output)

    def get(
        self,
        spec_hash: str,
        content_hash: str,
    ) -> TransitionToolOutput | None:
        """
        Look up a cached t8n output.

        Return None on miss or if the cached data is corrupt.
        """
        try:
            row = self.conn.execute(
                "SELECT data FROM cache"
                " WHERE spec_hash = ? AND content_hash = ?",
                (spec_hash, content_hash),
            ).fetchone()
        except sqlite3.Error:
            logger.debug("Disk cache: DB read error", exc_info=True)
            self.misses += 1
            return None

        if row is None:
            self.misses += 1
            return None

        try:
            # Safe: local cache, not untrusted data
            data = pickle.loads(  # noqa: S301
                zlib.decompress(row[0])
            )
            result = deserialize_output(
                data, context=self.exception_mapper_context
            )
            self.hits += 1
            return result
        except (
            pickle.UnpicklingError,
            zlib.error,
            KeyError,
            ValueError,
            TypeError,
        ):
            logger.warning(
                "Disk cache: corrupt entry %s/%s, ignoring",
                spec_hash,
                content_hash,
            )
            self.misses += 1
            return None

    def set(
        self,
        spec_hash: str,
        content_hash: str,
        output: TransitionToolOutput,
    ) -> None:
        """
        Write a t8n output to the disk cache.

        Uses INSERT OR IGNORE for idempotent writes under xdist.
        """
        try:
            encoded = serialize_output(output)
            compressed = zlib.compress(encoded, level=1)
            self.conn.execute(
                "INSERT OR IGNORE INTO cache"
                " (spec_hash, content_hash, data)"
                " VALUES (?, ?, ?)",
                (spec_hash, content_hash, compressed),
            )
        except sqlite3.Error:
            logger.debug(
                "Disk cache: failed to write %s/%s",
                spec_hash,
                content_hash,
                exc_info=True,
            )
