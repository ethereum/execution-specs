"""
Class #5: forwarding-prediction agreement.

A contract reimplements the forwarding formula in order to predict what
its callee will receive, then acts on the prediction. a deployed oracle network's CCIP
`CallWithExactGas` library is the canonical deployed instance; its
`_callWithExactGas` assembly block is

    g := gas()
    if lt(g, GAS_FOR_CALL_EXACT_CHECK) { revert(0, 0) }
    g := sub(g, GAS_FOR_CALL_EXACT_CHECK)
    if iszero(gt(sub(g, div(g, 64)), gasLimit)) { revert(0, 0) }
    success := call(gasLimit, target, 0,
                     add(payload, 0x20), mload(payload), 0, 0)

and it documents its own fragility in deployed source:

    uint16 internal constant GAS_FOR_CALL_EXACT_CHECK = 5_000;
    // so that we can redeploy to adjust it should a hardfork change
    // the gas costs of relevant opcodes in callWithExactGas

The 5,000 is not decoration. The pre-check is sound exactly when

    c <= GAS_FOR_CALL_EXACT_CHECK

where `c` is everything the frame spends between the `gas()` reading and
the moment the EVM computes the child's grant: the prediction arithmetic
itself, plus `extra_gas` (account access, value transfer, EIP-7702
delegation resolution) plus `memory_cost`
(`calculate_message_call_gas`, amsterdam/vm/gas.py:801-843). `extra_gas`
is not a constant -- it is composed per call shape -- so the same deployed
idiom is sound on one shape and unsound on another. This file parametrises
over shape for exactly that reason.

Two complementary assertions, sensitive in opposite directions:

  `..._honours_the_promised_limit` is the deployed shape. It fails when
  the retention fraction *tightens*, or when `extra_gas` or `memory_cost`
  *grows* past the deployed slack.

  `..._prediction_agrees_with_delivery` forwards everything, so the clamp
  binds, and compares the on-chain prediction against what the child
  actually observes. Its `not_over_delivered` marker is a *sign* test, so
  it fails on any *loosening* of the retention fraction -- including
  `63/64 -> 127/128`, which no other archetype in this corpus detects.

Every number quoted below was measured with
`tests/tools/test_cls5_prediction_probe.py`; the tables are in README.md.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Deployed constant, a deployed oracle network CCIP `CallWithExactGas`. A literal in
# immutable bytecode: it cannot be rebased by a fork, which is precisely
# what the comment next to it says.
GAS_FOR_CALL_EXACT_CHECK = 5_000

# The child's own prologue is a single `GAS` opcode, so the gas it reports
# is its grant minus 2. 64 bounds that with room to spare. This is a
# discriminator between "full delivery" and "short by a call's worth of
# overhead" -- measured shortfalls are 287..6,944 -- not an assertion
# about any opcode's cost.
FULL_DELIVERY_BOUND = 64

# Far above any clamp, so `min(requested, clamp)` always picks the clamp.
FORWARD_EVERYTHING = 2**32

# Large enough that a loosened retention fraction moves delivery by more
# than the deployed slack, and small enough to stay a plausible mainnet
# transaction. At 3,000,000 a `63/64 -> 127/128` change hands the child
# ~23,000 gas more than the contract predicted.
PARENT_GAS = 3_000_000

# Return-buffer offsets. `callWithExactGasSafeReturnData` takes a
# `maxReturnBytes` argument, so a return buffer is part of the deployed
# idiom; these particular sizes are the measured boundary rather than a
# witnessed configuration (see README.md).
RETBUF_4KB = 0x1000
RETBUF_16KB = 0x4000
RETBUF_NONE = 0x40

MEM_G = 0x00  # the `gas()` reading
MEM_PRED = 0x20  # the prediction / the promised gasLimit


def _reporter() -> Bytecode:
    """Child: report its own `GAS` on entry, before anything else."""
    return Op.MSTORE(0, Op.GAS) + Op.RETURN(0, 32)


def _precheck_caller(
    storage: Storage,
    target: Address,
    *,
    honoured: int,
    warm: bool = False,
    value: int = 0,
    retbuf: int = RETBUF_NONE,
) -> Bytecode:
    """
    Build the deployed `callWithExactGas` shape.

    `gasLimit` is computed on-chain as the largest value satisfying the
    deployed pre-check `(g - 5000) - (g - 5000)/64 > gasLimit`, so the
    caller sits exactly on the boundary the deployed contract permits
    itself to sit on -- which is where the invariant is load-bearing.
    """
    code = Bytecode()
    if warm:
        code += Op.POP(Op.EXTCODESIZE(target))
    code += Op.MSTORE(MEM_G, Op.GAS)
    code += Op.MSTORE(
        MEM_PRED, Op.SUB(Op.MLOAD(MEM_G), GAS_FOR_CALL_EXACT_CHECK)
    )
    code += Op.MSTORE(
        MEM_PRED,
        Op.SUB(Op.SUB(Op.MLOAD(MEM_PRED), Op.DIV(Op.MLOAD(MEM_PRED), 64)), 1),
    )
    code += Op.POP(
        Op.CALL(
            gas=Op.MLOAD(MEM_PRED),
            address=target,
            value=value,
            args_offset=0,
            args_size=0,
            ret_offset=retbuf,
            ret_size=32,
        )
    )
    # `gasLimit - reported` is 2 on full delivery. An over-delivery would
    # underflow to ~2**256 and also trip the bound, which is intended.
    code += Op.SSTORE(
        storage.store_next(honoured, "limit_honoured"),
        Op.ISZERO(
            Op.GT(
                Op.SUB(Op.MLOAD(MEM_PRED), Op.MLOAD(retbuf)),
                FULL_DELIVERY_BOUND,
            )
        ),
    )
    return code + Op.STOP


def _agreement_caller(
    storage: Storage,
    target: Address,
    *,
    within_slack: int,
    warm: bool = False,
    value: int = 0,
    retbuf: int = RETBUF_NONE,
) -> Bytecode:
    """Build a caller that forwards everything and checks its prediction."""
    code = Bytecode()
    if warm:
        code += Op.POP(Op.EXTCODESIZE(target))
    code += Op.MSTORE(MEM_G, Op.GAS)
    code += Op.MSTORE(
        MEM_PRED, Op.SUB(Op.MLOAD(MEM_G), Op.DIV(Op.MLOAD(MEM_G), 64))
    )
    code += Op.POP(
        Op.CALL(
            gas=FORWARD_EVERYTHING,
            address=target,
            value=value,
            args_offset=0,
            args_size=0,
            ret_offset=retbuf,
            ret_size=32,
        )
    )
    # The prediction is an upper bound on what the EVM hands over. A sign
    # test, so it fails on *any* loosening of the retention fraction once
    # the budget is large enough for the difference to show.
    code += Op.SSTORE(
        storage.store_next(1, "not_over_delivered"),
        Op.ISZERO(Op.GT(Op.MLOAD(retbuf), Op.MLOAD(MEM_PRED))),
    )
    # And it is an *accurate* upper bound only while the deployed slack
    # covers the call's own charges.
    code += Op.SSTORE(
        storage.store_next(within_slack, "within_deployed_slack"),
        Op.LT(
            Op.SUB(Op.MLOAD(MEM_PRED), Op.MLOAD(retbuf)),
            GAS_FOR_CALL_EXACT_CHECK,
        ),
    )
    return code + Op.STOP


def _fill(
    state_test: StateTestFiller,
    pre: Alloc,
    code: Bytecode,
    storage: Storage,
) -> None:
    caller = pre.deploy_contract(code, balance=10**18)
    tx = Transaction(
        to=caller,
        gas_limit=PARENT_GAS,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


# --------------------------------------------------------------------------
# The deployed pre-check: does the callee get the gasLimit it was promised?
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param({"warm": True}, id="warm_zero_value"),
        pytest.param({}, id="cold_zero_value"),
        pytest.param({"retbuf": RETBUF_4KB}, id="cold_retbuf_4kb"),
    ],
)
@pytest.mark.valid_from("Berlin")
def test_exact_gas_precheck_honours_the_promised_limit(
    state_test: StateTestFiller, pre: Alloc, kwargs: dict
) -> None:
    """
    Test the deployed pre-check guarantees the callee receives its limit.

    The caller promises `gasLimit` and the pre-check passes, so the callee
    must observe at least `gasLimit`. These are the call shapes
    `callWithExactGas` actually performs -- zero value, no delegation --
    and the deployed 5,000-gas slack covers them on every fork from Berlin
    to Amsterdam, the cold-access shape consuming the largest share of it
    (measured 3,019 of 5,000 at Amsterdam, 2,626 before it).

    A failure means a deployed contract that checks whether it can afford
    an exact-gas call now gets the wrong answer, and nothing reverts.
    """
    storage = Storage()
    target = pre.deploy_contract(_reporter())
    code = _precheck_caller(storage, target, honoured=1, **kwargs)
    _fill(state_test, pre, code, storage)


@pytest.mark.valid_from("Berlin")
def test_exact_gas_precheck_is_short_on_a_value_bearing_call(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test the same pre-check does *not* hold once the call carries value.

    `extra_gas` gains `CALL_VALUE`, which the slack cannot absorb, and the
    2,300 stipend only partly compensates. Measured shortfall: 4,287 gas
    on Berlin..Osaka and 6,944 at Amsterdam, where
    `CALL_VALUE = ACCOUNT_WRITE + CALL_STIPEND` folded the stipend into
    the charge (amsterdam/vm/gas.py:86).

    Pinned as a violation on purpose: `callWithExactGas` passes a literal
    `0` for value, so this records the boundary of the idiom's validity. A
    fork that made this pass would mean the forwarding budget had stopped
    charging for a value transfer.
    """
    storage = Storage()
    target = pre.deploy_contract(_reporter())
    code = _precheck_caller(storage, target, honoured=0, value=1)
    _fill(state_test, pre, code, storage)


