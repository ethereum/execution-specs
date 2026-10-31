"""
Archetype 21: return-data pass-through fidelity (revert bubbling).

A proxy, router, or multicall copies a failed child's revert payload out and
re-reverts with it, so the original error reaches the caller's caller intact.
Every `try/catch` that inspects a custom error, every proxy that forwards a
revert reason, and every router that attributes a failure to a specific leg
depends on this.

L2 measured the shape at **723,118 distinct runtime code hashes across
4,755,135 addresses**, FP 0.0 — the **largest measured population in the
corpus**.

Two distinct rules hold it up, so there are two tests:

1. **Semantics.** `RETURNDATASIZE`/`RETURNDATACOPY` must expose the child's
   payload verbatim, and a `REVERT` of that buffer must propagate it
   unchanged. Nothing about gas is involved.
2. **Cost.** Bubbling is only possible if the bubbling frame can afford the
   memory expansion and the copy: `OPCODE_RETURNDATACOPY_PER_WORD = 3`
   (`vm/gas.py:235`) plus memory expansion at `MEMORY_PER_WORD = 3`
   (`vm/gas.py:94`) with a quadratic term. A large payload bubbled on a
   frozen budget is a real affordability cliff, and the failure is
   *silent degradation*: the outer frame sees an empty or truncated reason
   and misattributes the error.
"""

import pytest
from execution_testing import Account, Alloc, Op, StateTestFiller, Storage, Transaction

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# A distinctive payload head, so a truncated or zeroed bubble is detectable
# rather than looking like a legitimate empty revert.
MAGIC = 0xDEADBEEF

SLOT_HEAD = 0x01
SLOT_SIZE = 0x02


def _inner(pre: Alloc, payload_size: int) -> object:
    """A callee that reverts with MAGIC followed by zero padding."""
    return pre.deploy_contract(Op.MSTORE(0, MAGIC) + Op.REVERT(0, payload_size))


def _bubbler(pre: Alloc, inner: object, forwarded: object) -> object:
    """A proxy that re-reverts with the child's payload, verbatim."""
    return pre.deploy_contract(
        Op.POP(Op.CALL(gas=forwarded, address=inner))
        + Op.RETURNDATACOPY(0, 0, Op.RETURNDATASIZE)
        + Op.REVERT(0, Op.RETURNDATASIZE)
    )


def _observer(pre: Alloc, bubbler: object, storage: Storage, size: int) -> object:
    """The caller's caller: records what actually arrived."""
    return pre.deploy_contract(
        Op.POP(Op.CALL(gas=Op.GAS, address=bubbler))
        + Op.RETURNDATACOPY(0, 0, 32)
        + Op.SSTORE(storage.store_next(MAGIC, "payload_head"), Op.MLOAD(0))
        + Op.SSTORE(storage.store_next(size, "payload_size"), Op.RETURNDATASIZE)
        + Op.STOP
    )


@pytest.mark.parametrize(
    "payload_size",
    [
        pytest.param(32, id="one_word"),
        pytest.param(128, id="custom_error_with_args"),
        pytest.param(4096, id="large_reason_string"),
    ],
)
@pytest.mark.valid_from("Berlin")
def test_revert_payload_bubbles_verbatim(
    state_test: StateTestFiller,
    pre: Alloc,
    payload_size: int,
) -> None:
    """
    Test a revert payload survives two frames of bubbling unchanged.

    Both the head word and the exact size are asserted. Asserting only the
    size would miss a zeroed buffer; asserting only the head would miss a
    truncation. Gas is forwarded with `GAS` throughout, so this arm isolates
    the semantics from any affordability question.
    """
    inner = _inner(pre, payload_size)
    bubbler = _bubbler(pre, inner, Op.GAS)
    storage = Storage()
    observer = _observer(pre, bubbler, storage, payload_size)

    tx = Transaction(to=observer, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={observer: Account(storage=storage)}, tx=tx)


@pytest.mark.parametrize(
    "payload_size",
    [pytest.param(4096, id="large_reason_string")],
)
@pytest.mark.valid_from("Berlin")
def test_bubbling_a_large_payload_fits_a_frozen_budget(
    state_test: StateTestFiller,
    pre: Alloc,
    payload_size: int,
) -> None:
    """
    Test a proxy on a frozen budget can still bubble a large revert reason.

    The bubbling frame is given a hardcoded budget, as a deployed proxy's
    caller would, and must still afford the memory expansion and the copy for
    a 4 KiB reason. If a reprice pushes that past the budget, the proxy
    reverts with nothing and the observer misattributes the failure -- a
    silent degradation rather than an error.
    """
    inner = _inner(pre, payload_size)
    bubbler = _bubbler(pre, inner, Op.GAS)
    storage = Storage()
    observer = pre.deploy_contract(
        # Frozen operand, deliberately: see tests/frozen_budget/README.md.
        Op.POP(Op.CALL(gas=200_000, address=bubbler))
        + Op.RETURNDATACOPY(0, 0, 32)
        + Op.SSTORE(storage.store_next(MAGIC, "payload_head"), Op.MLOAD(0))
        + Op.SSTORE(storage.store_next(payload_size, "payload_size"),
                    Op.RETURNDATASIZE)
        + Op.STOP
    )
    tx = Transaction(to=observer, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={observer: Account(storage=storage)}, tx=tx)
