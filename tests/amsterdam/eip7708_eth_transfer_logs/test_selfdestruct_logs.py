"""
Tests for EIP-7708 Selfdestruct logs.

Tests for the Selfdestruct(address,uint256) log emitted when:
- SELFDESTRUCT to self with nonzero balance
- Account created and destroyed in the same transaction
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Alloc,
    Environment,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
    compute_create_address,
)
from execution_testing import (
    Macros as Om,
)

from .spec import ref_spec_7708, selfdestruct_log, transfer_log

REFERENCE_SPEC_GIT_PATH = ref_spec_7708.git_path
REFERENCE_SPEC_VERSION = ref_spec_7708.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def test_selfdestruct_to_self_pre_existing_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """
    Test that selfdestruct-to-self emits NO log for pre-existing contracts.

    Per EIP-7708, SELFDESTRUCT to the same account does not emit a Transfer
    log. The Selfdestruct log is only emitted when the account is created
    and destroyed in the same transaction (actual ETH burn).
    """
    contract_balance = 2000

    contract_code = Op.SELFDESTRUCT(Op.ADDRESS)
    contract = pre.deploy_contract(contract_code, balance=contract_balance)

    tx = Transaction(
        sender=sender,
        to=contract,
        value=0,
        gas_limit=100_000,
        expected_receipt=TransactionReceipt(logs=[]),
    )

    # Contract keeps its balance (not destroyed since not created in same tx)
    state_test(
        env=env,
        pre=pre,
        post={contract: Account(balance=contract_balance)},
        tx=tx,
    )


def test_selfdestruct_to_self_same_tx_emits_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """
    Test that selfdestruct-to-self emits a Selfdestruct log when created in
    same tx.

    A contract created via CREATE that immediately selfdestructs to itself
    in initcode is both created and destroyed in the same transaction.
    Expected logs:
    - CREATE transfer: factory -> created_address
    - Selfdestruct: created_address burns its balance
    """
    contract_balance = 2000

    initcode = Op.SELFDESTRUCT(Op.ADDRESS)
    initcode_bytes = bytes(initcode)
    initcode_len = len(initcode_bytes)

    factory_code = Op.MSTORE(
        0, Op.PUSH32(initcode_bytes.rjust(32, b"\x00"))
    ) + Op.CREATE(
        value=contract_balance, offset=32 - initcode_len, size=initcode_len
    )

    factory = pre.deploy_contract(factory_code, balance=contract_balance)
    created_address = compute_create_address(address=factory, nonce=1)

    tx = Transaction(
        sender=sender,
        to=factory,
        value=0,
        gas_limit=200_000,
        expected_receipt=TransactionReceipt(
            logs=[
                # CREATE transfers value to new contract
                transfer_log(factory, created_address, contract_balance),
                # Selfdestruct-to-self burns the balance
                selfdestruct_log(created_address, contract_balance),
            ]
        ),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.parametrize(
    "to_self",
    [
        pytest.param(True, id="to_self"),
        pytest.param(False, id="to_other"),
    ],
)
def test_selfdestruct_same_tx_zero_balance_no_log(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    to_self: bool,
) -> None:
    """
    Test that same-tx selfdestruct with zero balance emits no logs.

    Both emit_selfdestruct_log and emit_transfer_log skip zero amounts.
    A contract created with zero value that immediately selfdestructs in
    initcode should produce no logs regardless of beneficiary.
    """
    beneficiary = pre.deploy_contract(Op.STOP)

    if to_self:
        initcode = Op.SELFDESTRUCT(Op.ADDRESS)
    else:
        initcode = Op.SELFDESTRUCT(beneficiary)

    initcode_bytes = bytes(initcode)
    initcode_len = len(initcode_bytes)

    factory_code = Op.MSTORE(
        0, Op.PUSH32(initcode_bytes.rjust(32, b"\x00"))
    ) + Op.CREATE(value=0, offset=32 - initcode_len, size=initcode_len)

    factory = pre.deploy_contract(factory_code)

    tx = Transaction(
        sender=sender,
        to=factory,
        value=0,
        gas_limit=200_000,
        expected_receipt=TransactionReceipt(logs=[]),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.parametrize(
    "to_self",
    [
        pytest.param(True, id="to_self"),
        pytest.param(False, id="to_other"),
    ],
)
def test_selfdestruct_same_tx_via_call(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    to_self: bool,
) -> None:
    """
    Test selfdestruct log for contract created via CREATE then called.

    All existing same-tx tests use initcode selfdestruct. This tests the
    create-then-call path: factory CREATEs a contract with deployed runtime
    code, then CALLs it to trigger SELFDESTRUCT. Contract is still in
    created_accounts.

    Expected logs:
    - to_self: transfer_log(factory, created, 2000) +
               selfdestruct_log(created, 2000)
    - to_other: transfer_log(factory, created, 2000) +
                transfer_log(created, beneficiary, 2000)
    """
    contract_balance = 2000
    beneficiary = pre.deploy_contract(Op.STOP)

    if to_self:
        runtime_code = Op.SELFDESTRUCT(Op.ADDRESS)
    else:
        runtime_code = Op.SELFDESTRUCT(beneficiary)

    initcode = Initcode(deploy_code=runtime_code)
    initcode_len = len(initcode)

    factory_code = (
        Om.MSTORE(initcode, 0)
        + Op.SSTORE(
            0, Op.CREATE(value=contract_balance, offset=0, size=initcode_len)
        )
        + Op.CALL(gas=100_000, address=Op.SLOAD(0), value=0)
    )

    factory = pre.deploy_contract(factory_code, balance=contract_balance)
    created_address = compute_create_address(address=factory, nonce=1)

    if to_self:
        expected_logs = [
            transfer_log(factory, created_address, contract_balance),
            selfdestruct_log(created_address, contract_balance),
        ]
        post = {}
    else:
        expected_logs = [
            transfer_log(factory, created_address, contract_balance),
            transfer_log(created_address, beneficiary, contract_balance),
        ]
        post = {beneficiary: Account(balance=contract_balance)}

    tx = Transaction(
        sender=sender,
        to=factory,
        value=0,
        gas_limit=300_000,
        expected_receipt=TransactionReceipt(logs=expected_logs),
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


def test_finalization_selfdestruct_logs(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
) -> None:
    """
    Test Selfdestruct logs at finalization for post-selfdestruct balance.

    Multiple contracts selfdestruct then receive ETH. At finalization, logs
    are emitted in lexicographical order of contract addresses.
    """
    beneficiary = pre.deploy_contract(Op.STOP)

    runtime = Op.SELFDESTRUCT(beneficiary)
    initcode = Initcode(deploy_code=runtime)
    initcode_len = len(initcode)

    # C1 and C2 selfdestruct to addresses in calldata
    c1_code = Op.SELFDESTRUCT(Op.CALLDATALOAD(0))
    c2_code = Op.SELFDESTRUCT(Op.CALLDATALOAD(0))
    c1 = pre.deploy_contract(c1_code, balance=100)
    c2 = pre.deploy_contract(c2_code, balance=200)

    # Factory: CREATE A, CREATE B, CALL A, CALL B, then CALL C1/C2 to send ETH
    factory_code = (
        Om.MSTORE(initcode, 0)
        # CREATE A (nonce 1) and B (nonce 2)
        + Op.SSTORE(0, Op.CREATE(value=1000, offset=0, size=initcode_len))
        + Op.SSTORE(1, Op.CREATE(value=2000, offset=0, size=initcode_len))
        # CALL A and B to trigger selfdestructs
        + Op.CALL(gas=100_000, address=Op.SLOAD(0), value=0)
        + Op.CALL(gas=100_000, address=Op.SLOAD(1), value=0)
        # CALL C1 with A's address, CALL C2 with B's address
        + Op.MSTORE(0, Op.SLOAD(0))
        + Op.CALL(gas=100_000, address=c1, args_offset=0, args_size=32)
        + Op.MSTORE(0, Op.SLOAD(1))
        + Op.CALL(gas=100_000, address=c2, args_offset=0, args_size=32)
    )

    factory = pre.deploy_contract(factory_code, balance=3000)
    addr_a = compute_create_address(address=factory, nonce=1)
    addr_b = compute_create_address(address=factory, nonce=2)

    # Sort addresses for expected finalization log order
    sorted_addrs = sorted([addr_a, addr_b])
    amounts = {addr_a: 100, addr_b: 200}

    # Execution logs: CREATE A, CREATE B, SD A, SD B, C1->A, C2->B
    execution_logs = [
        transfer_log(factory, addr_a, 1000),
        transfer_log(factory, addr_b, 2000),
        transfer_log(addr_a, beneficiary, 1000),
        transfer_log(addr_b, beneficiary, 2000),
        transfer_log(c1, addr_a, 100),
        transfer_log(c2, addr_b, 200),
    ]
    # Finalization logs in sorted address order
    finalization_logs = [
        selfdestruct_log(addr, amounts[addr]) for addr in sorted_addrs
    ]

    tx = Transaction(
        sender=sender,
        to=factory,
        value=0,
        gas_limit=1_000_000,
        expected_receipt=TransactionReceipt(
            logs=execution_logs + finalization_logs
        ),
    )

    post = {
        addr_a: Account.NONEXISTENT,
        addr_b: Account.NONEXISTENT,
        beneficiary: Account(balance=3000),
        c1: Account(balance=0),
        c2: Account(balance=0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
