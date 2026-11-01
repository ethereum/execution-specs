"""
Measurement instrument for invariant classes 13/14/15 (settlement).

NOT a corpus test. This conftest wraps two functions with *logging only*
side effects, so every settlement quantity a transaction produces can be
read off directly instead of guessed:

  * `ethereum.forks.amsterdam.fork.settle_transaction_gas`
      -- the pre-clamp `state_gas_used`, the refund, the floor, and both
         settled figures. This is the only way to observe whether
         `max(0, state_gas_used)` ever has anything to clamp.
  * `execution_testing.evm_tools.t8n.build_result`
      -- the three block counters and the receipts, on EVERY fork, since
         pre-Amsterdam forks settle inline in `fork.py` and have no
         wrappable settlement function.

`fill` runs t8n in-process, so patching the importing module's namespace
reaches the code that actually executes. Nothing in the EELS tree is
edited, so this instrument never contends with `tools/mutate.py`.

Output: one JSON object per line at `$SETTLEMENT_PROBE_LOG`.

**The instrument is inert unless `SETTLEMENT_PROBE_LOG` is set.** Other
contributors run `fill` over the whole `tests/tools/` tree, and a
conftest that patched unconditionally would attach to their runs and
write a file they never asked for.
"""

import json
import os
from pathlib import Path

_LOG_PATH = os.environ.get("SETTLEMENT_PROBE_LOG")
LOG = Path(_LOG_PATH) if _LOG_PATH else None


def _emit(record: dict) -> None:
    assert LOG is not None
    with LOG.open("a") as fh:
        fh.write(json.dumps(record, default=str) + "\n")


def _patch_settlement() -> None:
    """Log every argument and result of Amsterdam's settlement."""
    from ethereum.forks.amsterdam import fork as am_fork

    original = am_fork.settle_transaction_gas
    if getattr(original, "_probe_wrapped", False):
        return

    def wrapper(
        tx_gas, calldata_floor, gas_left, state_gas_left, refund_counter, state_gas_used
    ):  # noqa: ANN001, ANN202
        out = original(
            tx_gas,
            calldata_floor,
            gas_left,
            state_gas_left,
            refund_counter,
            state_gas_used,
        )
        before = int(tx_gas) - int(gas_left) - int(state_gas_left)
        _emit(
            {
                "kind": "settle",
                "tx_gas": int(tx_gas),
                "calldata_floor": int(calldata_floor),
                "gas_left_returned": int(gas_left),
                "state_gas_left_returned": int(state_gas_left),
                "refund_counter": int(refund_counter),
                # The pre-clamp value. Negative here is the ONLY thing
                # `max(0, state_gas_used)` can act on.
                "state_gas_used_raw": int(state_gas_used),
                "gas_used_before_refund": before,
                "gas_refund": min(before // 5, int(refund_counter)),
                "settled_gas_used": int(out.gas_used),
                "settled_execution_gas_used": int(out.execution_gas_used),
                "settled_state_gas_used": int(out.state_gas_used),
            }
        )
        return out

    wrapper._probe_wrapped = True  # type: ignore[attr-defined]
    am_fork.settle_transaction_gas = wrapper


def _patch_build_result() -> None:
    """Log the three block counters and the receipts, on every fork."""
    from execution_testing.evm_tools import t8n as t8n_mod

    original = t8n_mod.build_result
    if getattr(original, "_probe_wrapped", False):
        return

    def wrapper(t8n, block_env, block_output, *args, **kwargs):  # noqa: ANN001, ANN202
        out = original(t8n, block_env, block_output, *args, **kwargs)
        _emit(
            {
                "kind": "block",
                "fork": str(getattr(t8n.fork, "__name__", t8n.fork)),
                # Amsterdam: execution gas only, pre-refund (EIP-7778).
                # Pre-Amsterdam: the post-refund total.
                "block_gas_used": int(getattr(block_output, "block_gas_used", -1)),
                "block_state_gas_used": int(
                    getattr(block_output, "block_state_gas_used", -1)
                ),
                # Amsterdam only: the sender-facing counter the receipts use.
                "cumulative_gas_used": int(
                    getattr(block_output, "cumulative_gas_used", -1)
                ),
                # What the header carries, and what header_verify checks.
                "header_gas_used": int(out.gas_used),
                "receipt_cumulative_gas_used": [
                    int(r.cumulative_gas_used) for r in (out.receipts or [])
                ],
            }
        )
        return out

    wrapper._probe_wrapped = True  # type: ignore[attr-defined]
    t8n_mod.build_result = wrapper


if LOG is not None:
    _patch_settlement()
    _patch_build_result()


def pytest_runtest_logstart(nodeid, location):  # noqa: ANN001, ANN201, D103
    if LOG is not None:
        _emit({"kind": "test", "nodeid": nodeid})
