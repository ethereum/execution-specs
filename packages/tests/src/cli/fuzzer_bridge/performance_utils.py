"""Performance utilities for fuzzer bridge processing."""

import json
import mmap
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import orjson  # type: ignore  # Fast JSON library (optional dependency)

    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False


class FastJSONHandler:
    """Fast JSON operations using memory-mapped files and optimized parsing."""

    @staticmethod
    def load_json_mmap(file_path: Path) -> Dict[str, Any]:
        """Load JSON using memory-mapped file for better I/O performance."""
        with open(file_path, "r+b") as f:
            # Memory-map the file
            with mmap.mmap(
                f.fileno(), 0, access=mmap.ACCESS_READ
            ) as mmapped_file:
                # Read the entire content at once
                content = mmapped_file.read()
                if HAS_ORJSON:
                    return orjson.loads(content)
                else:
                    # Fallback to standard json
                    return json.loads(content.decode("utf-8"))

    @staticmethod
    def dump_json_fast(
        data: Dict[str, Any], file_path: Path, pretty: bool = False
    ) -> None:
        """Dump JSON using optimized serialization."""
        if HAS_ORJSON:
            # Use orjson for faster serialization
            if pretty:
                content = orjson.dumps(data, option=orjson.OPT_INDENT_2)
            else:
                content = orjson.dumps(data)
            with open(file_path, "wb") as f:
                f.write(content)
        else:
            # Fallback to standard json
            with open(file_path, "w") as f:
                if pretty:
                    json.dump(data, f, indent=2)
                else:
                    json.dump(data, f)


class BatchProcessor:
    """Optimized batch processing utilities."""

    @staticmethod
    def calculate_optimal_batch_size(file_count: int, num_workers: int) -> int:
        """Calculate optimal batch size based on file count and workers."""
        # Aim for at least 4 batches per worker for better load balancing
        # But not too small to avoid overhead
        min_batch_size = 5
        ideal_batches_per_worker = 4

        ideal_batch_size = max(
            min_batch_size,
            file_count // (num_workers * ideal_batches_per_worker),
        )

        # Adjust for very large file counts
        if file_count > 10000:
            # Larger batches for many files to reduce overhead
            ideal_batch_size = max(50, ideal_batch_size)
        elif file_count < 100:
            # Smaller batches for few files to maximize parallelism
            ideal_batch_size = max(1, file_count // (num_workers * 2))

        return ideal_batch_size

    @staticmethod
    def calculate_optimal_workers(file_count: int) -> int:
        """Calculate optimal number of workers for processing."""
        cpu_count = os.cpu_count() or 4

        # Scale workers based on file count
        if file_count < 10:
            return 1  # Sequential for very small workloads
        elif file_count < 50:
            return min(2, cpu_count)
        elif file_count < 200:
            return min(4, cpu_count)
        elif file_count < 1000:
            return min(cpu_count, 8)
        else:
            # For large file counts, use all available CPUs but cap at 16
            return min(cpu_count, 16)


@lru_cache(maxsize=128)
def cached_fork_lookup(fork_name: str) -> Optional[Any]:
    """Cache fork lookups to avoid repeated module imports."""
    try:
        import ethereum_test_forks

        return getattr(ethereum_test_forks, fork_name, None)
    except (ImportError, AttributeError):
        return None


class ParallelProgressTracker:
    """Thread-safe progress tracking for parallel processing."""

    def __init__(self, total: int):
        """Initialize progress tracker."""
        from threading import Lock

        self.total = total
        self.completed = 0
        self.errors = 0
        self.lock = Lock()

    def update(self, success: int = 0, error: int = 0) -> tuple[int, int]:
        """Update progress counters thread-safely."""
        with self.lock:
            self.completed += success
            self.errors += error
            return self.completed, self.errors

    def get_stats(self) -> tuple[int, int, int]:
        """Get current statistics."""
        with self.lock:
            return self.completed, self.errors, self.total


# Memory pool for reusing buffers
class BufferPool:
    """Reusable buffer pool to reduce memory allocations."""

    def __init__(self, buffer_size: int = 1024 * 1024):  # 1MB default
        """Initialize buffer pool."""
        self.buffer_size = buffer_size
        self.buffers: List[bytearray] = []

    def get_buffer(self) -> bytearray:
        """Get a buffer from pool or create new one."""
        if self.buffers:
            return self.buffers.pop()
        return bytearray(self.buffer_size)

    def return_buffer(self, buffer: bytearray) -> None:
        """Return buffer to pool for reuse."""
        if len(buffer) == self.buffer_size:
            self.buffers.append(buffer)
