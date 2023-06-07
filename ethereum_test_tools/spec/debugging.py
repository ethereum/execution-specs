"""
Test spec debugging tools.
"""
import pprint
from typing import Dict, List


def print_traces(traces: List[List[List[Dict]]] | None):
    """
    Print the traces from the transition tool for debugging.
    """
    if traces is None:
        print("Traces not collected. Use `--traces` to see detailed" + " execution information.")
        return
    print("Printing traces for debugging purposes:")
    pp = pprint.PrettyPrinter(indent=2)
    for block_number, block in enumerate(traces):
        print(f"Block {block_number}:")
        for tx_number, tx in enumerate(block):
            print(f"Transaction {tx_number}:")
            for exec_step, trace in enumerate(tx):
                print(f"Step {exec_step}:")
                pp.pprint(trace)
                print()
