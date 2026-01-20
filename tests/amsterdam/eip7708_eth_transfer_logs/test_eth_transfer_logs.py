"""
Tests [EIP-7708: ETH Transfers Emit a Log](https://eips.ethereum.org/EIPS/eip-7708).

Tests for verifying that ETH transfers emit LOG3 events as specified.
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    Environment,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
    TransactionLog,
    TransactionReceipt,
)

from .spec import Spec, ref_spec_7708

REFERENCE_SPEC_GIT_PATH = ref_spec_7708.git_path
REFERENCE_SPEC_VERSION = ref_spec_7708.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def transfer_log(
    sender: Address, recipient: Address, amount: int
) -> TransactionLog:
    """Create an expected transfer log."""
    return TransactionLog(
        address=Spec.SYSTEM_ADDRESS,
        topics=[
            Spec.TRANSFER_TOPIC,
            Hash(bytes(sender).rjust(32, b"\x00")),
            Hash(bytes(recipient).rjust(32, b"\x00")),
        ],
        data=Bytes(amount.to_bytes(32, "big")),
    )


def test_simple_transfer_emits_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """Test that a simple ETH transfer emits a transfer log."""
    recipient = pre.empty_account()
    transfer_amount = 1000

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=transfer_amount,
        gas_limit=21_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(sender, recipient, transfer_amount)]
        ),
    )

    post = {recipient: Account(balance=transfer_amount)}
    state_test(env=env, pre=pre, post=post, tx=tx)


def test_zero_value_transfer_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """Test that a zero-value transfer does NOT emit a transfer log."""
    recipient = pre.empty_account()

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        gas_limit=21_000,
        expected_receipt=TransactionReceipt(logs=[]),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


def test_call_with_value_emits_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """Test that CALL with value emits a transfer log."""
    recipient = pre.empty_account()
    transfer_amount = 500
    tx_transfer_amount = 1000

    contract_code = Op.CALL(
        gas=100_000,
        address=recipient,
        value=transfer_amount,
    )
    contract = pre.deploy_contract(contract_code, balance=tx_transfer_amount)

    tx = Transaction(
        sender=sender,
        to=contract,
        value=tx_transfer_amount,
        gas_limit=100_000,
        expected_receipt=TransactionReceipt(
            logs=[
                transfer_log(sender, contract, tx_transfer_amount),
                transfer_log(contract, recipient, transfer_amount),
            ]
        ),
    )

    post = {recipient: Account(balance=transfer_amount)}
    state_test(env=env, pre=pre, post=post, tx=tx)


def test_selfdestruct_with_value_emits_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """Test that SELFDESTRUCT with value emits a transfer log."""
    beneficiary = pre.empty_account()
    contract_balance = 2000

    contract_code = Op.SELFDESTRUCT(beneficiary)
    contract = pre.deploy_contract(contract_code, balance=contract_balance)

    tx = Transaction(
        sender=sender,
        to=contract,
        value=0,
        gas_limit=100_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(contract, beneficiary, contract_balance)]
        ),
    )

    post = {beneficiary: Account(balance=contract_balance)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "op_type",
    [
        pytest.param("call", id="call_zero_value"),
        pytest.param("selfdestruct", id="selfdestruct_zero_balance"),
    ],
)
def test_zero_value_operations_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    op_type: str,
) -> None:
    """Test that zero-value operations do NOT emit transfer logs."""
    target = pre.empty_account()

    if op_type == "call":
        contract_code = Op.CALL(gas=100_000, address=target, value=0)
    else:
        contract_code = Op.SELFDESTRUCT(target)

    contract = pre.deploy_contract(contract_code, balance=0)

    tx = Transaction(
        sender=sender,
        to=contract,
        value=0,
        gas_limit=100_000,
        expected_receipt=TransactionReceipt(logs=[]),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.parametrize(
    "recipient_code,call_gas",
    [
        pytest.param(Op.REVERT(0, 0), 50_000, id="reverted_call"),
        pytest.param(Op.JUMP(0), 100, id="out_of_gas_call"),
    ],
)
def test_failed_call_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    recipient_code: Bytecode,
    call_gas: int,
) -> None:
    """Test that failed inner CALLs do NOT emit transfer logs."""
    recipient = pre.deploy_contract(recipient_code)
    call_value = 500
    tx_value = 1000

    contract_code = Op.CALL(
        gas=call_gas,
        address=recipient,
        value=call_value,
    )
    contract = pre.deploy_contract(contract_code, balance=call_value)

    tx = Transaction(
        sender=sender,
        to=contract,
        value=tx_value,
        gas_limit=100_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(sender, contract, tx_value)]
        ),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.parametrize(
    "call_depth",
    [
        pytest.param(2, id="depth_2"),
        pytest.param(3, id="depth_3"),
        pytest.param(10, id="depth_10"),
    ],
)
def test_nested_calls_log_order(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    call_depth: int,
) -> None:
    """Test that nested CALLs emit transfer logs in chronological order."""
    transfer_value = 100
    tx_value = 1000

    # Build chain of contracts: each calls the next with value
    # contracts[0] -> contracts[1] -> ... -> contracts[depth-1] -> final_recipient
    final_recipient = pre.empty_account()
    contracts: list[Address] = []
    expected_logs: list[TransactionLog] = []

    # Build contracts in reverse order (deepest first)
    next_target = final_recipient
    for i in range(call_depth):
        contract_code = Op.CALL(gas=500_000, address=next_target, value=transfer_value)
        # Each contract needs enough balance for its transfer
        contract = pre.deploy_contract(contract_code, balance=transfer_value)
        contracts.insert(0, contract)
        next_target = contract

    # First contract is the tx target
    entry_contract = contracts[0]

    # Build expected logs in chronological order
    # First: tx-level transfer (sender -> entry_contract)
    expected_logs.append(transfer_log(sender, entry_contract, tx_value))

    # Then: each CALL in order
    for i in range(call_depth):
        from_addr = contracts[i]
        to_addr = contracts[i + 1] if i + 1 < call_depth else final_recipient
        expected_logs.append(transfer_log(from_addr, to_addr, transfer_value))

    tx = Transaction(
        sender=sender,
        to=entry_contract,
        value=tx_value,
        gas_limit=1_000_000,
        expected_receipt=TransactionReceipt(logs=expected_logs),
    )

    post = {final_recipient: Account(balance=transfer_value)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "reverting_code",
    [
        pytest.param(Op.REVERT(0, 0), id="revert"),
        pytest.param(Op.INVALID, id="invalid_opcode"),
        pytest.param(Op.ADD, id="stack_underflow"),
        pytest.param(Op.MSTORE(2**256 - 1, 0), id="out_of_gas"),
    ],
)
def test_reverted_transaction_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    reverting_code: Bytecode,
) -> None:
    """Test that a failed transaction does NOT emit a transfer log."""
    contract = pre.deploy_contract(reverting_code)

    tx = Transaction(
        sender=sender,
        to=contract,
        value=1000,
        gas_limit=100_000,
        expected_receipt=TransactionReceipt(logs=[]),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)
