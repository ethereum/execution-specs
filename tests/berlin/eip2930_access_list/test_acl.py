"""Test ACL Transaction Source Code Examples."""

from typing import List

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    CodeGasMeasure,
    Environment,
    Fork,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
)

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
) -> None:
    """Test type 1 transaction."""
    env = Environment()

    storage_reader_contract = pre.deploy_contract(Op.SLOAD(1) + Op.STOP)
    # Overhead: PUSH args for CALL (popped_stack_items - 1)
    # + GAS opcode + PUSH for SLOAD
    overhead_cost = (
        Op.PUSH1(0) * (Op.CALL.popped_stack_items - 1)
        + Op.GAS
        + Op.PUSH1(0)  # SLOAD push
    ).gas_cost(fork)
    contract_address = pre.deploy_contract(
        CodeGasMeasure(
            code=Op.CALL(address=storage_reader_contract),
            overhead_cost=overhead_cost,
            extra_stack_items=1,
            sstore_key=0,
        )
    )
    access_list_address = Address(0)
    access_list_storage_key = Hash(0)
    # Expected gas: CALL access cost + SLOAD cost
    expected_gas_cost = Op.CALL(address_warm=account_warm).gas_cost(
        fork
    ) + Op.SLOAD(key_warm=storage_key_warm).gas_cost(fork)
    if account_warm:
        access_list_address = storage_reader_contract
    if storage_key_warm:
        access_list_storage_key = Hash(1)

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
        data=tx_data,
        to=contract_address,
        gas_limit=tx_gas_limit,
        access_list=access_lists,
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
                AccessList(
                    address=Address(0), storage_keys=[Hash(0), Hash(1)]
                ),
                AccessList(address=Address(1), storage_keys=[]),
            ],
            id="multiple_addresses_second_address_no_storage_keys",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(0), storage_keys=[Hash(0), Hash(1)]
                ),
                AccessList(address=Address(1), storage_keys=[Hash(0)]),
            ],
            id="multiple_addresses_second_address_single_storage_key",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(0), storage_keys=[Hash(0), Hash(1)]
                ),
                AccessList(
                    address=Address(1), storage_keys=[Hash(0), Hash(1)]
                ),
            ],
            id="multiple_addresses_second_address_multiple_storage_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(0), storage_keys=[]),
                AccessList(
                    address=Address(1), storage_keys=[Hash(0), Hash(1)]
                ),
            ],
            id="multiple_addresses_first_address_no_storage_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(0), storage_keys=[Hash(0)]),
                AccessList(
                    address=Address(1), storage_keys=[Hash(0), Hash(1)]
                ),
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
                AccessList(
                    address=Address(0), storage_keys=[Hash(0), Hash(1)]
                ),
                AccessList(
                    address=Address(0), storage_keys=[Hash(0), Hash(1)]
                ),
            ],
            id="repeated_address_multiple_storage_keys",
        ),
    ],
)
@pytest.mark.parametrize(
    "enough_gas",
    [
        pytest.param(True, id="enough_gas"),
        pytest.param(
            False, id="not_enough_gas", marks=pytest.mark.exception_test
        ),
    ],
)
@pytest.mark.json_loader
def test_transaction_intrinsic_gas_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    access_lists: List[AccessList],
    enough_gas: bool,
) -> None:
    """Test type 1 transaction."""
    env = Environment()

    contract_start_balance = 3
    contract_address = pre.deploy_contract(
        Op.STOP,
        balance=contract_start_balance,
    )
    sender = pre.fund_eoa()
    tx_value = 1

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
        data=tx_data,
        to=contract_address,
        value=tx_value,
        gas_limit=tx_gas_limit,
        access_list=access_lists,
        sender=sender,
        error=tx_exception,
    )

    post = {
        contract_address: Account(
            balance=contract_start_balance + 1
            if enough_gas
            else contract_start_balance,
            nonce=1,
        ),
        sender: Account(
            nonce=1 if enough_gas else 0,
        ),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


def test_repeated_address_acl(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Tests that slots are warmed correctly in an access list that has the same
    address repeated more than once, each time with different slots.

    Difference with other ACL tests is that we actually try to
    access both slots at runtime. We also measure the gas cost
    of each access in order to make debugging easier.
    """
    sender = pre.fund_eoa()

    # Cost of pushing SLOAD args
    sload_push_cost = (Op.PUSH1(0) * len(Op.SLOAD.kwargs)).gas_cost(fork)

    sload0_measure = CodeGasMeasure(
        code=Op.SLOAD(0),
        overhead_cost=sload_push_cost,
        extra_stack_items=1,  # SLOAD pushes 1 item to the stack
        sstore_key=0,
        stop=False,  # Because it's the first CodeGasMeasure
    )

    sload1_measure = CodeGasMeasure(
        code=Op.SLOAD(1),
        overhead_cost=sload_push_cost,
        extra_stack_items=1,  # SLOAD pushes 1 item to the stack
        sstore_key=1,
    )

    contract = pre.deploy_contract(sload0_measure + sload1_measure)

    tx = Transaction(
        gas_limit=500_000,
        to=contract,
        value=0,
        sender=sender,
        access_list=[
            AccessList(
                address=contract,
                storage_keys=[0],
            ),
            AccessList(
                address=contract,
                storage_keys=[1],
            ),
        ],
    )

    sload_cost = Op.SLOAD(key_warm=True).gas_cost(fork)

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            contract: Account(
                storage={0: sload_cost, 1: sload_cost},
            )
        },
    )
