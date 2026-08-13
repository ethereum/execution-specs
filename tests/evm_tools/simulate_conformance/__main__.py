"""
Run the comparison and print the table, outside pytest.

`python -m tests.evm_tools.simulate_conformance` starts the client, runs
every vector and reports the count, which is the form the result is
quoted in. The pytest tier asserts the same thing; this exists so the
number can be re-established without reading a test failure.
"""

import sys

from .cases import CASES
from .client import ClientUnavailableError, client_version, running_client
from .runner import run_all, summarize


def main() -> int:
    """Run every vector against the client and report."""
    try:
        with running_client() as client:
            comparisons = run_all(client)
    except ClientUnavailableError as unavailable:
        print(f"client unavailable: {unavailable}", file=sys.stderr)
        return 2

    print(f"client: {client_version()}")
    print(summarize(comparisons))
    contested = {case.name for case in CASES if case.contested}
    unexpected = [
        entry.name
        for entry in comparisons
        if not entry.matches and entry.name not in contested
    ]
    stale = [
        entry.name
        for entry in comparisons
        if entry.matches and entry.name in contested
    ]
    if unexpected:
        print(f"\nunexpected differences: {', '.join(unexpected)}")
    if stale:
        print(f"\ncases that no longer differ: {', '.join(stale)}")
    return 1 if unexpected or stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
