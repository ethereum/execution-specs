"""
Run every vector on both sides and collect the verdicts.

The specification's answer is produced here rather than by the tool's
own entry point, because each case needs a fresh pre-state: the driver
advances the state in place across blocks, which is exactly right within
one request and exactly wrong between two.
"""

from typing import Any, Dict, List, Optional

from ethereum_spec_tools.evm_tools.simulate import EthSimulate
from ethereum_spec_tools.evm_tools.simulate.context import (
    resolve_simulate_fork,
)
from ethereum_spec_tools.evm_tools.simulate.errors import SimulateError
from ethereum_spec_tools.evm_tools.simulate.payload import SimulatePayload

from .cases import CASES, Case
from .client import SimulateClient
from .compare import Comparison, compare_envelopes
from .genesis import CHAIN_ID, FORK_NAME, base_block, genesis_state

INTERNAL_ERROR_CODE = -32603
"""What an unhandled spec exception is reported as."""


def derive(case: Case) -> Dict[str, Any]:
    """
    Answer one case from the specification, as a JSON-RPC envelope.

    An exception the error table knows about becomes the code it names;
    anything else becomes an internal error, which is a difference the
    comparison will report rather than something to swallow.
    """
    simulator = EthSimulate(
        fork=resolve_simulate_fork(FORK_NAME),
        chain_id=CHAIN_ID,
        state=genesis_state(),
        base_block=base_block(),
        payload=SimulatePayload.parse(case.payload),
    )
    try:
        return {"jsonrpc": "2.0", "id": 1, "result": simulator.result()}
    except SimulateError as failure:
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": failure.code, "message": failure.message},
        }
    except Exception as failure:  # noqa: BLE001
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": INTERNAL_ERROR_CODE,
                "message": f"{type(failure).__name__}: {failure}",
            },
        }


def compare_case(case: Case, client: SimulateClient) -> Comparison:
    """Run one case on both sides and return the verdict."""
    ours = derive(case)
    theirs = client.simulate(case.payload, case.reference)
    return compare_envelopes(case.name, ours, theirs)


def run_all(
    client: SimulateClient, cases: Optional[List[Case]] = None
) -> List[Comparison]:
    """Run every case and return one verdict each."""
    return [compare_case(case, client) for case in (cases or list(CASES))]


def summarize(comparisons: List[Comparison]) -> str:
    """Render the verdicts as the table the assessment reports."""
    matched = sum(1 for entry in comparisons if entry.matches)
    lines = [f"{matched} of {len(comparisons)} cases match", ""]
    for entry in comparisons:
        verdict = "match" if entry.matches else "differs"
        lines.append(f"  {entry.name}: {verdict}")
        for difference in entry.differences[:8]:
            lines.append(f"      {difference}")
        if len(entry.differences) > 8:
            remaining = len(entry.differences) - 8
            lines.append(f"      ... and {remaining} more")
    return "\n".join(lines)
