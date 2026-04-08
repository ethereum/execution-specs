"""
Tests for EIP-7708 Transfer logs.

Tests for the Transfer(address,address,uint256) log emitted when:
- Nonzero-value-transferring transaction
- Nonzero-value-transferring CALL
- Nonzero-value-transferring SELFDESTRUCT to a different account
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Bytes,
    Environment,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    TransactionLog,
    TransactionReceipt,
    compute_create2_address,
    compute_create_address,
)

from .spec import Spec, ref_spec_7708, transfer_log

REFERENCE_SPEC_GIT_PATH = ref_spec_7708.git_path
REFERENCE_SPEC_VERSION = ref_spec_7708.version

pytestmark = pytest.mark.valid_from("EIP7708")


def test_simple_transfer_emits_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """Test that a simple ETH transfer emits a transfer log."""
    recipient = pre.nonexistent_account()

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=1,
        gas_limit=21_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(sender, recipient, 1)]
        ),
    )

    post = {recipient: Account(balance=1)}
    state_test(env=env, pre=pre, post=post, tx=tx)


def test_transfer_to_delegated_account_emits_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """
    Test that transfer to EIP-7702 delegated account emits correct log.

    The transfer log should show the EOA address as recipient,
    not the delegation target address.
    """
    delegation_target = pre.deploy_contract(code=Op.STOP)
    recipient = pre.fund_eoa(amount=0, delegation=delegation_target)

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=1,
        gas_limit=100_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(sender, recipient, 1)]
        ),
    )

    post = {recipient: Account(balance=1)}
    state_test(env=env, pre=pre, post=post, tx=tx)


def test_transfer_to_self_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """Test that a transaction sending value to self emits no transfer log."""
    tx = Transaction(
        sender=sender,
        to=sender,
        value=1,
        gas_limit=21_000,
        expected_receipt=TransactionReceipt(logs=[]),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


def test_zero_value_transfer_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """Test that a zero-value transfer does NOT emit a transfer log."""
    recipient = pre.nonexistent_account()

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        gas_limit=21_000,
        expected_receipt=TransactionReceipt(logs=[]),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.parametrize(
    "tx_value,expect_log",
    [
        pytest.param(1000, True, id="with_value"),
        pytest.param(0, False, id="zero_value"),
    ],
)
def test_contract_creation_tx(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    tx_value: int,
    expect_log: bool,
) -> None:
    """Test that contract creation transactions emit logs based on value."""
    initcode = Op.RETURN(0, 0)
    created_address = compute_create_address(address=sender, nonce=0)

    expected_logs = (
        [transfer_log(sender, created_address, tx_value)] if expect_log else []
    )

    tx = Transaction(
        sender=sender,
        to=None,
        value=tx_value,
        gas_limit=100_000,
        data=bytes(initcode),
        expected_receipt=TransactionReceipt(logs=expected_logs),
    )

    post = {created_address: Account(balance=tx_value)} if tx_value > 0 else {}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.with_all_call_opcodes
def test_call_opcodes_transfer_log_behavior(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    call_opcode: Op,
) -> None:
    """
    Test ETH transfer log behavior across all call opcode contexts.

    - CALL with value: emits log (caller -> callee)
    - CALLCODE with value: emits log (caller -> caller) as self-transfer
    - DELEGATECALL: no value parameter, no transfer log
    - STATICCALL: no value parameter, no transfer log
    """
    callee = pre.deploy_contract(Op.STOP)

    # Build the call based on opcode type
    if call_opcode in [Op.CALL, Op.CALLCODE]:
        # These opcodes have a value parameter
        call_code = call_opcode(gas=100_000, address=callee, value=1)
    else:
        # DELEGATECALL and STATICCALL don't have value parameter
        call_code = call_opcode(gas=100_000, address=callee)

    contract = pre.deploy_contract(call_code, balance=1)

    # Determine expected logs based on opcode behavior
    expected_logs = [transfer_log(sender, contract, 1)]

    if call_opcode == Op.CALL:
        # CALL transfers value from contract to callee
        expected_logs.append(transfer_log(contract, callee, 1))
        post = {callee: Account(balance=1)}
    elif call_opcode == Op.CALLCODE:
        # CALLCODE transfers value but stays in caller's context.
        # This is a self-transfer (contract -> contract), so no transfer
        # log per EIP-7708 ("CALL to a different account").
        post = {}
    else:
        # DELEGATECALL and STATICCALL: no value transfer, no additional log
        post = {}

    tx = Transaction(
        sender=sender,
        to=contract,
        value=1,
        gas_limit=200_000,
        expected_receipt=TransactionReceipt(logs=expected_logs),
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


def test_delegatecall_inner_call_with_value(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """
    Test DELEGATECALL to code that performs CALL with value.

    Scenario: A DELEGATECALLs B, B does CALL with value to C.
    The CALL from B executes in A's context, so log shows A as sender.
    """
    recipient = pre.deploy_contract(Op.STOP)

    # B: code that CALLs recipient with value
    code_b = Op.CALL(gas=50_000, address=recipient, value=1)
    contract_b = pre.deploy_contract(code_b)

    # A: DELEGATECALLs to B (executes B's code in A's context)
    code_a = Op.DELEGATECALL(gas=100_000, address=contract_b)
    contract_a = pre.deploy_contract(code_a, balance=1)

    tx = Transaction(
        sender=sender,
        to=contract_a,
        value=0,
        gas_limit=200_000,
        expected_receipt=TransactionReceipt(
            logs=[
                # CALL from B executes in A's context, so A is the sender
                transfer_log(contract_a, recipient, 1),
            ]
        ),
    )

    post = {recipient: Account(balance=1)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "create_value",
    [
        pytest.param(1, id="with_value"),
        pytest.param(0, id="zero_value"),
    ],
)
@pytest.mark.with_all_create_opcodes
def test_create_opcode_emits_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    create_opcode: Op,
    create_value: int,
) -> None:
    """Test that CREATE/CREATE2 opcodes emit logs based on value."""
    initcode = Op.RETURN(0, 0)
    initcode_len = len(initcode)

    contract_code = Op.MSTORE(
        0, Op.PUSH32(bytes(initcode).rjust(32, b"\x00"))
    ) + Op.SSTORE(
        0,
        create_opcode(
            value=create_value, offset=32 - initcode_len, size=initcode_len
        ),
    )
    contract = pre.deploy_contract(contract_code, balance=create_value)
    created_address = compute_create_address(
        address=contract,
        nonce=1,
        salt=0,
        initcode=bytes(initcode),
        opcode=create_opcode,
    )

    expected_logs = [transfer_log(sender, contract, 1)]
    if create_value > 0:
        expected_logs.append(
            transfer_log(contract, created_address, create_value)
        )

    tx = Transaction(
        sender=sender,
        to=contract,
        value=1,
        gas_limit=200_000,
        expected_receipt=TransactionReceipt(logs=expected_logs),
    )

    post = {created_address: Account(balance=create_value)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.with_all_create_opcodes
def test_initcode_calls_with_value(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    create_opcode: Op,
) -> None:
    """
    Test that CALL with value during initcode emits correct log.

    Initcode performs CALL with value before returning deployed code.
    Log should show the being-created contract as sender.
    """
    recipient = pre.deploy_contract(Op.STOP)

    # Initcode: CALL recipient with value, then RETURN empty code
    initcode = Op.CALL(gas=50_000, address=recipient, value=1) + Op.RETURN(
        0, 0
    )
    initcode_bytes = bytes(initcode)

    # Use Initcode helper or direct memory setup for longer initcode
    if create_opcode == Op.CREATE:
        # Store initcode in memory using code copy approach
        factory_code = (
            Op.CODECOPY(
                0,
                Op.SUB(Op.CODESIZE, len(initcode_bytes)),
                len(initcode_bytes),
            )
            + Op.CREATE(value=1, offset=0, size=len(initcode_bytes))
            + Op.STOP
        ) + initcode
    else:
        factory_code = (
            Op.CODECOPY(
                0,
                Op.SUB(Op.CODESIZE, len(initcode_bytes)),
                len(initcode_bytes),
            )
            + Op.CREATE2(value=1, offset=0, size=len(initcode_bytes), salt=0)
            + Op.STOP
        ) + initcode

    factory = pre.deploy_contract(factory_code, balance=2)

    # Compute created address
    if create_opcode == Op.CREATE:
        created_address = compute_create_address(address=factory, nonce=1)
    else:
        created_address = compute_create2_address(
            address=factory, salt=0, initcode=initcode_bytes
        )

    tx = Transaction(
        sender=sender,
        to=factory,
        value=0,
        gas_limit=300_000,
        expected_receipt=TransactionReceipt(
            logs=[
                # CREATE transfers value to new contract
                transfer_log(factory, created_address, 1),
                # Initcode CALLs recipient with value
                transfer_log(created_address, recipient, 1),
            ]
        ),
    )

    post = {recipient: Account(balance=1)}
    state_test(env=env, pre=pre, post=post, tx=tx)


def test_create_initcode_stop_emits_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """
    Test that CREATE with initcode using STOP (no RETURN) emits transfer log.

    When initcode runs STOP instead of RETURN, the contract is created with
    empty code. This is a successful CREATE, so transfer log should be emitted.
    """
    contract_code = Op.MSTORE(
        0, Op.PUSH32(bytes(Op.STOP).rjust(32, b"\x00"))
    ) + Op.CREATE(value=1, offset=31, size=1)
    contract = pre.deploy_contract(contract_code, balance=1)

    created_address = compute_create_address(address=contract, nonce=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        value=0,
        gas_limit=500_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(contract, created_address, 1)]
        ),
    )

    post = {created_address: Account(balance=1, code=b"")}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "initcode",
    [
        pytest.param(Op.REVERT(0, 0), id="initcode_reverts"),
        pytest.param(Op.INVALID, id="initcode_invalid"),
    ],
)
def test_failed_create_with_value_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    initcode: Bytecode,
) -> None:
    """
    Test that failed CREATE with value does NOT emit transfer log.

    When initcode fails (REVERT, INVALID), the value transfer is reverted
    and no log should be emitted for the CREATE.
    """
    initcode_len = len(initcode)
    contract_code = Op.MSTORE(
        0, Op.PUSH32(bytes(initcode).rjust(32, b"\x00"))
    ) + Op.SSTORE(0, Op.CREATE(1, 32 - initcode_len, initcode_len))
    contract = pre.deploy_contract(contract_code, balance=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        value=1,
        gas_limit=500_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(sender, contract, 1)]
        ),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


def test_create_insufficient_balance_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """
    Test that CREATE with insufficient balance does NOT emit transfer log.

    Contract receives 1, tries to CREATE with 1000 value - CREATE fails
    (returns 0) but doesn't halt, so tx-level log remains.
    """
    initcode = Op.RETURN(0, 0)
    initcode_len = len(initcode)
    contract_code = Op.MSTORE(
        0, Op.PUSH32(bytes(initcode).rjust(32, b"\x00"))
    ) + Op.SSTORE(0, Op.CREATE(1000, 32 - initcode_len, initcode_len))
    contract = pre.deploy_contract(contract_code, balance=0)

    tx = Transaction(
        sender=sender,
        to=contract,
        value=1,
        gas_limit=500_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(sender, contract, 1)]
        ),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.parametrize(
    "initcode",
    [
        pytest.param(
            # OOG before return
            Op.MSTORE(offset=0xFFFFFF, value=0) + Op.RETURN(0, 0),
            id="create_out_of_gas_memory_expansion",
        ),
        pytest.param(
            # Invalid opcode
            Op.INVALID + Op.RETURN(0, 0),
            id="invalid_opcode",
        ),
        pytest.param(
            # OOG during code deposit payment (200 gas/byte for returned code)
            # Returns 1000 bytes which costs 200,000 gas for code deposit
            Op.RETURN(0, 1000),
            id="create_out_of_gas_code_deposit",
        ),
    ],
)
def test_create_out_of_gas_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    initcode: Bytecode,
) -> None:
    """Test that CREATE running out of gas does NOT emit transfer log."""
    tx_value = 1000
    gas_limit = 100_000
    create_value = 500
    contract_code = Op.CALLDATACOPY(
        dest_offset=0,
        offset=0,
        size=Op.CALLDATASIZE,
    ) + Op.CREATE(value=create_value, offset=0, size=Op.CALLDATASIZE)
    contract = pre.deploy_contract(contract_code)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=initcode,
        value=tx_value,
        gas_limit=gas_limit,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(sender, contract, tx_value)]
        ),
    )
    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.parametrize(
    "contract_code",
    [
        pytest.param(
            # CALL stack underflow: only push 6 items instead of 7
            Op.PUSH1(0)
            + Op.PUSH1(0)
            + Op.PUSH1(0)
            + Op.PUSH1(0)
            + Op.PUSH1(100)
            + Op.PUSH2(0x1234)
            + Op.CALL,
            id="call_stack_underflow",
        ),
        pytest.param(
            # CREATE stack underflow: only push 2 items instead of 3
            Op.PUSH1(0) + Op.PUSH1(0) + Op.CREATE,
            id="create_stack_underflow",
        ),
    ],
)
def test_stack_underflow_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    contract_code: Bytecode,
) -> None:
    """Test that stack underflow during CALL/CREATE does NOT emit log."""
    contract = pre.deploy_contract(contract_code, balance=1000)

    tx = Transaction(
        sender=sender,
        to=contract,
        value=1000,
        gas_limit=100_000,
        expected_receipt=TransactionReceipt(logs=[]),  # TX fails, no logs
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.pre_alloc_mutable
@pytest.mark.with_all_create_opcodes
def test_create_collision_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    create_opcode: Op,
) -> None:
    """
    Test that CREATE/CREATE2 collision does not emit transfer log.

    When CREATE fails because target address already has code/nonce,
    no value transfer occurs and no log should be emitted.
    """
    initcode = Op.RETURN(0, 0)
    initcode_bytes = bytes(initcode)
    initcode_len = len(initcode_bytes)

    # Deploy factory first to compute created address
    if create_opcode == Op.CREATE:
        factory_code = Op.MSTORE(
            0, Op.PUSH32(initcode_bytes.rjust(32, b"\x00"))
        ) + Op.CREATE(value=1, offset=32 - initcode_len, size=initcode_len)
    else:
        factory_code = Op.MSTORE(
            0, Op.PUSH32(initcode_bytes.rjust(32, b"\x00"))
        ) + Op.CREATE2(
            value=1, offset=32 - initcode_len, size=initcode_len, salt=0
        )

    factory = pre.deploy_contract(factory_code, balance=1)

    # Compute and pre-populate the collision address
    if create_opcode == Op.CREATE:
        collision_address = compute_create_address(address=factory, nonce=1)
    else:
        collision_address = compute_create2_address(
            address=factory, salt=0, initcode=initcode_bytes
        )

    # Pre-deploy contract at collision address to cause collision
    pre.deploy_contract(Op.STOP, address=collision_address)

    tx = Transaction(
        sender=sender,
        to=factory,
        value=0,
        gas_limit=200_000,
        expected_receipt=TransactionReceipt(
            logs=[]
        ),  # No logs - CREATE failed
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


def test_selfdestruct_with_value_emits_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """Test that SELFDESTRUCT with value emits a transfer log."""
    beneficiary = pre.nonexistent_account()
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


def test_selfdestruct_to_system_address(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """
    Test SELFDESTRUCT sending ETH to the EIP-7708 system address.

    Edge case: beneficiary is the same address (0xff...fe) that emits logs.
    """
    contract_code = Op.SELFDESTRUCT(Spec.SYSTEM_ADDRESS)
    contract = pre.deploy_contract(contract_code, balance=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        value=0,
        gas_limit=100_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(contract, Spec.SYSTEM_ADDRESS, 1)]
        ),
    )

    post = {Spec.SYSTEM_ADDRESS: Account(balance=1)}
    state_test(env=env, pre=pre, post=post, tx=tx)


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
    target = pre.nonexistent_account()

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
    "call_opcode",
    [
        pytest.param(Op.CALL, id="call"),
        pytest.param(Op.CALLCODE, id="callcode"),
    ],
)
def test_call_to_self_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    call_opcode: Op,
) -> None:
    """
    Test that CALL/CALLCODE with value to self emits no transfer log.

    Uses CALLDATASIZE to detect recursion: external call has no calldata,
    recursive call passes 1 byte of calldata to signal stop.
    """
    # CALLDATASIZE > 0 means recursive call, jump to end
    # Byte offsets: CALLDATASIZE(1) + PUSH1(2) + JUMPI(1) = 4
    # CALL with args_size=1: ~16 bytes, JUMPDEST at offset 20
    contract_code = (
        Op.CALLDATASIZE
        + Op.PUSH1(20)
        + Op.JUMPI
        + call_opcode(gas=100_000, address=Op.ADDRESS, value=1, args_size=1)
        + Op.JUMPDEST
        + Op.STOP
    )
    contract = pre.deploy_contract(contract_code, balance=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        value=0,
        gas_limit=200_000,
        expected_receipt=TransactionReceipt(logs=[]),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.parametrize(
    "recipient_code,call_gas,call_value,recipient_balance,contract_balance",
    [
        pytest.param(Op.REVERT(0, 0), 50_000, 500, 0, 500, id="call_reverted"),
        pytest.param(Op.JUMP(0), 100, 500, 0, 500, id="call_out_of_gas"),
        pytest.param(
            # OOG with memory expansion - tries to access large memory offset
            Op.MSTORE(0xFFFFFF, 0) + Op.STOP,
            1000,
            500,
            0,
            500,
            id="call_out_of_gas_memory_expansion",
        ),
        pytest.param(
            Op.SELFDESTRUCT(Address(0x1234)),
            100,
            0,
            2000,
            0,
            id="selfdestruct_out_of_gas",
        ),
        pytest.param(
            Op.STOP,
            50_000,
            2000,
            0,
            0,
            id="call_insufficient_balance",
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
    contract_balance: int,
) -> None:
    """Test that failed inner operations do NOT emit transfer logs."""
    recipient = pre.deploy_contract(recipient_code, balance=recipient_balance)
    tx_value = 1000

    contract_code = Op.CALL(
        gas=call_gas,
        address=recipient,
        value=call_value,
    )
    contract = pre.deploy_contract(contract_code, balance=contract_balance)

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
    "inner_calls",
    [
        pytest.param(1, id="single_call"),
        pytest.param(3, id="multiple_calls"),
    ],
)
def test_inner_call_succeeds_outer_reverts_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    inner_calls: int,
) -> None:
    """
    Test that logs from successful inner calls are rolled back on outer revert.

    Scenario: Contract performs N CALLs with value (all succeed), then REVERTs.
    Expected: No logs remain (all transfer logs are rolled back).
    """
    callee = pre.deploy_contract(Op.STOP)

    # Build contract code: N CALLs with value, then REVERT
    contract_code = Op.CALL(gas=100_000, address=callee, value=1)
    for _ in range(inner_calls - 1):
        contract_code += Op.POP + Op.CALL(gas=100_000, address=callee, value=1)
    contract_code += Op.POP + Op.REVERT(0, 0)

    contract = pre.deploy_contract(contract_code, balance=inner_calls)

    tx = Transaction(
        sender=sender,
        to=contract,
        value=1,
        gas_limit=500_000,
        expected_receipt=TransactionReceipt(logs=[]),
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
    final_recipient = pre.nonexistent_account()
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


def test_contract_log_and_transfer_ordering(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """
    Test log ordering between contract-emitted logs and transfer logs.

    Scenario: Contract emits LOG0, then CALLs with value.
    Expected order: tx transfer log, contract LOG0, CALL transfer log.
    """
    callee = pre.deploy_contract(Op.STOP)

    # Contract emits LOG0, then CALLs callee with value
    contract_code = (
        Op.MSTORE(0, 0xDEADBEEF)
        + Op.LOG0(offset=0, size=32)  # Emit LOG0 with data
        + Op.CALL(gas=50_000, address=callee, value=1)
    )
    contract = pre.deploy_contract(contract_code, balance=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        value=1,
        gas_limit=200_000,
        expected_receipt=TransactionReceipt(
            logs=[
                # 1. TX-level transfer
                transfer_log(sender, contract, 1),
                # 2. Contract LOG0 (emitted before CALL)
                TransactionLog(
                    address=contract,
                    topics=[],
                    data=Bytes((0xDEADBEEF).to_bytes(32, "big")),
                ),
                # 3. CALL transfer (emitted during CALL)
                transfer_log(contract, callee, 1),
            ]
        ),
    )

    post = {callee: Account(balance=1)}
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
    recipient = pre.nonexistent_account()
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


def test_multiple_transfers_same_block(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Test that multiple transfers in the same block have independent logs.

    Each transaction should have its own transfer log in its receipt,
    verifying logs don't bleed across transactions.
    """
    sender = pre.fund_eoa()
    recipient1 = pre.nonexistent_account()
    recipient2 = pre.nonexistent_account()

    blocks = [
        Block(
            txs=[
                Transaction(
                    to=recipient1,
                    sender=sender,
                    nonce=0,
                    value=100,
                    gas_limit=21_000,
                    expected_receipt=TransactionReceipt(
                        logs=[transfer_log(sender, recipient1, 100)]
                    ),
                ),
                Transaction(
                    to=recipient2,
                    sender=sender,
                    nonce=1,
                    value=200,
                    gas_limit=21_000,
                    expected_receipt=TransactionReceipt(
                        logs=[transfer_log(sender, recipient2, 200)]
                    ),
                ),
            ],
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            recipient1: Account(balance=100),
            recipient2: Account(balance=200),
        },
    )


