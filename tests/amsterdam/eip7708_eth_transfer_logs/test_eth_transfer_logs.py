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
    compute_create_address,
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


def selfdestruct_log(contract: Address, amount: int) -> TransactionLog:
    """Create an expected selfdestruct log (for selfdestruct to self)."""
    return TransactionLog(
        address=Spec.SYSTEM_ADDRESS,
        topics=[
            Spec.SELFDESTRUCT_TOPIC,
            Hash(bytes(contract).rjust(32, b"\x00")),
        ],
        data=Bytes(amount.to_bytes(32, "big")),
    )


def test_selfdestruct_to_self_emits_finalization_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """
    Test that selfdestruct-to-self emits a finalization log for remaining ETH.

    Scenario:
    1. Factory creates child contract via CREATE with 1000 wei
    2. Factory calls child, child selfdestructs to itself (emits log for 1000)
    3. Factory sends 500 more wei to child (transfer log emitted)
    4. At finalization, child has 500 wei remaining (emits finalization log)

    This tests the EIP-7708 requirement that when a contract receives ETH after
    being flagged for SELFDESTRUCT, a Selfdestruct log is emitted at
    finalization for the remaining balance.
    """
    tx_value = 2000
    child_init_balance = 1000
    additional_eth = 500

    # Child contract: selfdestructs to itself (address(this))
    child_code = Op.SELFDESTRUCT(Op.ADDRESS)
    child_initcode = Op.MSTORE(
        0, Op.PUSH32(bytes(child_code).rjust(32, b"\x00"))
    ) + Op.RETURN(32 - len(child_code), len(child_code))

    initcode_len = len(child_initcode)

    # Factory: CREATE child, CALL to trigger selfdestruct, CALL again with ETH
    factory_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(1, Op.CREATE(child_init_balance, 0, initcode_len))
        + Op.CALL(address=Op.SLOAD(1), value=0, gas=50_000)
        + Op.POP
        + Op.CALL(address=Op.SLOAD(1), value=additional_eth, gas=50_000)
        + Op.POP
    )

    factory = pre.deploy_contract(
        factory_code, balance=child_init_balance + additional_eth
    )
    child_addr = compute_create_address(address=factory, nonce=1)

    # Expected logs:
    # 1. Transfer: sender -> factory (tx value)
    # 2. Transfer: factory -> child (CREATE value)
    # 3. Selfdestruct: child (initial balance at execution)
    # 4. Transfer: factory -> child (additional ETH)
    # 5. Selfdestruct: child (remaining balance at finalization)
    expected_logs = [
        transfer_log(sender, factory, tx_value),
        transfer_log(factory, child_addr, child_init_balance),
        selfdestruct_log(child_addr, child_init_balance),
        transfer_log(factory, child_addr, additional_eth),
        selfdestruct_log(child_addr, additional_eth),
    ]

    tx = Transaction(
        sender=sender,
        to=factory,
        value=tx_value,
        gas_limit=500_000,
        data=bytes(child_initcode),
        expected_receipt=TransactionReceipt(logs=expected_logs),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.parametrize(
    "op_type",
    [
        pytest.param("call", id="call"),
        pytest.param("selfdestruct", id="selfdestruct"),
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
    "recipient_code,call_gas,call_value,recipient_balance",
    [
        pytest.param(Op.REVERT(0, 0), 50_000, 500, 0, id="call_reverted"),
        pytest.param(Op.JUMP(0), 100, 500, 0, id="call_out_of_gas"),
        pytest.param(
            Op.SELFDESTRUCT(Address(0x1234)),
            100,
            0,
            2000,
            id="selfdestruct_out_of_gas",
        ),
    ],
)
def test_failed_inner_operation_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    recipient_code: Bytecode,
    call_gas: int,
    call_value: int,
    recipient_balance: int,
) -> None:
    """Test that failed inner operations do NOT emit transfer logs."""
    recipient = pre.deploy_contract(recipient_code, balance=recipient_balance)
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

    # Build chain: contracts[0] -> contracts[1] -> ... -> final_recipient
    final_recipient = pre.empty_account()
    contracts: list[Address] = []
    expected_logs: list[TransactionLog] = []

    # Build contracts in reverse order (deepest first)
    next_target = final_recipient
    for _ in range(call_depth):
        contract_code = Op.CALL(
            gas=500_000, address=next_target, value=transfer_value
        )
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


@pytest.mark.parametrize(
    "address_type",
    [
        pytest.param("ecrecover", id="precompile_ecrecover"),
        pytest.param("sha256", id="precompile_sha256"),
        pytest.param("system", id="system_address"),
        pytest.param("coinbase", id="coinbase_address"),
    ],
)
def test_transfer_to_special_address(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    address_type: str,
) -> None:
    """Test that transfers to special addresses emit transfer logs."""
    transfer_amount = 1000

    # Resolve target address based on type
    # Note: blake2f (0x09) excluded as it requires specific input format
    address_map = {
        "ecrecover": Address(0x01),
        "sha256": Address(0x02),
        "system": Spec.SYSTEM_ADDRESS,
    }

    if address_type == "coinbase":
        target = env.fee_recipient
        # Don't check exact balance - coinbase also receives gas fees
        post = {}
    else:
        target = address_map[address_type]
        post = {target: Account(balance=transfer_amount)}

    tx = Transaction(
        sender=sender,
        to=target,
        value=transfer_amount,
        gas_limit=100_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(sender, target, transfer_amount)]
        ),
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.with_all_typed_transactions
def test_transfer_with_all_tx_types(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    typed_transaction: Transaction,
) -> None:
    """Test that ETH transfers emit logs for all transaction types."""
    recipient = pre.empty_account()
    transfer_amount = 1000

    tx = typed_transaction.copy(
        to=recipient,
        value=transfer_amount,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(sender, recipient, transfer_amount)]
        ),
    )

    post = {recipient: Account(balance=transfer_amount)}
    state_test(env=env, pre=pre, post=post, tx=tx)
