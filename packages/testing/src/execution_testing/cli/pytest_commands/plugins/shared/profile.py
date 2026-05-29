"""
Shared profile log for fill-stateful runs.

Appends one line per timed event to ``PROFILE_FILE`` and stderr. Uses a
plain file so output survives pytest's stdout/stderr capture without
requiring ``-s`` or ``--log-cli-level``.
"""

import contextlib
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Iterator

PROFILE_FILE: Path = Path("/tmp/fill-stateful-profile.log")


def start_session() -> None:
    """Truncate the profile file and write a session-start marker."""
    PROFILE_FILE.write_text("")
    write("session start", at=datetime.now().isoformat(timespec="seconds"))


def write(label: str, **fields: object) -> None:
    """Append a profile entry to the log file and stderr."""
    parts = [f"[profile] {label}"]
    for key, value in fields.items():
        parts.append(f"{key}={value}")
    line = "  ".join(parts)
    print(line, file=sys.stderr, flush=True)
    with PROFILE_FILE.open("a") as fh:
        fh.write(line + "\n")


@contextlib.contextmanager
def phase(label: str, **fields: object) -> Iterator[None]:
    """Time a phase. Log start, end, and elapsed seconds."""
    write(f"{label}: starting", **fields)
    t0 = time.perf_counter()
    try:
        yield
    finally:
        write(
            f"{label}: done",
            elapsed_s=f"{time.perf_counter() - t0:.3f}",
            **fields,
        )
