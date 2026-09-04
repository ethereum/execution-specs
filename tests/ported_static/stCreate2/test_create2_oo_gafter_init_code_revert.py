"""
Verify a CREATE2 whose child completes its init code but runs out of gas
at the code-deposit charge, inside a frame that then REVERTs: the revert
payload carries the CREATE2 result (zero) back to the caller and every
side effect of the creating frame is rolled back.

Ported from:
state_tests/stCreate2/Create2OOGafterInitCodeRevert2Filler.json

@manually-enhanced: Do not overwrite. Joins the Revert and Revert2
fillers: they are one scenario differing only in whether the child can
afford its code deposit, so the grant is parametrized. The ported Revert
case stored only the payload's first word, which is identical in both
arms, so it could not tell a successful CREATE2 from a failed one.
The forwarded grant is derived from
fork composites so the child fails exactly at the deposit charge on every
fork. The revert payload now also carries the CREATE2 result, and the
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

# The init code returns this many memory bytes as the code to deposit.
# The grant is sized so this charge is exactly what the child cannot pay.
DEPOSIT_SIZE = 0x40


@pytest.mark.ported_from(
    [
        "state_tests/stCreate2/Create2OOGafterInitCodeRevertFiller.json",
        "state_tests/stCreate2/Create2OOGafterInitCodeRevert2Filler.json",
    ],
)
@pytest.mark.valid_from("Constantinople")
@pytest.mark.parametrize(
    "deposit_succeeds",
    [
        pytest.param(True, id="deposit_paid"),
        pytest.param(False, id="deposit_unaffordable"),
    ],
)
def test_create2_oo_gafter_init_code_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    deposit_succeeds: bool,
) -> None:
    """A CREATE2 inside a reverting frame, with and without deposit gas."""
    # The child's init code is a bare deposit request. Its metadata
    # carries the deposit charge, so `gas_cost` is what the child needs
    # to both run and deposit.
    initcode = Op.RETURN(
        offset=0x0,
        size=DEPOSIT_SIZE,
        new_memory_size=DEPOSIT_SIZE,
        code_deposit_size=DEPOSIT_SIZE,
    )
    # The same RETURN priced without the deposit: what the child must
    # afford to reach the deposit charge at all.
    initcode_run_only = Op.RETURN(
        offset=0x0,
        size=DEPOSIT_SIZE,
        new_memory_size=DEPOSIT_SIZE,
    )
    assert len(initcode) <= 0x20, "init code must fit one word"

    # The creator writes the init code into memory (right-aligned in the
    # first word), runs CREATE2, appends the CREATE2 result to memory and
    # reverts both words back to the caller.
    creator_setup = Op.MSTORE(
        offset=0x0,
        value=int.from_bytes(initcode, "big"),
        new_memory_size=0x20,
    )
    create2_code = Op.CREATE2(
        value=0x0,
        offset=0x20 - len(initcode),
        size=len(initcode),
        salt=0x0,
        new_memory_size=0x20,
        old_memory_size=0x20,
        init_code_size=len(initcode),
    )
    creator_tail = (
        Op.PUSH1[0x20]
        + Op.MSTORE(
            new_memory_size=0x40,
            old_memory_size=0x20,
        )
        + Op.REVERT(offset=0x0, size=0x40)
    )
    creator = pre.deploy_contract(
        code=creator_setup + create2_code + creator_tail
    )

    # Size the grant so the child's grant covers its init-code execution
    # but not the deposit charge, and the creator's 1/64 retention still
    # covers its tail (the result MSTORE and the REVERT).
    # The two arms differ by a single gas: enough to pay the deposit,
    # or one short of it.
    initcode_cost = initcode.gas_cost(fork)
    target_grant = initcode_cost - (0 if deposit_succeeds else 1)
    # What the creating frame still holds at the moment CREATE2 runs:
    # the child receives 63/64 of it and the creator keeps the rest, so
    # the pool has to be a 64th larger than the grant. Round down, since
    # one gas more would let the child afford the deposit after all.
    gas_at_create2 = target_grant * 64 // 63
    forwarded = (
        creator_setup.gas_cost(fork)
        + create2_code.gas_cost(fork)
        + gas_at_create2
    )

    granted = gas_at_create2 - gas_at_create2 // 64
    assert granted >= target_grant, "the child must receive its grant"
    if deposit_succeeds:
        assert granted >= initcode_cost, "the child must afford the deposit"
    else:
        # The child must reach the deposit and fail on it alone, not
        # earlier in its init code.
        assert initcode_run_only.gas_cost(fork) <= granted < initcode_cost, (
            "the child must die at the deposit charge, not before it"
        )
    assert gas_at_create2 // 64 >= creator_tail.gas_cost(fork), (
        "the creator's retention must cover its tail"
    )

    # The caller forwards the sized grant, then stores the call result
    # and both words of the revert payload. The two results are stored
    # as `1 + result`, so a zero result is distinguishable from a store
    # that never happened.
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

    child_address = compute_create2_address(creator, 0, initcode)
    post = {
        caller: Account(
            storage={
                # The creator reverted, so the call returned 0.
                CALL_RESULT_SLOT: 0x1,
                # First payload word: the init code the creator staged.
                PAYLOAD_SLOT: int.from_bytes(initcode, "big"),
                # Second payload word: the CREATE2 result, which is
                # the child's address when the deposit was paid and 0
                # when it was not. This is the only observable that
                # separates the two arms, since the revert rolls the
                # deposit back either way.
                CREATE2_RESULT_SLOT: 0x1
                + (
                    int.from_bytes(bytes(child_address), "big")
                    if deposit_succeeds
                    else 0x0
                ),
            }
        ),
        # Everything inside the creator was rolled back.
        creator: Account(nonce=1, storage={}),
        # The creator reverted, so the deposit never survives.
        child_address: Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
