"""
Opcode-trace output for ``fill-stateful --trace-opcodes``.

Serialise the per-test opcode counts collected by ``ClientBackend``
(via ``debug_traceBlockByNumber`` with the unigram tracer) into a JSON
file mapping test names to opcode counts, matching the format produced
by gas-benchmarks' ``eest_stateful_generator.py --trace-json``::

    {
      "test_single_opcode.py__test_sload[fork_Amsterdam-...]": {
        "PUSH1": 55674,
        "SLOAD": 11132
      }
    }
"""

import json
from pathlib import Path
from typing import Dict

from execution_testing.client_clis.cli_types import OpcodeCount

# ``OpcodeCount`` canonicalizes client-reported opcode names through the
# ``Opcodes`` enum (geth's ``KECCAK256`` becomes ``SHA3``); map back to
# the geth-style name so the output matches gas-benchmarks' trace files.
_OPCODE_OUTPUT_NAMES = {"SHA3": "KECCAK256"}


def node_id_to_test_key(node_id: str) -> str:
    """
    Convert a pytest node id to a gas-benchmarks-compatible test key.

    ``tests/benchmark/test_single_opcode.py::test_sload[params]`` becomes
    ``test_single_opcode.py__test_sload[params]``: the module path is
    reduced to its basename and ``::`` separators become ``__``, mirroring
    the payload file names gas-benchmarks derives its keys from.
    """
    module_path, sep, test_part = node_id.partition("::")
    if not sep:
        return node_id
    module_name = module_path.rpartition("/")[2]
    return f"{module_name}__{test_part.replace('::', '__')}"


def write_opcode_trace_file(
    path: Path, collected: Dict[str, OpcodeCount]
) -> None:
    """
    Write collected per-test opcode counts to ``path`` as JSON.

    ``collected`` is keyed by pytest node id; keys are converted via
    ``node_id_to_test_key``. Keys that collide after the module path is
    flattened get an ``__<n>`` suffix, as in gas-benchmarks.
    """
    results: Dict[str, Dict[str, int]] = {}
    for node_id, opcode_count in collected.items():
        key = node_id_to_test_key(node_id)
        if key in results:
            duplicate_idx = 1
            while f"{key}__{duplicate_idx}" in results:
                duplicate_idx += 1
            key = f"{key}__{duplicate_idx}"
        results[key] = {
            _OPCODE_OUTPUT_NAMES.get(str(opcode), str(opcode)): count
            for opcode, count in opcode_count.root.items()
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
