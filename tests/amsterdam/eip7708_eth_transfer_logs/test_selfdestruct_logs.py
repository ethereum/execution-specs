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

    Selfdestruct log only emitted when created and destroyed in same tx.
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


@pytest.mark.parametrize(
    "contract_balance",
    [
        pytest.param(2000, id="with_balance"),
        pytest.param(0, id="zero_balance"),
    ],
)
def test_selfdestruct_to_self_same_tx(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    contract_balance: int,
) -> None:
    """
    Test selfdestruct-to-self for same-tx created contracts.

    - With balance, SELFDESTRUCT log emitted (burns ETH).
    - No balance, no logs expected.
    """
    initcode = Op.SELFDESTRUCT(Op.ADDRESS)
    initcode_bytes = bytes(initcode)
    initcode_len = len(initcode_bytes)

    factory_code = Op.MSTORE(
        0, Op.PUSH32(initcode_bytes.rjust(32, b"\x00"))
    ) + Op.CREATE(
        value=Op.CALLVALUE, offset=32 - initcode_len, size=initcode_len
    )

    factory = pre.deploy_contract(factory_code)
    created_address = compute_create_address(address=factory, nonce=1)

    if contract_balance > 0:
        expected_logs = [
            transfer_log(sender, factory, contract_balance),
            transfer_log(factory, created_address, contract_balance),
            selfdestruct_log(created_address, contract_balance),
        ]
    else:
        expected_logs = []

    tx = Transaction(
        sender=sender,
        to=factory,
        value=contract_balance,
        gas_limit=200_000,
        expected_receipt=TransactionReceipt(logs=expected_logs),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.parametrize(
    "contract_balance",
    [
        pytest.param(2000, id="with_balance"),
        pytest.param(0, id="zero_balance"),
    ],
)
def test_selfdestruct_to_different_address_same_tx(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    contract_balance: int,
) -> None:
    """
    Test same-tx selfdestruct to different address.

    With balance: Transfer log emitted. Zero balance: no logs.
    """
    beneficiary = pre.deploy_contract(Op.STOP)

    initcode = Op.SELFDESTRUCT(beneficiary)
    initcode_bytes = bytes(initcode)
    initcode_len = len(initcode_bytes)

    factory_code = Op.MSTORE(
        0, Op.PUSH32(initcode_bytes.rjust(32, b"\x00"))
    ) + Op.CREATE(
        value=Op.CALLVALUE, offset=32 - initcode_len, size=initcode_len
    )

    factory = pre.deploy_contract(factory_code)
    created_address = compute_create_address(address=factory, nonce=1)

    if contract_balance > 0:
        expected_logs = [
            transfer_log(sender, factory, contract_balance),
            transfer_log(factory, created_address, contract_balance),
            transfer_log(created_address, beneficiary, contract_balance),
        ]
        post = {beneficiary: Account(balance=contract_balance)}
    else:
        expected_logs = []
        post = {}

    tx = Transaction(
        sender=sender,
        to=factory,
        value=contract_balance,
        gas_limit=200_000,
        expected_receipt=TransactionReceipt(logs=expected_logs),
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "to_self",
    [
        pytest.param(True, id="to_self"),
        pytest.param(False, id="to_other"),
    ],
)
@pytest.mark.parametrize(
    "call_twice,second_call_value",
    [
        pytest.param(True, 1, id="call_twice_with_value"),
        pytest.param(True, 0, id="call_twice"),
        pytest.param(False, 0, id="call_once"),
    ],
)
@pytest.mark.parametrize(
    "transfer_during_create",
    [
        pytest.param(True, id="transfer_during_create"),
        pytest.param(False, id="transfer_during_call"),
    ],
)
def test_selfdestruct_same_tx_via_call(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: EOA,
    to_self: bool,
    call_twice: bool,
    second_call_value: int,
    transfer_during_create: bool,
) -> None:
    """
    Test selfdestruct via CREATE-then-CALL (not initcode selfdestruct).

    Factory CREATEs contract with runtime code, then CALLs to trigger
    SELFDESTRUCT. Contract is still in created_accounts.
    """
    contract_balance = 2000
    beneficiary = pre.deploy_contract(Op.STOP)

    if to_self:
        runtime_code = Op.SELFDESTRUCT(Op.ADDRESS)
    else:
        runtime_code = Op.SELFDESTRUCT(beneficiary)

    initcode = Initcode(deploy_code=runtime_code)
    initcode_len = len(initcode)

    if transfer_during_create:
        create_value = contract_balance
        first_call_value = 0
    else:
        create_value = 0
        first_call_value = contract_balance

    factory_code = (
        Om.MSTORE(initcode, 0)
        + Op.TSTORE(
            0, Op.CREATE(value=create_value, offset=0, size=initcode_len)
        )
        + Op.CALL(gas=100_000, address=Op.TLOAD(0), value=first_call_value)
    )
    if call_twice:
        factory_code += Op.CALL(
            gas=100_000, address=Op.TLOAD(0), value=second_call_value
        )

    factory = pre.deploy_contract(
        factory_code, balance=contract_balance + second_call_value
    )
    created_address = compute_create_address(address=factory, nonce=1)

    if to_self:
        expected_logs = [
            transfer_log(factory, created_address, contract_balance),
            selfdestruct_log(created_address, contract_balance),
        ]
        if call_twice and second_call_value > 0:
            expected_logs += [
                transfer_log(factory, created_address, second_call_value),
                selfdestruct_log(created_address, second_call_value),
            ]
        post = {}
    else:
        expected_logs = [
            transfer_log(factory, created_address, contract_balance),
            transfer_log(created_address, beneficiary, contract_balance),
        ]
        if call_twice and second_call_value > 0:
            expected_logs += [
                transfer_log(factory, created_address, second_call_value),
                transfer_log(created_address, beneficiary, second_call_value),
            ]
        post = {
            beneficiary: Account(balance=contract_balance + second_call_value)
        }

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

    Contracts A and B selfdestruct, then receive ETH via C1/C2's selfdestruct.
    At finalization, A and B emit Selfdestruct logs for their remaining balance
    in lexicographical address order.
    """
    beneficiary = pre.deploy_contract(Op.STOP)

    runtime = Op.SELFDESTRUCT(beneficiary)
    initcode = Initcode(deploy_code=runtime)
    initcode_len = len(initcode)

    c1_code = Op.SELFDESTRUCT(Op.CALLDATALOAD(0))
    c2_code = Op.SELFDESTRUCT(Op.CALLDATALOAD(0))
    c1 = pre.deploy_contract(c1_code, balance=100)
    c2 = pre.deploy_contract(c2_code, balance=200)

    factory_code = (
        Om.MSTORE(initcode, 0)
        + Op.TSTORE(0, Op.CREATE(value=1000, offset=0, size=initcode_len))
        + Op.TSTORE(1, Op.CREATE(value=2000, offset=0, size=initcode_len))
        + Op.CALL(gas=100_000, address=Op.TLOAD(0), value=0)
        + Op.CALL(gas=100_000, address=Op.TLOAD(1), value=0)
        + Op.MSTORE(0, Op.TLOAD(0))
        + Op.CALL(gas=100_000, address=c1, args_offset=0, args_size=32)
        + Op.MSTORE(0, Op.TLOAD(1))
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
