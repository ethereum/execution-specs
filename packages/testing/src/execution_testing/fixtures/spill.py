"""
Disk-backed payload lists for fixtures too large to hold in memory.

A spilled payload is one line of canonical JSON (the exact form
BaseFixture.hash digests), so readers splice it back without re-encoding.
Peak memory is the largest single payload.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import IO, Any, Dict, Iterator, List

__all__ = ["PayloadBuffer", "DEFAULT_SPILL_THRESHOLD", "canonical_json"]

# Payloads held in memory before moving to disk. Chosen so every ordinary
# fill stays on the in-memory path and keeps its previous behaviour.
DEFAULT_SPILL_THRESHOLD = 512


def canonical_json(value: Any) -> str:
    """Render `value` in the form the fixture hash digests."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _canonical(payload: Any) -> str:
    """Render one payload, dumping a model down to plain types first."""
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump(
            mode="json", by_alias=True, exclude_none=True
        )
    return canonical_json(payload)


class PayloadBuffer:
    """
    An append-only payload list that moves to disk when it grows large.

    Buffered it hands back the payloads themselves; spilled, canonical
    JSON text one payload at a time.
    """

    def __init__(
        self,
        prefix: str = "fixture-payloads-",
        threshold: int = DEFAULT_SPILL_THRESHOLD,
    ) -> None:
        """Start buffered; no file is created unless the fill outgrows it."""
        self._prefix = prefix
        self._threshold = threshold
        self._buffer: List[Any] = []
        self._file: IO[str] | None = None
        self._path: Path | None = None
        self._count = 0

    @property
    def spilled(self) -> bool:
        """True once the payloads moved to disk."""
        return self._file is not None

    @property
    def buffered(self) -> List[Any]:
        """The payloads held in memory. Empty once spilled."""
        return self._buffer

    def append(self, payload: Any) -> None:
        """Add one payload, moving to disk if the threshold is passed."""
        self._count += 1
        if self._file is None:
            self._buffer.append(payload)
            if len(self._buffer) > self._threshold:
                self._start_spilling()
            return
        self._write(payload)

    def _start_spilling(self) -> None:
        """Move what is buffered to a temp file and drop the models."""
        fd, name = tempfile.mkstemp(prefix=self._prefix, suffix=".jsonl")
        self._path = Path(name)
        self._file = os.fdopen(fd, "w+")
        for payload in self._buffer:
            self._write(payload)
        self._buffer = []

    def _write(self, payload: Any) -> None:
        """Append one payload's canonical JSON to the temp file."""
        assert self._file is not None
        self._file.write(_canonical(payload) + "\n")

    def __len__(self) -> int:
        """Number of payloads appended."""
        return self._count

    def iter_canonical(self) -> Iterator[str]:
        """Yield each payload as canonical JSON text, in order."""
        if self._file is None:
            for payload in self._buffer:
                yield _canonical(payload)
            return
        self._file.flush()
        self._file.seek(0)
        for line in self._file:
            yield line.rstrip("\n")

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Yield each payload as a decoded dict, one at a time."""
        for line in self.iter_canonical():
            yield json.loads(line)

    def close(self) -> None:
        """Close and remove the temp file, if one was opened."""
        if self._file is not None:
            self._file.close()
            self._file = None
        if self._path is not None:
            self._path.unlink(missing_ok=True)
            self._path = None
