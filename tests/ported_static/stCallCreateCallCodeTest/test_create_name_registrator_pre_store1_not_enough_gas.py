"""
Verify a nested CREATE/CREATE2 of the name registrar at the exact boundary
of its EIP-150 grant: one gas either side decides whether the child account
materializes, while the creating frame completes regardless.

Ported from:
state_tests/stCallCreateCallCodeTest/createNameRegistratorPreStore1NotEnoughGasFiller.json
Legacy Test from Christoph. J.

@manually-enhanced: Do not overwrite. The registrar init code is composed
(not a hex blob), with the runtime a separate bytecode appended to it so
the executed cost never counts the payload, and the deposit riding on
RETURN's `code_deposit_size` metadata. The creator's frame gas is solved
for the exact 63/64 grant that covers the child, then stepped one grant
below it for the failing arm; the creator's balance is asserted (the
endowment returns on failure). Both create opcodes are covered, which the
boundary keeps honest: CREATE2 costs 15 gas more up front (hashing the
init code, plus the salt push) and the solved budget absorbs it.
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
from execution_testing.vm import Macros, Op, Opcodes

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_VALUE = 0x186A0
CREATE_VALUE = 0x17
INITIAL_BALANCE = 10**15
COPY_OFFSET = 18


@pytest.mark.ported_from(
    [
        "state_tests/stCallCreateCallCodeTest/createNameRegistratorPreStore1NotEnoughGasFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.with_all_create_opcodes
@pytest.mark.parametrize(
    "enough_gas",
    [
        pytest.param(False, id="insufficient_gas"),
        pytest.param(True, id="sufficient_gas"),
    ],
)
def test_create_name_registrator_pre_store1_not_enough_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Opcodes,
    enough_gas: bool,
) -> None:
    """A nested registrar creation at the exact edge of its EIP-150 grant."""
    # The registrar runtime, deployed by the init code below.
    deployed = (
        Op.JUMPI(
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
    deployed_size = len(deployed)
    # The registrar init code (same as the per-txs sibling): write slot 1,
    # then copy the runtime appended after it and return it for deposit.
    initcode = (
        Op.SSTORE(
            key=0x1, value=0x1, key_warm=False, original_value=0, new_value=1
        )
        + Op.CODECOPY(
            dest_offset=0x0,
            offset=COPY_OFFSET,
            size=deployed_size,
            data_size=deployed_size,
            new_memory_size=deployed_size,
        )
        + Op.RETURN(0, deployed_size, code_deposit_size=deployed_size)
        + Op.STOP
    )
    assert len(initcode) == COPY_OFFSET
    child_code = bytes(initcode + deployed)

    setup = Macros.MSTORE(child_code)
    create_code = create_opcode(
        value=CREATE_VALUE,
        offset=0x0,
        size=len(child_code),
        init_code_size=len(child_code),
    )
    creator = pre.deploy_contract(
        code=setup + Op.POP(create_code) + Op.STOP,
        balance=INITIAL_BALANCE,
    )

    # Solve for the creator frame's gas at the CREATE so its 63/64 grant
    # lands exactly on the child's cost; the failing arm steps down until
    # the grant really drops below it (the grant repeats every 64 gas).
    child_needed = initcode.gas_cost(fork)
    frame_gas = child_needed * 64 // 63
    while frame_gas - frame_gas // 64 < child_needed:
        frame_gas += 1
    if not enough_gas:
        while frame_gas - frame_gas // 64 >= child_needed:
            frame_gas -= 1

    gas_limit = (
        fork.transaction_intrinsic_cost_calculator()(
            sends_value=True,
            return_cost_deducted_prior_execution=True,
        )
        + setup.gas_cost(fork)
        + create_code.gas_cost(fork)
        + frame_gas
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=creator,
        gas_limit=gas_limit,
        value=TX_VALUE,
    )

    created = compute_create_address(
        address=creator,
        nonce=1,
        initcode=child_code,
        opcode=create_opcode,
    )
    if enough_gas:
        created_account: Account | None = Account(
            nonce=1,
            code=deployed,
            balance=CREATE_VALUE,
            storage={1: 1},
        )
        creator_balance = INITIAL_BALANCE + TX_VALUE - CREATE_VALUE
    else:
        # The endowment returns when the child fails.
        created_account = Account.NONEXISTENT
        creator_balance = INITIAL_BALANCE + TX_VALUE

    post = {
        # The CREATE advanced the nonce whether or not its child completed.
        creator: Account(nonce=2, balance=creator_balance),
        created: created_account,
    }

    state_test(pre=pre, post=post, tx=tx)
