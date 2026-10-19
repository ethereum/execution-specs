"""
Tests for transaction validity with [EIP-7981: Increase Access List Cost](https://eips.ethereum.org/EIPS/eip-7981).
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Bytes,
    EIPChecklist,
    Fork,
    Hash,
    RecipientType,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
    compute_create_address,
)

from .spec import ref_spec_7981

REFERENCE_SPEC_GIT_PATH = ref_spec_7981.git_path
REFERENCE_SPEC_VERSION = ref_spec_7981.version

pytestmark = [
    pytest.mark.valid_at("EIP7981"),
    pytest.mark.inclusion_test,
]


@EIPChecklist.TransactionType.Test.IntrinsicValidity.GasLimit.Insufficient()
@pytest.mark.exception_test
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type >= 1)
@pytest.mark.parametrize(
    "access_list,tx_gas_delta",
    [
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            -1,
            id="insufficient_gas_by_one",
        ),
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            -100,
            id="insufficient_gas_by_hundred",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(1),
                    storage_keys=[Hash(i) for i in range(10)],
                )
            ],
            -1,
            id="large_access_list_insufficient_gas",
        ),
    ],
)
@pytest.mark.parametrize(
    "to",
    [pytest.param("eoa", id="")],
    indirect=True,
)
def test_insufficient_gas_for_access_list(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
) -> None:
    """
    Test that transactions with insufficient gas for access list costs
    are rejected.

    With EIP-7981, the intrinsic gas must cover:
    - Base transaction cost
    - Calldata costs
    - Access list storage costs
    - Access list data costs (new in EIP-7981)
    - Calldata floor plus the access list data surcharge
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@EIPChecklist.TransactionType.Test.IntrinsicValidity.DataFloorAboveIntrinsicGasCost()
@pytest.mark.exception_test
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type >= 1)
@pytest.mark.parametrize(
    "access_list,tx_data,tx_gas_delta",
    [
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            Bytes(b"\x01" * 1000),
            -1,
            id="large_calldata_and_access_list_insufficient_gas",
        ),
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            Bytes(b"\x00" * 1000),
            -1,
            id="large_zero_calldata_and_access_list_insufficient_gas",
        ),
    ],
)
@pytest.mark.parametrize(
    "to",
    [pytest.param("eoa", id="")],
    indirect=True,
)
def test_floor_cost_validation_with_access_list(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
) -> None:
    """
    Reject a gas limit below the calldata floor plus the access list surcharge.
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@EIPChecklist.TransactionType.Test.IntrinsicValidity.GasLimit.Exact()
@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type >= 1)
@pytest.mark.parametrize(
    "access_list,tx_gas_delta",
    [
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            0,
            id="exact_gas",
        ),
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            1,
            id="one_extra_gas",
        ),
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            1000,
            id="plenty_extra_gas",
        ),
    ],
)
@pytest.mark.parametrize(
    "to",
    [pytest.param("eoa", id="")],
    indirect=True,
)
@pytest.mark.parametrize(
    "tx_gas_surplus",
    [pytest.param(0, id="")],
)
def test_valid_gas_limits_with_access_list(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
) -> None:
    """
    Test that transactions with sufficient gas are valid.

    Tests various gas limit scenarios:
    - Exact intrinsic gas
    - Slightly more than intrinsic gas
    - Much more than intrinsic gas

    The exact case leaves no surplus. For type 4 it also funds the top-frame
    authorization gas, which is charged after intrinsic validation but is
    needed for the transaction to succeed.
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
# A type 4 authorization's top-frame state gas outgrows any moderate
# floor, and the floor does not depend on the transaction type.
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type in (1, 2, 3))
@pytest.mark.parametrize(
    "access_list,tx_data",
    [
        pytest.param(
            [AccessList(address=Address(0), storage_keys=[Hash(0)] * 10)],
            Bytes(b"\x00" * 3000),
            id="zero_heavy_data_and_access_list",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                    ),
                    storage_keys=[
                        Hash(
                            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                        )
                    ]
                    * 5,
                )
            ],
            Bytes(b"\xff" * 2000),
            id="nonzero_heavy_data_and_access_list",
        ),
    ],
)
@pytest.mark.parametrize(
    "to",
    [pytest.param("eoa", id="")],
    indirect=True,
)
@pytest.mark.parametrize(
    "tx_gas_delta",
    [pytest.param(0, id="")],
)
def test_mixed_zero_nonzero_bytes_floor_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx: Transaction,
    access_list: list,
    tx_data: Bytes,
    tx_intrinsic_gas_cost_before_execution: int,
) -> None:
    """
    Bill the floor with every calldata and access list byte at the floor
    rate, whether zero or non-zero.
    """
    floor = fork.transaction_data_floor_cost_calculator()(
        data=tx_data, access_list=access_list
    )
    assert floor > tx_intrinsic_gas_cost_before_execution
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "tx_type,access_list",
    [
        pytest.param(
            0,
            None,
            id="type_0_no_access_list",
        ),
        pytest.param(
            1,
            [],
            id="type_1_empty_access_list",
        ),
        pytest.param(
            2,
            [],
            id="type_2_empty_access_list",
        ),
        pytest.param(
            3,
            [],
            id="type_3_empty_access_list",
        ),
        pytest.param(
            4,
            [],
            id="type_4_empty_access_list",
        ),
    ],
)
@pytest.mark.parametrize(
    "to",
    [pytest.param("eoa", id="")],
    indirect=True,
)
@pytest.mark.parametrize(
    "tx_gas_delta",
    [pytest.param(0, id="")],
)
def test_transactions_without_access_list(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
) -> None:
    """
    Test that transactions without access lists still work correctly.

    EIP-7981 should only affect transactions with non-empty access lists.
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@EIPChecklist.TransactionType.Test.ContractCreation()
@EIPChecklist.TransactionType.Test.IntrinsicValidity.To()
@EIPChecklist.TransactionType.Test.IntrinsicValidity.GasLimit.Insufficient()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type in (1, 2))
@pytest.mark.parametrize(
    "valid",
    [
        pytest.param(True, id="exact_gas"),
        pytest.param(
            False,
            id="insufficient_gas_by_one",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_contract_creation_with_access_list(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    valid: bool,
) -> None:
    """
    Test the intrinsic boundary of a contract-creating transaction with
    an access list.

    The EIP-7981 access list data cost stacks on top of the creation
    intrinsic (creation access and init code charges). The created
    account's state charge is applied at the top frame, after intrinsic
    validation, so the exact-gas arm funds it separately while the
    off-by-one arm pins the intrinsic requirement alone.
    """
    access_list = [
        AccessList(address=Address(1), storage_keys=[Hash(0), Hash(1)])
    ]
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        contract_creation=True,
        access_list=access_list,
        return_cost_deducted_prior_execution=True,
    )
    floor_gas = fork.transaction_data_floor_cost_calculator()(
        data=b"", access_list=access_list, contract_creation=True
    )
    assert floor_gas <= intrinsic_gas

    sender = pre.fund_eoa()
    post: dict = {}
    if valid:
        gas_limit = intrinsic_gas + fork.transaction_top_frame_state_gas(
            contract_creation=True
        )
        error = None
        created = compute_create_address(address=sender, nonce=sender.nonce)
        post[created] = Account(nonce=1, code=b"")
    else:
        gas_limit = intrinsic_gas - 1
        error = TransactionException.INTRINSIC_GAS_TOO_LOW

    tx = Transaction(
        ty=tx_type,
        sender=sender,
        to=None,
        access_list=access_list,
        gas_limit=gas_limit,
        error=error,
    )

    state_test(
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "value,balance_delta",
    [
        pytest.param(
            0,
            -1,
            id="value_zero_insufficient_balance",
            marks=[
                pytest.mark.exception_test,
                EIPChecklist.TransactionType.Test.IntrinsicValidity.ValueZeroInsufficientBalance(),
            ],
        ),
        pytest.param(
            0,
            0,
            id="value_zero_sufficient_balance",
            marks=EIPChecklist.TransactionType.Test.IntrinsicValidity.ValueZeroSufficientBalance(),
        ),
        pytest.param(
            1,
            -1,
            id="value_non_zero_insufficient_balance",
            marks=[
                pytest.mark.exception_test,
                EIPChecklist.TransactionType.Test.IntrinsicValidity.ValueNonZeroInsufficientBalance(),
            ],
        ),
        pytest.param(
            1,
            0,
            id="value_non_zero_sufficient_balance",
            marks=EIPChecklist.TransactionType.Test.IntrinsicValidity.ValueNonZeroSufficientBalance(),
        ),
    ],
)
@pytest.mark.parametrize(
    "tx_type",
    [pytest.param(1, id="type_1"), pytest.param(2, id="type_2")],
)
def test_access_list_sender_balance_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    value: int,
    balance_delta: int,
) -> None:
    """Fund the surcharged gas limit plus value exactly, or one wei short."""
    recipient = pre.fund_eoa(amount=1)
    access_list = [AccessList(address=Address(1), storage_keys=[Hash(0)])]
    # With no calldata the intrinsic side binds, and an existing recipient
    # keeps the value transfer free of state gas, so the exact intrinsic
    # cost is also the gas used.
    gas_limit = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list,
        sends_value=value > 0,
        recipient_type=RecipientType.EOA,
    )
    gas_price = 10
    sender = pre.fund_eoa(amount=gas_limit * gas_price + value + balance_delta)
    if tx_type == 1:
        fee_args: dict = {"gas_price": gas_price}
    else:
        fee_args = {
            "max_fee_per_gas": gas_price,
            "max_priority_fee_per_gas": gas_price,
        }
    if balance_delta >= 0:
        error = None
        expected_receipt = TransactionReceipt(status=1, gas_used=gas_limit)
        post = {
            sender: Account(nonce=1, balance=0),
            recipient: Account(balance=1 + value),
        }
    else:
        error = TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
        expected_receipt = None
        post = {}
    tx = Transaction(
        ty=tx_type,
        sender=sender,
        to=recipient,
        value=value,
        gas_limit=gas_limit,
        access_list=access_list,
        error=error,
        expected_receipt=expected_receipt,
        **fee_args,
    )
    state_test(pre=pre, post=post, tx=tx)
