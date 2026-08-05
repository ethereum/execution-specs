"""
Verify a CREATE2 whose child completes its init code but runs out of gas
at the code-deposit charge, inside a frame that then REVERTs: the revert
payload carries the CREATE2 result (zero) back to the caller and every
side effect of the creating frame is rolled back.

Ported from:
state_tests/stCreate2/Create2OOGafterInitCodeRevert2Filler.json

@manually-enhanced: Do not overwrite. The forwarded grant is derived from
fork composites so the child fails exactly at the deposit charge on every
fork; the revert payload now also carries the CREATE2 result, and the
caller stores the call result plus both payload words.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create2_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

PAYLOAD_SLOT = 0x1
CREATE2_RESULT_SLOT = 0x2
CALL_RESULT_SLOT = 0x3

# The init code returns this many memory bytes as the code to deposit;
# the grant is sized so this charge is exactly what the child cannot pay.
DEPOSIT_SIZE = 0x40


@pytest.mark.ported_from(
    ["state_tests/stCreate2/Create2OOGafterInitCodeRevert2Filler.json"],
)
@pytest.mark.valid_from("Constantinople")
def test_create2_oo_gafter_init_code_revert2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """A CREATE2 child dies at the deposit charge; its creator reverts."""
    # The child's init code: one word of scratch data, then a deposit
    # request the sized grant cannot cover. The would-be deposited code
    # (an SSTORE) never runs.
    child_mstore = Op.MSTORE(
        offset=0x0,
        value=0x6001600155,
        new_memory_size=0x20,
    )
    child_return = Op.RETURN(
        offset=0x0,
        size=DEPOSIT_SIZE,
        new_memory_size=DEPOSIT_SIZE,
        old_memory_size=0x20,
    )
    initcode = child_mstore + child_return
    initcode_bytes = bytes(initcode)
    assert len(initcode_bytes) <= 0x20, "init code must fit one word"

    # The creator writes the init code into memory (right-aligned in the
    # first word), runs CREATE2, appends the CREATE2 result to memory and
    # reverts both words back to the caller.
    creator_setup = Op.MSTORE(
        offset=0x0,
        value=int.from_bytes(initcode_bytes, "big"),
        new_memory_size=0x20,
    )
    create2_code = Op.CREATE2(
        value=0x0,
        offset=0x20 - len(initcode_bytes),
        size=len(initcode_bytes),
        salt=0x0,
        new_memory_size=0x20,
        old_memory_size=0x20,
        init_code_size=len(initcode_bytes),
    )
    creator = pre.deploy_contract(
        code=creator_setup
        + Op.MSTORE(
            offset=0x20,
            value=create2_code,
            new_memory_size=0x40,
            old_memory_size=0x20,
        )
        + Op.REVERT(offset=0x0, size=0x40)
    )

    # Size the grant so the child's grant covers its init-code execution
    # but not the deposit charge, and the creator's 1/64 retention still
    # covers its tail (the result MSTORE and the REVERT).
    child_exec = child_mstore.gas_cost(fork) + child_return.gas_cost(fork)
    deposit_cost = DEPOSIT_SIZE * fork.gas_costs().CODE_DEPOSIT_PER_BYTE
    deposit_cost += fork.code_deposit_state_gas(code_size=DEPOSIT_SIZE)
    child_grant = child_exec + deposit_cost // 2
    rem_after_create = -(-child_grant * 64 // 63)
    forwarded = (
        creator_setup.gas_cost(fork)
        + create2_code.gas_cost(fork)
        + rem_after_create
    )
    granted = rem_after_create - rem_after_create // 64
    assert child_exec + 10 <= granted <= child_exec + deposit_cost - 10, (
        "the child grant must die exactly at the deposit charge"
    )
    creator_tail = Op.MSTORE(
        offset=0x20,
        value=0x0,
        new_memory_size=0x40,
        old_memory_size=0x20,
    ).gas_cost(fork) + Op.REVERT(offset=0x0, size=0x40).gas_cost(fork)
    assert rem_after_create // 64 >= creator_tail + 5, (
        "the creator's retention must cover its tail"
    )

    # The caller forwards the sized grant, then stores the call result
    # and both words of the revert payload.
    call_code = Op.CALL(gas=forwarded, address=creator, ret_size=0x40)
    caller = pre.deploy_contract(
        code=Op.SSTORE(key=CALL_RESULT_SLOT, value=Op.ADD(0x1, call_code))
        + Op.SSTORE(key=PAYLOAD_SLOT, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(
            key=CREATE2_RESULT_SLOT,
            value=Op.ADD(0x1, Op.MLOAD(offset=0x20)),
        )
        + Op.STOP,
        storage={PAYLOAD_SLOT: 0x1},
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        state_gas_reservoir=0,
    )

    post = {
        caller: Account(
            storage={
                # The creator reverted: the call result is 0.
                CALL_RESULT_SLOT: 0x1,
                # First payload word: the init code the creator staged.
                PAYLOAD_SLOT: int.from_bytes(initcode_bytes, "big"),
                # Second payload word: the failed CREATE2 returned 0.
                CREATE2_RESULT_SLOT: 0x1,
            }
        ),
        # Everything inside the creator was rolled back.
        creator: Account(nonce=1, storage={}),
        compute_create2_address(creator, 0, initcode): Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
