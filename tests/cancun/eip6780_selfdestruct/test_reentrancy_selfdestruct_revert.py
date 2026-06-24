"""
Self-destruct scenario requested test
https://github.com/ethereum/tests/issues/1325.
"""

from typing import SupportsBytes

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytecode,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)
from execution_testing.forks import Cancun

from tests.amsterdam.eip7708_eth_transfer_logs.spec import transfer_log

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6780.md"
REFERENCE_SPEC_VERSION = "1b6a0e94cc47e859b9866e570391cf37dc55059a"


@pytest.fixture
def selfdestruct_contract_bytecode(
    selfdestruct_recipient_address: Address,
) -> Bytecode:
    """Contract code that performs a SELFDESTRUCT operation."""
    return Op.SELFDESTRUCT(selfdestruct_recipient_address)


@pytest.fixture
def selfdestruct_contract_init_balance() -> int:  # noqa: D103
    return 300_000


@pytest.fixture
def selfdestruct_contract_address(
    pre: Alloc,
    selfdestruct_contract_bytecode: Bytecode,
    selfdestruct_contract_init_balance: int,
) -> Address:
    """Address of the selfdestruct contract."""
    return pre.deploy_contract(
        code=selfdestruct_contract_bytecode,
        balance=selfdestruct_contract_init_balance,
    )


@pytest.fixture
def executor_contract_bytecode(
    first_selfdestruct: Op,
    revert_contract_address: Address,
    selfdestruct_contract_address: Address,
) -> Bytecode:
    """Contract code that performs a selfdestruct call then revert."""
    return (
        Op.SSTORE(
            1,
            (
                first_selfdestruct(
                    address=selfdestruct_contract_address, value=0
                )
                if first_selfdestruct in [Op.CALL, Op.CALLCODE]
                else first_selfdestruct(address=selfdestruct_contract_address)
            ),
        )
        + Op.SSTORE(2, Op.CALL(address=revert_contract_address))
        + Op.RETURNDATACOPY(0, 0, Op.RETURNDATASIZE())
        + Op.SSTORE(3, Op.MLOAD(0))
    )


@pytest.fixture
def executor_contract_init_storage() -> (  # noqa: D103
    dict[str | bytes | SupportsBytes | int, str | bytes | SupportsBytes | int]
):
    return {0x01: 0x0100, 0x02: 0x0100, 0x03: 0x0100}


@pytest.fixture
def executor_contract_init_balance() -> int:  # noqa: D103
    return 100_000


@pytest.fixture
def executor_contract_address(
    pre: Alloc,
    executor_contract_bytecode: Bytecode,
    executor_contract_init_balance: int,
    executor_contract_init_storage: dict[
        str | bytes | SupportsBytes | int, str | bytes | SupportsBytes | int
    ],
) -> Address:
    """Address of the executor contract."""
    return pre.deploy_contract(
        executor_contract_bytecode,
        balance=executor_contract_init_balance,
        storage=executor_contract_init_storage,
    )


@pytest.fixture
def revert_contract_bytecode(
    second_selfdestruct: Op,
    selfdestruct_contract_address: Address,
) -> Bytecode:
    """Contract code that performs a call and then reverts."""
    call_op = (
        second_selfdestruct(address=selfdestruct_contract_address, value=100)
        if second_selfdestruct in [Op.CALL, Op.CALLCODE]
        else second_selfdestruct(address=selfdestruct_contract_address)
    )
    return Op.MSTORE(0, Op.ADD(15, call_op)) + Op.REVERT(0, 32)


@pytest.fixture
def revert_contract_init_balance() -> int:  # noqa: D103
    return 500_000


@pytest.fixture
def revert_contract_address(
    pre: Alloc,
    revert_contract_bytecode: Bytecode,
    revert_contract_init_balance: int,
) -> Address:
    """Address of the revert contract."""
    return pre.deploy_contract(
        revert_contract_bytecode, balance=revert_contract_init_balance
    )


