"""
Build the docc spec docs as parallel shards of consecutive forks.

Fast PR-time validation only: the fork range is split into ``n``
contiguous shards, each overlapping its predecessor by one fork so a
fork's reference to the previous fork resolves within its shard. One
``docc`` process renders each shard concurrently; the per-shard outputs
are not merged.

Forward references (a fork referencing a later fork) fall outside their
shard and are pruned, so they are validated only by the serial
default-branch ``docs-spec`` build that gates the docs deploy.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List

from .forks import Hardfork


def compute_shards(forks: List[str], n: int) -> List[List[str]]:
    """
    Split ``forks`` into at most ``n`` contiguous shards.

    Every shard after the first is prefixed with its predecessor fork, so
    a fork's reference to the previous fork resolves within its shard.
    """
    per = (len(forks) + n - 1) // n
    shards: List[List[str]] = []
    for i in range(n):
        start = i * per
        if start >= len(forks):
            break
        lo = start - 1 if start > 0 else start
        shards.append(forks[lo : min(start + per, len(forks))])
    return shards


def main() -> int:
    """Discover forks, shard them, and render each shard with ``docc``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-n",
        "--shards",
        type=int,
        default=4,
        help="number of parallel shards (default: 4)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        required=True,
        help="parent directory for each shard's output",
    )
    args = parser.parse_args()
    if args.shards < 1:
        parser.error("--shards must be a positive integer")

    forks = [fork.short_name for fork in Hardfork.discover()]
    if not forks:
        print("error: no forks discovered", file=sys.stderr)
        return 1

    processes: List[subprocess.Popen[bytes]] = []
    for i, shard in enumerate(compute_shards(forks, args.shards)):
        print(f"shard {i}: {','.join(shard)}", flush=True)
        env = {
            **os.environ,
            "DOCC_SKIP_DIFFS": "1",
            "DOCC_ONLY_FORKS": ",".join(shard),
        }
        output = args.output_dir / f"shard-{i}"
        processes.append(
            subprocess.Popen(["docc", "--output", str(output)], env=env)
        )

    exit_codes = [process.wait() for process in processes]
    return 1 if any(exit_codes) else 0


if __name__ == "__main__":
    sys.exit(main())
