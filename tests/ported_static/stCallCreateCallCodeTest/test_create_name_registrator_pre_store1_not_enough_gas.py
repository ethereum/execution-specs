"""
Verify a nested CREATE of the name registrar whose child grant cannot cover
the init code: the child account never materializes, while the creating
frame completes (its nonce still advances).

Ported from:
state_tests/stCallCreateCallCodeTest/createNameRegistratorPreStore1NotEnoughGasFiller.json

@manually-enhanced: Do not overwrite. The registrar init code is composed
(not a hex blob) and the transaction budget is derived from the fork so
the child's 63/64 grant undercuts its cost on every fork; the creator's
balance is asserted (the endowment returns on failure).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_VALUE = 0x186A0
CREATE_VALUE = 0x17
INITIAL_BALANCE = 10**15
COPY_OFFSET = 0xC
DEPOSITED_SIZE = 0x10


@pytest.mark.ported_from(
    [
        "state_tests/stCallCreateCallCodeTest/createNameRegistratorPreStore1NotEnoughGasFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
def test_create_name_registrator_pre_store1_not_enough_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """A starved nested registrar creation leaves no account behind."""
    # The registrar init code (same as the per-txs sibling): write slot 1,
    # deposit 16 bytes of runtime copied from its own bytes.
    initcode = (
        Op.SSTORE(
            key=0x1, value=0x1, key_warm=False, original_value=0, new_value=1
        )
        + Op.PUSH1[DEPOSITED_SIZE]
        + Op.CODECOPY(
            dest_offset=0x0,
            offset=COPY_OFFSET,
            size=Op.DUP1,
            data_size=DEPOSITED_SIZE,
            new_memory_size=0x20,
        )
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.STOP
        + Op.JUMPI(
            pc=0x9,
            condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
        )
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(
            key=Op.CALLDATALOAD(offset=0x0),
            value=Op.CALLDATALOAD(offset=0x20),
        )
    )
    initcode_bytes = bytes(initcode)
    assert len(initcode_bytes) == 0x22, "ported init code is 34 bytes"

    # Memory setup derived from the composed bytes (one word plus two
    # trailing byte stores, as in the ported filler).
    setup = (
        Op.MSTORE(
            offset=0x0,
            value=int.from_bytes(initcode_bytes[:0x20], "big"),
            new_memory_size=0x20,
        )
        + Op.MSTORE8(
            offset=0x20, value=initcode_bytes[0x20], new_memory_size=0x40
        )
        + Op.MSTORE8(
            offset=0x21, value=initcode_bytes[0x21], new_memory_size=0x40
        )
    )
    create_code = Op.CREATE(
        value=CREATE_VALUE,
        offset=0x0,
        size=len(initcode_bytes),
        new_memory_size=0x40,
        old_memory_size=0x40,
        init_code_size=len(initcode_bytes),
    )
    creator = pre.deploy_contract(
        code=setup + Op.POP(create_code) + Op.STOP,
        balance=INITIAL_BALANCE,
    )

    # Budget: covers the frame's own work and the CREATE's peak charge,
    # but the child's 63/64 grant undercuts the init code plus deposit.
    child_needed = (
        initcode.gas_cost(fork)
        + DEPOSITED_SIZE * fork.gas_costs().CODE_DEPOSIT_PER_BYTE
        + fork.code_deposit_state_gas(code_size=DEPOSITED_SIZE)
    )
    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    gas_limit = (
        intrinsic
        + setup.gas_cost(fork)
        + create_code.gas_cost(fork)
        + child_needed // 2
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=creator,
        gas_limit=gas_limit,
        value=TX_VALUE,
    )

    post = {
        # The CREATE advanced the nonce even though its child failed, and
        # the endowment returned.
        creator: Account(nonce=2, balance=INITIAL_BALANCE + TX_VALUE),
        compute_create_address(address=creator, nonce=1): Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
