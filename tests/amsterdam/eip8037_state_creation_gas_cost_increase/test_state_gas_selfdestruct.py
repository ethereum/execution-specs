"""
Test SELFDESTRUCT state gas charging under EIP-8037.

SELFDESTRUCT charges new-account state gas of state gas when the
beneficiary account does not exist AND the originating contract has
a nonzero balance. No state gas is charged when the beneficiary
already exists or the originator has zero balance.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_new_beneficiary_charges_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SELFDESTRUCT to non-existent beneficiary charges state gas.

    When the beneficiary does not exist and the originator has nonzero
    balance, SELFDESTRUCT charges new-account state gas for
    creating the new beneficiary account.
    """
    gas_costs = fork.gas_costs()
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    new_account_state_gas = gas_costs.GAS_NEW_ACCOUNT

    # Non-existent beneficiary
    beneficiary = 0xDEAD

    contract = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary),
        balance=1,
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + new_account_state_gas,
        sender=pre.fund_eoa(),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_existing_beneficiary_no_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SELFDESTRUCT to existing beneficiary charges no state gas.

    When the beneficiary already exists, no new account is created
    and no state gas is charged.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    beneficiary = pre.fund_eoa(amount=0)

    contract = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary),
        balance=1,
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_zero_balance_no_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SELFDESTRUCT with zero balance charges no state gas.

    When the originating contract has zero balance, no value is
    transferred, so no new account is created even if the beneficiary
    does not exist.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    # Non-existent beneficiary but contract has zero balance
    beneficiary = 0xDEAD

    contract = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary),
        balance=0,
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_state_gas_from_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SELFDESTRUCT state gas drawn from reservoir.

    Provide gas above TX_MAX_GAS_LIMIT so the new account state gas
    for the non-existent beneficiary is drawn from the reservoir.
    """
    gas_costs = fork.gas_costs()
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    new_account_state_gas = gas_costs.GAS_NEW_ACCOUNT

    beneficiary = 0xDEAD

    contract = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary),
        balance=1,
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + new_account_state_gas,
        sender=pre.fund_eoa(),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_to_self_in_create_tx(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SELFDESTRUCT to self in the transaction the contract was created.

    When a contract created in the current transaction SELFDESTRUCTs
    to itself, the balance is burned and the account is deleted. No
    new account state gas is charged since the beneficiary already
    exists.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()

    inner_code = Op.SELFDESTRUCT(Op.ADDRESS)

    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(inner_code), "big")
                << (256 - 8 * len(inner_code)),
            )
            + Op.POP(Op.CREATE(1, 0, len(inner_code)))
        ),
        balance=1,
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap * 2,
        sender=pre.fund_eoa(),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_new_beneficiary_header_gas_used(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify block gas accounting for SELFDESTRUCT to new beneficiary.

    A contract with nonzero balance SELFDESTRUCTs to a non-existent
    beneficiary, charging GAS_NEW_ACCOUNT state gas. The block must
    be accepted with correct 2D gas accounting in the header.
    """
    gas_costs = fork.gas_costs()
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    new_account_state_gas = gas_costs.GAS_NEW_ACCOUNT

    beneficiary = pre.fund_eoa(amount=0)

    storage = Storage()
    inner = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary),
        balance=1,
    )
    caller = pre.deploy_contract(
        code=(
            Op.CALL(gas=100_000, address=inner)
            + Op.SSTORE(storage.store_next(1, "completed"), 1)
        ),
    )

    tx = Transaction(
        to=caller,
        gas_limit=gas_limit_cap + new_account_state_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx]),
        ],
        post={caller: Account(storage=storage)},
    )