@pytest.mark.valid_from("Paris")
@pytest.mark.parametrize(
    "first_selfdestruct", [Op.CALL, Op.CALLCODE, Op.DELEGATECALL]
)
@pytest.mark.parametrize(
    "second_selfdestruct", [Op.CALL, Op.CALLCODE, Op.DELEGATECALL]
)
def test_reentrancy_selfdestruct_revert(
    pre: Alloc,
    sender: EOA,
    fork: Fork,
    first_selfdestruct: Op,
    second_selfdestruct: Op,
    state_test: StateTestFiller,
    selfdestruct_contract_bytecode: Bytecode,
    selfdestruct_contract_address: Address,
    selfdestruct_contract_init_balance: int,
    revert_contract_address: Address,
    revert_contract_init_balance: int,
    executor_contract_address: Address,
    executor_contract_init_balance: int,
    selfdestruct_recipient_address: Address,
) -> None:
    """
    Suicide reentrancy scenario.

    Call|Callcode|Delegatecall the contract S.
    S self destructs.
    Call the revert proxy contract R.
    R Calls|Callcode|Delegatecall S.
    S self destructs (for the second time).
    R reverts (including the effects of the second selfdestruct).
    It is expected the S is self destructed after the transaction.
    """
    post = {
        # Second caller unchanged as call gets reverted
        revert_contract_address: Account(
            balance=revert_contract_init_balance, storage={}
        ),
    }

    if first_selfdestruct in [Op.CALLCODE, Op.DELEGATECALL]:
        if fork >= Cancun:
            # On Cancun even callcode/delegatecall does not remove the account,
            # so the value remain
            post[executor_contract_address] = Account(
                storage={
                    0x01: 0x01,  # 1st call to contract S->selfdestruct success
                    0x02: 0x00,  # 2nd call to contract S->selfdestruct revert
                    0x03: 16,  # Reverted value to check that revert really
                    # worked
                },
            )
        else:
            # Callcode executed first selfdestruct from sender.
            # Sender is deleted.
            post[executor_contract_address] = Account.NONEXISTENT  # type: ignore

        # Original selfdestruct account remains in state
        post[selfdestruct_contract_address] = Account(
            balance=selfdestruct_contract_init_balance, storage={}
        )
        # Suicide destination
        post[selfdestruct_recipient_address] = Account(
            balance=executor_contract_init_balance,
        )

    # On Cancun selfdestruct no longer destroys the account from state, just
    # cleans the balance
    if first_selfdestruct in [Op.CALL]:
        post[executor_contract_address] = Account(
            storage={
                0x01: 0x01,  # First call to contract S->selfdestruct success
                0x02: 0x00,  # Second call to contract S->selfdestruct reverted
                0x03: 16,  # Reverted value to check that revert really worked
            },
        )
        if fork >= Cancun:
            # On Cancun selfdestruct does not remove the account, just sends
            # the balance
            post[selfdestruct_contract_address] = Account(
                balance=0, code=selfdestruct_contract_bytecode, storage={}
            )
        else:
            post[selfdestruct_contract_address] = Account.NONEXISTENT  # type: ignore

        # Suicide destination
        post[selfdestruct_recipient_address] = Account(
            balance=selfdestruct_contract_init_balance,
        )

    # Under EIP-7708 the first SELFDESTRUCT emits a Transfer log to the
    # recipient; the second SELFDESTRUCT happens inside the reverted frame so
    # its logs are discarded. For CALL the transfer is from S; for
    # CALLCODE/DELEGATECALL the code runs in executor's context, so the
    # transfer is from executor.
    expected_receipt = None
    if fork.is_eip_enabled(7708):
        if first_selfdestruct == Op.CALL:
            expected_logs = [
                transfer_log(
                    selfdestruct_contract_address,
                    selfdestruct_recipient_address,
                    selfdestruct_contract_init_balance,
                )
            ]
        elif first_selfdestruct in [Op.CALLCODE, Op.DELEGATECALL]:
            expected_logs = [
                transfer_log(
                    executor_contract_address,
                    selfdestruct_recipient_address,
                    executor_contract_init_balance,
                )
            ]
        else:
            raise RuntimeError(
                f"Unexpected opcode for test: {first_selfdestruct}"
            )
        expected_receipt = TransactionReceipt(logs=expected_logs)

    tx = Transaction(
        sender=sender,
        to=executor_contract_address,
        expected_receipt=expected_receipt,
    )

    state_test(pre=pre, post=post, tx=tx)