def test_selfdestruct_then_transfer_same_block(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Test transfer to address that selfdestructed earlier in the same block.

    Tx1: Contract selfdestructs, sending balance to beneficiary.
    Tx2: Transfer to the contract triggers SELFDESTRUCT again (code not deleted
         per EIP-6780), sending the received value to beneficiary.

    Expected logs:
    - Tx1: contract -> beneficiary (500)
    - Tx2: sender -> contract (100) + contract -> beneficiary (100)
    """
    sender = pre.fund_eoa()
    beneficiary = pre.nonexistent_account()

    contract_code = Op.SELFDESTRUCT(beneficiary)
    contract = pre.deploy_contract(contract_code, balance=500)

    blocks = [
        Block(
            txs=[
                Transaction(
                    to=contract,
                    sender=sender,
                    nonce=0,
                    value=0,
                    gas_limit=100_000,
                    expected_receipt=TransactionReceipt(
                        logs=[transfer_log(contract, beneficiary, 500)]
                    ),
                ),
                Transaction(
                    to=contract,
                    sender=sender,
                    nonce=1,
                    value=100,
                    gas_limit=100_000,
                    expected_receipt=TransactionReceipt(
                        logs=[
                            transfer_log(sender, contract, 100),
                            transfer_log(contract, beneficiary, 100),
                        ]
                    ),
                ),
            ],
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            beneficiary: Account(balance=600),
            contract: Account(balance=0),
        },
    )


def test_selfdestruct_to_self_cross_tx_no_log(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Test that selfdestruct-to-self in a cross-tx context emits no log.

    A contract created in Tx1 is not in created_accounts during Tx2.
    Selfdestruct-to-self in Tx2 emits no log per EIP-7708: no Burn
    log (not same-tx) and no Transfer log (not a different account).

    Tx1: Contract creation tx (to=None) deploying SELFDESTRUCT(ADDRESS),
         value=2000. Logs: [transfer_log(sender, created, 2000)]
    Tx2: Call created contract directly, value=0. Logs: []
    Post: contract keeps balance (not deleted, not in created_accounts in Tx2)
    """
    contract_balance = 2000
    sender = pre.fund_eoa()

    runtime_code = Op.SELFDESTRUCT(Op.ADDRESS)
    initcode = Initcode(deploy_code=runtime_code)

    # Calculate the address that will be created by the first tx
    created_address = compute_create_address(address=sender, nonce=0)

    blocks = [
        Block(
            txs=[
                # Tx1: Create the contract directly via contract creation tx
                Transaction(
                    to=None,
                    sender=sender,
                    nonce=0,
                    value=contract_balance,
                    data=bytes(initcode),
                    gas_limit=300_000,
                    expected_receipt=TransactionReceipt(
                        logs=[
                            transfer_log(
                                sender, created_address, contract_balance
                            ),
                        ]
                    ),
                ),
                # Tx2: Call the created contract directly (cross-tx)
                Transaction(
                    to=created_address,
                    sender=sender,
                    nonce=1,
                    value=0,
                    gas_limit=100_000,
                    expected_receipt=TransactionReceipt(logs=[]),
                ),
            ],
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            # Contract keeps balance: not deleted since not in
            # created_accounts during Tx2
            created_address: Account(balance=contract_balance),
        },
    )


def test_call_to_delegated_account_with_value(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """
    Test CALL opcode to 7702 delegated account with value.

    Unlike simple tx transfer, CALL to delegated account executes the
    delegated code. The transfer log should show the EOA as recipient.
    """
    delegation_target = pre.deploy_contract(code=Op.STOP)
    delegated_eoa = pre.fund_eoa(amount=0, delegation=delegation_target)

    caller_code = Op.CALL(gas=50_000, address=delegated_eoa, value=100)
    caller = pre.deploy_contract(caller_code, balance=100)

    tx = Transaction(
        sender=sender,
        to=caller,
        value=0,
        gas_limit=200_000,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(caller, delegated_eoa, 100)]
        ),
    )

    post = {delegated_eoa: Account(balance=100)}
    state_test(env=env, pre=pre, post=post, tx=tx)
