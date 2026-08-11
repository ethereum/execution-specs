"""
Verify a name-registrator contract creation succeeds or fails with the
transaction budget: the init code writes a storage slot and deposits the
registrar's runtime code.

Ported from:
state_tests/stCallCreateCallCodeTest/createNameRegistratorPerTxsNotEnoughGasFiller.json
Legacy Test from Christoph. J.

@manually-enhanced: Do not overwrite. The budget is an exact off-by-one
boundary derived from the fork: the sufficient arm gets intrinsic +
top-frame state gas + init code execution, the insufficient arm one gas
less. The deposit cost rides on RETURN's `code_deposit_size` metadata
rather than a hand-rolled per-byte constant, so it stays correct once
EIP-8037 moves most of it to state gas. The runtime code is a separate
bytecode appended to the init code instead of a slice of it, so the
executed cost no longer counts the payload. The success arm also pins
the deposited code and transferred balance, which the ported post never
checked.
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

COPY_OFFSET = 18


@pytest.mark.ported_from(
    [
        "state_tests/stCallCreateCallCodeTest/createNameRegistratorPerTxsNotEnoughGasFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "enough_gas",
    [
        pytest.param(False, id="insufficient_gas"),
        pytest.param(True, id="sufficient_gas"),
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non_zero_value"),
    ],
)
def test_create_name_registrator_per_txs_not_enough_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    enough_gas: bool,
    value: int,
) -> None:
    """An under-budgeted registrar creation leaves no account behind."""
    # The ported init code: write slot 1, then copy the registrar runtime
    # appended after it and return it for deposit.
    store = Op.SSTORE(
        key=0x1, value=0x1, key_warm=False, original_value=0, new_value=1
    )
    deposited = (
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
    deposited_size = len(deposited)
    initcode = (
        store
        + Op.CODECOPY(
            dest_offset=0x0,
            offset=COPY_OFFSET,
            size=deposited_size,
            data_size=deposited_size,
            new_memory_size=deposited_size,
        )
        + Op.RETURN(0, deposited_size, code_deposit_size=deposited_size)
        + Op.STOP
    )
    assert len(initcode) == COPY_OFFSET
    calldata = initcode + deposited

    # Fork-derived budget: exactly what the creation needs, so one gas
    # less must fail. The deposit is already inside the init code's cost,
    # via RETURN's `code_deposit_size`.
    overhead = fork.transaction_intrinsic_cost_calculator()(
        calldata=calldata,
        contract_creation=True,
        return_cost_deducted_prior_execution=True,
    ) + fork.transaction_top_frame_state_gas(
        contract_creation=True, sends_value=value > 0
    )
    execution_cost = initcode.gas_cost(fork)
    gas_limit = overhead + execution_cost
    if not enough_gas:
        gas_limit -= 1

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=None,
        data=calldata,
        gas_limit=gas_limit,
        value=value,
    )

    created = compute_create_address(address=sender, nonce=0)
    if enough_gas:
        created_account: Account | None = Account(
            nonce=1,
            code=deposited,
            balance=value,
            storage={1: 1},
        )
    else:
        created_account = Account.NONEXISTENT
    post = {
        sender: Account(nonce=1),
        created: created_account,
    }

    state_test(pre=pre, post=post, tx=tx)
