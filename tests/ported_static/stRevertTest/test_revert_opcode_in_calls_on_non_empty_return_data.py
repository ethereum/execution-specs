"""
Verify that a reverting callee's return data replaces the empty return
data left by a previously failed call: each prober records the failed
call's result and RETURNDATASIZE, for CALL, CALLCODE, DELEGATECALL and a
nested CALL chain, with an ample and a starved transaction budget.

Ported from:
state_tests/stRevertTest/RevertOpcodeInCallsOnNonEmptyReturnDataFiller.json

@manually-enhanced: Do not overwrite. Sub-calls forward all gas and the
ample arm omits the gas limit (maxing the EIP-8037 reservoir), replacing
per-fork gas bumps; the starved budget derives from fork composites; all
addresses are dynamic and every contract is pinned in the post.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Fork,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Bytecode, Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

RESULT_SLOT = 0x0
RETURN_DATA_SIZE_SLOT = 0x2
NESTED_RESULT_SLOT = 0x4
NESTED_RETURN_DATA_SIZE_SLOT = 0x5
ENTRY_SLOT = 0xA
ENTRY_SLOT_INITIAL = 255
# A zero-gas grant: the prelude call must fail without touching the
# return data buffer.
FAILING_CALL_GAS = 0
# Gas left at the entry frame's call site in the starved arm: enough to
# start the call, too little for any frame to complete.
STARVE_MARGIN = 1_000


@pytest.mark.ported_from(
    [
        "state_tests/stRevertTest/RevertOpcodeInCallsOnNonEmptyReturnDataFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "call_op",
    [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, None],
    ids=["call", "callcode", "delegatecall", "nested_call"],
)
@pytest.mark.parametrize(
    "ample_gas",
    [True, False],
    ids=["ample", "starved"],
)
def test_revert_opcode_in_calls_on_non_empty_return_data(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_op: Op | None,
    ample_gas: bool,
) -> None:
    """A revert's return data is observed after a failed call."""
    # Reverts one byte of return data; the store before the REVERT is
    # undone and the code after it must never run.
    reverter = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0xC)
        + Op.REVERT(offset=0x0, size=0x1)
        + Op.SSTORE(key=0x3, value=0xD)
        + Op.STOP,
    )
    # Would return 64 bytes, but is only ever called with zero gas.
    returner = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0xC)
        + Op.RETURN(offset=0x0, size=0x40),
    )

    prelude = Op.POP(
        Op.CALL(gas=FAILING_CALL_GAS, address=returner, address_warm=False)
    )

    def prober_code(
        op: Op, callee: Address, result_slot: int, rds_slot: int
    ) -> Bytecode:
        """Call the callee and record its result and RETURNDATASIZE."""
        return (
            prelude
            + Op.SSTORE(key=result_slot, value=op(address=callee))
            + Op.SSTORE(key=rds_slot, value=Op.RETURNDATASIZE)
            + Op.STOP
        )

    prober_call = pre.deploy_contract(
        code=prober_code(Op.CALL, reverter, RESULT_SLOT, RETURN_DATA_SIZE_SLOT)
    )
    prober_callcode = pre.deploy_contract(
        code=prober_code(
            Op.CALLCODE, reverter, RESULT_SLOT, RETURN_DATA_SIZE_SLOT
        )
    )
    prober_delegatecall = pre.deploy_contract(
        code=prober_code(
            Op.DELEGATECALL, reverter, RESULT_SLOT, RETURN_DATA_SIZE_SLOT
        )
    )
    inner_prober = pre.deploy_contract(
        code=prober_code(
            Op.CALL,
            reverter,
            NESTED_RESULT_SLOT,
            NESTED_RETURN_DATA_SIZE_SLOT,
        )
    )
    prober_nested = pre.deploy_contract(
        code=prober_code(
            Op.CALL, inner_prober, RESULT_SLOT, RETURN_DATA_SIZE_SLOT
        )
    )

    big_call = Op.CALL(address=Op.CALLDATALOAD(offset=0x0), address_warm=False)
    entry = pre.deploy_contract(
        code=prelude + Op.SSTORE(key=ENTRY_SLOT, value=big_call) + Op.STOP,
        storage={ENTRY_SLOT: ENTRY_SLOT_INITIAL},
    )

    probers = {
        Op.CALL: prober_call,
        Op.CALLCODE: prober_callcode,
        Op.DELEGATECALL: prober_delegatecall,
        None: prober_nested,
    }
    prober = probers[call_op]
    data = Hash(prober, left_padding=True)

    sender = pre.fund_eoa()
    if ample_gas:
        tx = Transaction(sender=sender, to=entry, data=data)
    else:
        # The entry frame reaches its call with only STARVE_MARGIN left:
        # the prober cannot even pay its prelude, and the retained 1/64
        # cannot pass the EIP-2200 stipend check, so everything reverts.
        intrinsic = fork.transaction_intrinsic_cost_calculator()(
            calldata=data, return_cost_deducted_prior_execution=True
        )
        starved = (
            intrinsic
            + prelude.gas_cost(fork)
            + big_call.gas_cost(fork)
            + STARVE_MARGIN
        )
        forwarded = STARVE_MARGIN - STARVE_MARGIN // 64
        assert forwarded < prelude.gas_cost(fork), "prober must starve"
        assert STARVE_MARGIN // 64 <= 2300, "entry store must halt"
        tx = Transaction(sender=sender, to=entry, data=data, gas_limit=starved)

    untouched = {
        reverter: Account(storage={}),
        prober_call: Account(storage={}),
        prober_callcode: Account(storage={}),
        prober_delegatecall: Account(storage={}),
        inner_prober: Account(storage={}),
        prober_nested: Account(storage={}),
    }
    if not ample_gas:
        # The transaction runs out of gas at the entry frame: everything
        # reverts.
        post = {
            **untouched,
            entry: Account(storage={ENTRY_SLOT: ENTRY_SLOT_INITIAL}),
        }
    elif call_op is None:
        # The nested prober's callee completes (its own probe fails), so
        # the outer call succeeds and returns no data.
        post = {
            **untouched,
            entry: Account(storage={ENTRY_SLOT: 1}),
            prober_nested: Account(storage={RESULT_SLOT: 1}),
            inner_prober: Account(storage={NESTED_RETURN_DATA_SIZE_SLOT: 1}),
        }
    else:
        # The probed call reverts with one byte of return data: result 0,
        # RETURNDATASIZE 1.
        post = {
            **untouched,
            entry: Account(storage={ENTRY_SLOT: 1}),
            prober: Account(storage={RETURN_DATA_SIZE_SLOT: 1}),
        }

    state_test(pre=pre, post=post, tx=tx)
