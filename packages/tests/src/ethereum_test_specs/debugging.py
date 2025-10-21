"""Test spec debugging tools."""

from typing import List

from ethereum_clis import Traces


def print_traces(traces: List[Traces] | None) -> None:
    """Print the traces from the transition tool for debugging."""
    if traces is None:
        print(
            "Traces not collected. Use `--traces` to see detailed execution information."
        )
        return
    print("Printing traces for debugging purposes:")
    for block_number, block in enumerate(traces):
        print(f"Block {block_number}:")
        block.print()
