"""Test ACL Transaction Source Code Examples."""

from typing import List

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    AccessList,
    Account,
    Address,
    Alloc,
    CodeGasMeasure,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from ethereum_test_tools import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-2930.md"
REFERENCE_SPEC_VERSION = "c9db53a936c5c9cbe2db32ba0d1b86c4c6e73534"

pytestmark = pytest.mark.valid_from("Berlin")


@pytest.mark.parametrize(
    "account_warm,storage_key_warm",
    [
        (True, True),
        (True, False),
        # (False, True),  Not possible
        (False, False),
    ],
)
def test_account_storage_warm_cold_state(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    account_warm: bool,
    storage_key_warm: bool,
):
    """Test type 1 transaction."""
    env = Environment()
    gas_costs = fork.gas_costs()

    storage_reader_contract = pre.deploy_contract(Op.SLOAD(1) + Op.STOP)
    overhead_cost = (
        gas_costs.G_VERY_LOW * (Op.CALL.popped_stack_items - 1)  # Call stack items
        + gas_costs.G_BASE  # Call gas
        + gas_costs.G_VERY_LOW  # SLOAD Push
    )
    contract_address = pre.deploy_contract(
        CodeGasMeasure(
            code=Op.CALL(address=storage_reader_contract),
            overhead_cost=overhead_cost,
            extra_stack_items=1,
            sstore_key=0,
        )
    )
    expected_gas_cost = 0
    access_list_address = Address(0)
    access_list_storage_key = Hash(0)
    if account_warm:
        expected_gas_cost += gas_costs.G_WARM_ACCOUNT_ACCESS
        access_list_address = storage_reader_contract
    else:
        expected_gas_cost += gas_costs.G_COLD_ACCOUNT_ACCESS
    if storage_key_warm:
        expected_gas_cost += gas_costs.G_WARM_SLOAD
        access_list_storage_key = Hash(1)
    else:
        expected_gas_cost += gas_costs.G_COLD_SLOAD

    access_lists: List[AccessList] = [
        AccessList(
            address=access_list_address,
            storage_keys=[access_list_storage_key],
        ),
    ]

    sender = pre.fund_eoa()

    contract_creation = False
    tx_data = b""

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()

    tx_gas_limit = (
        intrinsic_gas_calculator(
            calldata=tx_data,
            contract_creation=contract_creation,
            access_list=access_lists,
        )
        + 100_000
    )

    tx = Transaction(
        ty=1,
        chain_id=0x01,
        data=tx_data,
        to=contract_address,
        gas_limit=tx_gas_limit,
        access_list=access_lists,
        protected=True,
        sender=sender,
    )

    post = {
        contract_address: Account(
            nonce=1,
            storage={0: expected_gas_cost},
        ),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "access_lists",
    [
        pytest.param(
            [],
            id="empty_access_list",
        ),
        pytest.param(
            [AccessList(address=Address(0), storage_keys=[])],
            id="single_address_multiple_no_storage_keys",
        ),
        pytest.param(
            [AccessList(address=Address(0), storage_keys=[Hash(0)])],
            id="single_address_single_storage_key",
        ),
        pytest.param(
            [AccessList(address=Address(0), storage_keys=[Hash(0), Hash(1)])],
            id="single_address_multiple_storage_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(0), storage_keys=[Hash(0), Hash(1)]),
                AccessList(address=Address(1), storage_keys=[]),
            ],
            id="multiple_addresses_second_address_no_storage_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(0), storage_keys=[Hash(0), Hash(1)]),
                AccessList(address=Address(1), storage_keys=[Hash(0)]),
            ],
            id="multiple_addresses_second_address_single_storage_key",
        ),
        pytest.param(
            [
                AccessList(address=Address(0), storage_keys=[Hash(0), Hash(1)]),
                AccessList(address=Address(1), storage_keys=[Hash(0), Hash(1)]),
            ],
            id="multiple_addresses_second_address_multiple_storage_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(0), storage_keys=[]),
                AccessList(address=Address(1), storage_keys=[Hash(0), Hash(1)]),
            ],
            id="multiple_addresses_first_address_no_storage_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(0), storage_keys=[Hash(0)]),
                AccessList(address=Address(1), storage_keys=[Hash(0), Hash(1)]),
            ],
            id="multiple_addresses_first_address_single_storage_key",
        ),
        pytest.param(
            [
                AccessList(address=Address(0), storage_keys=[]),
                AccessList(address=Address(1), storage_keys=[]),
            ],
            id="repeated_address_no_storage_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(0), storage_keys=[Hash(0)]),
                AccessList(address=Address(0), storage_keys=[Hash(1)]),
            ],
            id="repeated_address_single_storage_key",
        ),
        pytest.param(
            [
                AccessList(address=Address(0), storage_keys=[Hash(0), Hash(1)]),
                AccessList(address=Address(0), storage_keys=[Hash(0), Hash(1)]),
            ],
            id="repeated_address_multiple_storage_keys",
        ),
    ],
)
@pytest.mark.parametrize(
    "enough_gas",
    [
        pytest.param(True, id="enough_gas"),
        pytest.param(False, id="not_enough_gas", marks=pytest.mark.exception_test),
    ],
)
def test_transaction_intrinsic_gas_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    access_lists: List[AccessList],
    enough_gas: bool,
):
    """Test type 1 transaction."""
    env = Environment()

    contract_start_balance = 3
    contract_address = pre.deploy_contract(
        Op.STOP,
        balance=contract_start_balance,
    )
    sender = pre.fund_eoa()
    tx_value = 1
    pre.fund_address(sender, tx_value)

    contract_creation = False
    tx_data = b""

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()

    tx_exception = None
    tx_gas_limit = intrinsic_gas_calculator(
        calldata=tx_data,
        contract_creation=contract_creation,
        access_list=access_lists,
    )
    if not enough_gas:
        tx_gas_limit -= 1
        tx_exception = TransactionException.INTRINSIC_GAS_TOO_LOW

    tx = Transaction(
        ty=1,
        chain_id=0x01,
        data=tx_data,
        to=contract_address,
        value=tx_value,
        gas_limit=tx_gas_limit,
        access_list=access_lists,
        protected=True,
        sender=sender,
        error=tx_exception,
    )

    post = {
        contract_address: Account(
            balance=contract_start_balance + 1 if enough_gas else contract_start_balance,
            nonce=1,
        ),
        sender: Account(
            nonce=1 if enough_gas else 0,
        ),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)