@pytest.mark.valid_from("Prague")
def test_exact_gas_precheck_is_short_on_a_delegated_target(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test the pre-check does not hold when the target is an EIP-7702 EOA.

    Resolving the delegation adds a second cold account access to
    `extra_gas` (`calculate_delegation_cost`, charged before the child's
    grant is computed), and the deployed 5,000 does not cover two of them
    plus the prediction arithmetic. Measured shortfall: 287 gas on
    Prague/Osaka, growing to 1,074 at Amsterdam because EIP-8038 raised
    `COLD_ACCOUNT_ACCESS` from 2,600 to 3,000.

    So a deployed exact-gas forwarder silently under-delivers to any
    delegated recipient -- a call shape that did not exist when the 5,000
    was chosen.
    """
    impl = pre.deploy_contract(_reporter())
    target = pre.fund_eoa(delegation=impl)
    storage = Storage()
    code = _precheck_caller(storage, target, honoured=0)
    _fill(state_test, pre, code, storage)


@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Osaka")
def test_exact_gas_precheck_survives_a_16kb_return_buffer(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test a 16 KiB return buffer still fits the deployed slack, pre-8038.

    `memory_cost` is the third term the slack has to cover. Measured on
    Berlin..Osaka the 16 KiB buffer takes 4,638 of the 5,000, so the
    promised limit is still delivered in full -- with 362 gas of margin.

    The partner test below is the alarm: that margin is gone at Amsterdam.
    """
    storage = Storage()
    target = pre.deploy_contract(_reporter())
    code = _precheck_caller(storage, target, honoured=1, retbuf=RETBUF_16KB)
    _fill(state_test, pre, code, storage)


@pytest.mark.valid_from("EIP8037")
def test_exact_gas_precheck_is_short_on_a_16kb_return_buffer(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test the 16 KiB return buffer breaks the deployed slack from Amsterdam.

    EIP-8038 raised `COLD_ACCOUNT_ACCESS` 2,600 -> 3,000, adding 393 gas
    (`400 * 63/64`) to a cost that already stood at 4,638. The total
    crosses 5,000 and the callee is short by a measured 133 gas.

    **This is the first fork on which a deployed oracle network's own documented safety
    margin is insufficient for this shape**, and the pair of tests
    brackets it: the one above holds up to Osaka, this one from Amsterdam.
    If a later fork restores the headroom, this test fails and the one
    above starts applying again, which is the signal we want rather than
    silence.
    """
    storage = Storage()
    target = pre.deploy_contract(_reporter())
    code = _precheck_caller(storage, target, honoured=0, retbuf=RETBUF_16KB)
    _fill(state_test, pre, code, storage)


# --------------------------------------------------------------------------
# Prediction vs delivery, with the clamp binding
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param({"warm": True, "within_slack": 1}, id="warm_zero_value"),
        pytest.param({"within_slack": 1}, id="cold_zero_value"),
        pytest.param(
            {"retbuf": RETBUF_4KB, "within_slack": 1}, id="cold_retbuf_4kb"
        ),
        pytest.param({"value": 1, "within_slack": 0}, id="cold_with_value"),
    ],
)
@pytest.mark.valid_from("Berlin")
def test_forwarding_prediction_agrees_with_delivery(
    state_test: StateTestFiller, pre: Alloc, kwargs: dict
) -> None:
    """
    Test `g - g/64` bounds, and closely tracks, what the child receives.

    The caller forwards everything, so the 63/64 clamp binds and the
    child's grant is determined entirely by the retention fraction. Two
    markers:

    `not_over_delivered` -- the prediction is an upper bound on delivery.
    This is the marker that sees the retention fraction *loosen*: at a
    3,000,000-gas budget, `63/64 -> 127/128` hands the child ~23,000 gas
    more than the contract predicted and the sign flips.

    `within_deployed_slack` -- the prediction is accurate to within
    a deployed oracle network's 5,000. Measured gaps: 164 warm, 2,626/3,019 cold,
    3,029/3,423 with a 4 KiB buffer and 9,185/11,843 with value, the
    second figure of each pair being Amsterdam. Only the value-bearing
    shape exceeds the slack, so it is the one param expecting 0.
    """
    storage = Storage()
    target = pre.deploy_contract(_reporter())
    code = _agreement_caller(storage, target, **kwargs)
    _fill(state_test, pre, code, storage)


# STATE_BYTES_PER_STORAGE_SET(64) * COST_PER_STATE_BYTE(1530), i.e. one
# fresh storage slot's worth of EIP-8037 state gas.
ONE_SLOT_STATE_GAS = 97_920


@pytest.mark.valid_from("EIP8037")
def test_forwarding_prediction_ignores_the_state_gas_reservoir(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test the prediction still agrees when the caller holds a reservoir.

    `GAS` pushes `evm.gas_meter.gas_left` and nothing else, so it reports
    the execution-gas dimension alone and never the EIP-8037 state-gas
    reservoir. A forwarding predictor depends on that: only `gas_left`
    feeds `calculate_message_call_gas`, so a `GAS` reading that included
    the reservoir would inflate `g - g/64` by the whole reservoir and the
    pre-check would pass on gas the child can never receive.

    Same markers and the same measured gap (3,019 at Amsterdam) as the
    cold zero-value param above, with a reservoir of exactly one slot
    added. Note the transaction sets no explicit `gas_limit`: EIP-8037
    defines the reservoir as the part of `tx.gas` above
    `TX_MAX_GAS_LIMIT`, so passing both would silently yield a zero
    reservoir and test nothing.
    """
    storage = Storage()
    target = pre.deploy_contract(_reporter())
    code = _agreement_caller(storage, target, within_slack=1)
    caller = pre.deploy_contract(code, balance=10**18)
    tx = Transaction(
        to=caller,
        state_gas_reservoir=ONE_SLOT_STATE_GAS,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)
