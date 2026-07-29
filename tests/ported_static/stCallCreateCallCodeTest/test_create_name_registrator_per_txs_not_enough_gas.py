"""
Verify a name-registrator contract creation succeeds or fails with the
transaction budget: the init code writes a storage slot and deposits the
registrar's runtime code.

Ported from:
state_tests/stCallCreateCallCodeTest/createNameRegistratorPerTxsNotEnoughGasFiller.json

@manually-enhanced: Do not overwrite. Both budgets are derived from the
fork (intrinsic + top-frame state gas + init code execution + code deposit
regular and state costs); the success arm also pins the deposited code and
transferred balance, which the ported post never checked.
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

TX_VALUE = 100_000
COPY_OFFSET = 0xC
DEPOSITED_SIZE = 0x10


@pytest.mark.ported_from(
    [
        "state_tests/stCallCreateCallCodeTest/createNameRegistratorPerTxsNotEnoughGasFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "enough_gas",
    [
        pytest.param(False, id="g0"),
        pytest.param(True, id="g1"),
    ],
)
def test_create_name_registrator_per_txs_not_enough_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    enough_gas: bool,
) -> None:
    """An under-budgeted registrar creation leaves no account behind."""
    # The ported init code: write slot 1, then deposit 16 bytes of
    # registrar runtime copied from the init code's own bytes.
    store = Op.SSTORE(
        key=0x1, value=0x1, key_warm=False, original_value=0, new_value=1
    )
    initcode = (
        store
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
    deposited = bytes(initcode)[COPY_OFFSET : COPY_OFFSET + DEPOSITED_SIZE]

    # Fork-derived budgets: the sufficient one covers the init code, the
    # code deposit (regular and EIP-8037 state), and the created account's
    # top-frame state gas; the insufficient one dies mid-init-code.
    overhead = fork.transaction_intrinsic_cost_calculator()(
        calldata=initcode,
        contract_creation=True,
    ) + fork.transaction_top_frame_state_gas(contract_creation=True)
    execution_cost = (
        initcode.gas_cost(fork)
        + DEPOSITED_SIZE * fork.gas_costs().CODE_DEPOSIT_PER_BYTE
        + fork.code_deposit_state_gas(code_size=DEPOSITED_SIZE)
    )
    gas_limit = overhead + (
        execution_cost + 5_000 if enough_gas else execution_cost // 2
    )

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=gas_limit,
        value=TX_VALUE,
    )

    created = compute_create_address(address=sender, nonce=0)
    if enough_gas:
        created_account: Account | type = Account(
            nonce=1,
            code=deposited,
            balance=TX_VALUE,
            storage={1: 1},
        )
    else:
        created_account = Account.NONEXISTENT
    post = {
        sender: Account(nonce=1),
        created: created_account,
    }

    state_test(pre=pre, post=post, tx=tx)
