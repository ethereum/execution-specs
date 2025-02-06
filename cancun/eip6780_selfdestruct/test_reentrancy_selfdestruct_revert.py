"""
Suicide scenario requested test
https://github.com/ethereum/tests/issues/1325.
"""

from typing import SupportsBytes

import pytest

from ethereum_test_forks import Cancun, Fork
from ethereum_test_tools import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytecode,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6780.md"
REFERENCE_SPEC_VERSION = "2f8299df31bb8173618901a03a8366a3183479b0"


@pytest.fixture
def selfdestruct_contract_bytecode(selfdestruct_recipient_address: Address) -> Bytecode:
    """Contract code that performs a SELFDESTRUCT operation."""
    return Op.SELFDESTRUCT(selfdestruct_recipient_address)


@pytest.fixture
def selfdestruct_contract_init_balance() -> int:  # noqa: D103
    return 300_000


@pytest.fixture
def selfdestruct_contract_address(
    pre: Alloc, selfdestruct_contract_bytecode: Bytecode, selfdestruct_contract_init_balance: int
) -> Address:
    """Address of the selfdestruct contract."""
    return pre.deploy_contract(
        code=selfdestruct_contract_bytecode, balance=selfdestruct_contract_init_balance
    )


@pytest.fixture
def executor_contract_bytecode(
    first_suicide: Op,
    revert_contract_address: Address,
    selfdestruct_contract_address: Address,
) -> Bytecode:
    """Contract code that performs a selfdestruct call then revert."""
    return (
        Op.SSTORE(1, first_suicide(address=selfdestruct_contract_address, value=0))
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
    second_suicide: Op,
    selfdestruct_contract_address: Address,
) -> Bytecode:
    """Contract code that performs a call and then reverts."""
    call_op = second_suicide(address=selfdestruct_contract_address, value=100)
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
    return pre.deploy_contract(revert_contract_bytecode, balance=revert_contract_init_balance)


@pytest.mark.valid_from("Paris")
@pytest.mark.parametrize("first_suicide", [Op.CALL, Op.CALLCODE, Op.DELEGATECALL])
@pytest.mark.parametrize("second_suicide", [Op.CALL, Op.CALLCODE, Op.DELEGATECALL])
def test_reentrancy_selfdestruct_revert(
    pre: Alloc,
    env: Environment,
    sender: EOA,
    fork: Fork,
    first_suicide: Op,
    second_suicide: Op,
    state_test: StateTestFiller,
    selfdestruct_contract_bytecode: Bytecode,
    selfdestruct_contract_address: Address,
    selfdestruct_contract_init_balance: int,
    revert_contract_address: Address,
    revert_contract_init_balance: int,
    executor_contract_address: Address,
    executor_contract_init_balance: int,
    selfdestruct_recipient_address: Address,
):
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
        revert_contract_address: Account(balance=revert_contract_init_balance, storage={}),
    }

    if first_suicide in [Op.CALLCODE, Op.DELEGATECALL]:
        if fork >= Cancun:
            # On Cancun even callcode/delegatecall does not remove the account, so the value remain
            post[executor_contract_address] = Account(
                storage={
                    0x01: 0x01,  # First call to contract S->suicide success
                    0x02: 0x00,  # Second call to contract S->suicide reverted
                    0x03: 16,  # Reverted value to check that revert really worked
                },
            )
        else:
            # Callcode executed first suicide from sender. sender is deleted
            post[executor_contract_address] = Account.NONEXISTENT  # type: ignore

        # Original suicide account remains in state
        post[selfdestruct_contract_address] = Account(
            balance=selfdestruct_contract_init_balance, storage={}
        )
        # Suicide destination
        post[selfdestruct_recipient_address] = Account(
            balance=executor_contract_init_balance,
        )

    # On Cancun suicide no longer destroys the account from state, just cleans the balance
    if first_suicide in [Op.CALL]:
        post[executor_contract_address] = Account(
            storage={
                0x01: 0x01,  # First call to contract S->suicide success
                0x02: 0x00,  # Second call to contract S->suicide reverted
                0x03: 16,  # Reverted value to check that revert really worked
            },
        )
        if fork >= Cancun:
            # On Cancun suicide does not remove the account, just sends the balance
            post[selfdestruct_contract_address] = Account(
                balance=0, code=selfdestruct_contract_bytecode, storage={}
            )
        else:
            post[selfdestruct_contract_address] = Account.NONEXISTENT  # type: ignore

        # Suicide destination
        post[selfdestruct_recipient_address] = Account(
            balance=selfdestruct_contract_init_balance,
        )

    tx = Transaction(
        sender=sender,
        to=executor_contract_address,
        gas_limit=500_000,
        value=0,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
