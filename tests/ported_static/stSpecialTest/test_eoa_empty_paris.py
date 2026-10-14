"""
Test_eoa_empty_paris.

Ported from:
state_tests/stSpecialTest/eoaEmptyParisFiller.yml

@manually-enhanced: Do not overwrite. Slots 0xF1 and 0xFF measure the
CALLs to the origin and to the self-destructing contract with
`CodeGasMeasure`, and expect the gas their opcode metadata prices, so
repricings such as EIP-8038 need no per-fork adjustment. `EXTCODEHASH`
of the code-less accounts other than the origin moved to
`test_external_account_empty_paris`, one case per account kind, so only
the nonce-0 account with storage needs a mutable pre-alloc.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    CodeGasMeasure,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionException,
    keccak256,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_GAS_LIMIT = 10_000_000
"""Gas limit the sender's balance pays for in full."""

TX_VALUE = 100
"""Value of the value-bearing transactions, in wei."""


@pytest.mark.ported_from(
    ["state_tests/stSpecialTest/eoaEmptyParisFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("origin_call_value", [0, 1])
@pytest.mark.parametrize(
    "gas_limit_reduction, tx_value",
    [
        (0, 0),
        # Gas takes the whole balance, leaving nothing for the value.
        pytest.param(0, TX_VALUE, marks=pytest.mark.exception_test),
        (1, 0),
        (1, TX_VALUE),
    ],
)
def test_origin_empty_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    origin_call_value: int,
    gas_limit_reduction: int,
    tx_value: int,
) -> None:
    """Test_eoa_empty_paris."""
    # Reducing the gas limit by one unit leaves the sender one gas price
    # of balance. Matching the gas price to the value lets that leftover
    # pay the value exactly, draining the origin to a zero balance.
    tx_gas_price = TX_VALUE

    sender_amount = TX_GAS_LIMIT * tx_gas_price
    sender = pre.fund_eoa(amount=sender_amount)

    tx_gas = TX_GAS_LIMIT - gas_limit_reduction

    tx_sender_start_balance = (
        sender_amount - (tx_gas * tx_gas_price) - tx_value
    )

    # The origin is warm, and alive despite its zero balance, so no new
    # account is charged for.
    selfdestruct_code = Op.SELFDESTRUCT(
        address=Op.ORIGIN, address_warm=True, account_new=False
    )
    selfdestruct_contract = pre.deploy_contract(
        code=selfdestruct_code,
        balance=10_000,
        nonce=1,
    )
    slot_origin = 0x0
    slot_origin_balance = 0x31
    slot_origin_code_size = 0x3B
    slot_origin_code_hash = 0x3F
    slot_call_origin_gas = 0xF1
    slot_call_selfdestruct_gas = 0xFF
    # The origin is warm, and alive despite its zero balance, so a value
    # transfer to it charges no new account.
    call_origin = Op.CALL(
        address=Op.ORIGIN,
        value=Op.CALLDATALOAD(offset=0x0),
        address_warm=True,
        value_transfer=origin_call_value > 0,
        account_new=False,
    )
    call_selfdestruct = Op.CALL(address=selfdestruct_contract)
    target = pre.deploy_contract(
        code=Op.SSTORE(key=slot_origin, value=Op.ORIGIN)
        + Op.SSTORE(
            key=slot_origin_balance, value=Op.BALANCE(address=Op.ORIGIN)
        )
        + Op.SSTORE(
            key=slot_origin_code_size, value=Op.EXTCODESIZE(address=Op.ORIGIN)
        )
        + Op.SSTORE(
            key=slot_origin_code_hash, value=Op.EXTCODEHASH(address=Op.ORIGIN)
        )
        + CodeGasMeasure(
            code=call_origin,
            extra_stack_items=1,
            sstore_key=slot_call_origin_gas,
        )
        + CodeGasMeasure(
            code=call_selfdestruct,
            extra_stack_items=1,
            sstore_key=slot_call_selfdestruct_gas,
        ),
        nonce=1,
    )

    empty_code_hash = keccak256(b"")
    # A value-bearing call hands the stipend to the origin, which has no
    # code to spend it, so it comes back.
    call_origin_gas = call_origin.gas_cost(fork)
    if origin_call_value > 0:
        call_origin_gas -= fork.call_value_stipend()
    call_selfdestruct_gas = call_selfdestruct.gas_cost(
        fork
    ) + selfdestruct_code.gas_cost(fork)

    tx_error: TransactionException | None = None
    post: dict = {}
    if tx_sender_start_balance < 0:
        # The sender cannot pay for both the gas and the value.
        tx_error = TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
    else:
        post = {
            sender: Account(nonce=1),
            target: Account(
                storage={
                    slot_origin: sender,
                    slot_origin_balance: tx_sender_start_balance,
                    slot_origin_code_size: 0,
                    slot_origin_code_hash: empty_code_hash,
                    slot_call_origin_gas: call_origin_gas,
                    slot_call_selfdestruct_gas: call_selfdestruct_gas,
                },
            ),
        }

    tx = Transaction(
        sender=sender,
        to=target,
        data=Hash(origin_call_value),
        gas_limit=tx_gas,
        value=tx_value,
        gas_price=tx_gas_price,
        error=tx_error,
    )

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/stSpecialTest/eoaEmptyParisFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "account_kind",
    [
        "nonexistent",
        "balance_only",
        "nonce_only",
        "balance_and_nonce",
        # Storage without code needs a nonce of 0, which only a mutable
        # pre-allocation can hold.
        pytest.param(
            "storage_and_balance", marks=pytest.mark.pre_alloc_mutable
        ),
    ],
)
def test_external_account_empty_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    account_kind: str,
) -> None:
    """
    Verify `EXTCODEHASH` of an account without code: the empty code hash
    when the account exists, and zero when it does not.
    """
    expected_code_hash: int | Hash = keccak256(b"")
    if account_kind == "nonexistent":
        account = pre.nonexistent_account()
        expected_code_hash = 0
    elif account_kind == "balance_only":
        account = pre.fund_eoa(amount=1)
    elif account_kind == "nonce_only":
        account = pre.deploy_contract(code="", nonce=1)
    elif account_kind == "balance_and_nonce":
        account = pre.deploy_contract(code="", balance=1, nonce=1)
    else:
        account = pre.deploy_contract(
            code="", storage={0xDEAD: 0xBEEF}, balance=10, nonce=0
        )

    # A sentinel in the slot makes a stored zero observable.
    slot_code_hash = 0x0
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=slot_code_hash,
            value=Op.EXTCODEHASH(address=Op.CALLDATALOAD(0)),
        ),
        storage={slot_code_hash: 0xDEADBEEF},
    )

    tx = Transaction(
        sender=pre.fund_eoa(), to=target, data=Hash(account, left_padding=True)
    )

    state_test(
        pre=pre,
        post={target: Account(storage={slot_code_hash: expected_code_hash})},
        tx=tx,
    )
