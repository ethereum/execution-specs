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
