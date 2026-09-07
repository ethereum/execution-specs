"""
Tests for access list cost calculations in [EIP-7981: Increase Access List Cost](https://eips.ethereum.org/EIPS/eip-7981).
"""

import pytest
from execution_testing import (
    AccessList,
    Address,
    Alloc,
    Bytes,
    EIPChecklist,
    Fork,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .helpers import calculate_access_list_floor_tokens
from .spec import ref_spec_7981

REFERENCE_SPEC_GIT_PATH = ref_spec_7981.git_path
REFERENCE_SPEC_VERSION = ref_spec_7981.version

pytestmark = pytest.mark.valid_at("EIP7981")


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type >= 1)
@pytest.mark.parametrize(
    "access_list,expected_floor_tokens",
    [
        pytest.param(
            [AccessList(address=Address(0), storage_keys=[])],
            # 20 bytes total: 20 * 4 = 80 floor tokens
            80,
            id="single_zero_address_no_keys",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                    ),
                    storage_keys=[],
                )
            ],
            # 20 bytes total: 20 * 4 = 80 floor tokens
            80,
            id="single_nonzero_address_no_keys",
        ),
        pytest.param(
            [AccessList(address=Address(0), storage_keys=[Hash(0)])],
            # Total bytes: 20 + 32 = 52, floor tokens: 52 * 4 = 208
            208,
            id="zero_address_zero_key",
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
                    ],
                )
            ],
            # Total bytes: 20 + 32 = 52, floor tokens: 52 * 4 = 208
            208,
            id="nonzero_address_nonzero_key",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(1),
                    storage_keys=[Hash(0), Hash(1), Hash(2)],
                )
            ],
            # Total bytes: 20 + (3 * 32) = 116, floor tokens: 116 * 4 = 464
            464,
            id="one_address_three_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(1), storage_keys=[Hash(0)]),
                AccessList(address=Address(2), storage_keys=[Hash(1)]),
            ],
            # Total bytes: 2 * (20 + 32) = 104, floor tokens: 104 * 4 = 416
            416,
            id="two_addresses_with_keys",
        ),
    ],
)
@pytest.mark.parametrize(
    "to",
    [pytest.param("eoa", id="")],
    indirect=True,
)
def test_access_list_token_calculation(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    tx: Transaction,
    tx_expected_gas_used: int,
    tx_gas_delta: int,
    access_list: list,
    expected_floor_tokens: int,
) -> None:
    """
    Test that access list floor tokens are calculated correctly.

    Every access list byte contributes four floor tokens regardless of
    whether it is zero or non-zero. Verify both the reference helper and
    the fork's floor cost calculator agree with the expected token count.
    """
    assert (
        calculate_access_list_floor_tokens(access_list)
        == expected_floor_tokens
    )

    gas_costs = fork.gas_costs()
    expected_floor_cost = (
        expected_floor_tokens * gas_costs.TX_DATA_TOKEN_FLOOR
        + gas_costs.TX_BASE
        # EIP-2780 anchors the floor on the decomposed intrinsic base; the
        # tx targets a non-self account, adding the recipient-access charge.
        + gas_costs.COLD_ACCOUNT_ACCESS
    )
    actual_floor_cost = fork.transaction_data_floor_cost_calculator()(
        data=b"", access_list=access_list
    )
    assert actual_floor_cost == expected_floor_cost

    tx = tx.copy(gas_limit=tx_expected_gas_used + max(tx_gas_delta, 1000))
    tx.expected_receipt = TransactionReceipt(
        status=1, gas_used=tx_expected_gas_used
    )
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type >= 1)
@pytest.mark.parametrize(
    "access_list,tx_data",
    [
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            Bytes(b"\x01" * 100),
            id="access_list_and_calldata",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(1),
                    storage_keys=[Hash(i) for i in range(10)],
                )
            ],
            Bytes(b"\x00" * 50 + b"\x01" * 50),
            id="large_access_list_mixed_calldata",
        ),
    ],
)
@pytest.mark.parametrize(
    "to",
    [pytest.param("eoa", id="")],
    indirect=True,
)
def test_access_list_floor_cost_with_calldata(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    tx_expected_gas_used: int,
    tx_gas_delta: int,
) -> None:
    """
    Test that the floor cost correctly accounts for both access list
    and calldata tokens.

    According to EIP-7981:
    - total_floor_data_tokens =
      floor_tokens_in_calldata + floor_tokens_in_access_list
    - floor_gas =
      TX_BASE_COST + total_floor_data_tokens * TOTAL_COST_FLOOR_PER_TOKEN
    """
    tx = tx.copy(gas_limit=tx_expected_gas_used + max(tx_gas_delta, 1000))
    tx.expected_receipt = TransactionReceipt(
        status=1, gas_used=tx_expected_gas_used
    )
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type >= 1)
@pytest.mark.parametrize(
    "access_list",
    [
        pytest.param(
            [
                AccessList(
                    address=Address(i),
                    storage_keys=[Hash(j) for j in range(5)],
                )
                for i in range(1, 6)
            ],
            id="five_addresses_five_keys_each",
        ),
    ],
)
@pytest.mark.parametrize(
    "to",
    [pytest.param("eoa", id="")],
    indirect=True,
)
def test_large_access_list_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    tx_expected_gas_used: int,
    tx_gas_delta: int,
) -> None:
    """
    Test gas costs for large access lists.

    With EIP-7981, large access lists should incur:
    1. Storage access costs (per-address and per-key charges, priced
       at the fork's cold access costs since EIP-8038)
    2. Data footprint costs (16 per floor token)
    """
    tx = tx.copy(gas_limit=tx_expected_gas_used + max(tx_gas_delta, 1000))
    tx.expected_receipt = TransactionReceipt(
        status=1, gas_used=tx_expected_gas_used
    )
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type >= 1)
@pytest.mark.parametrize(
    "access_list",
    [
        pytest.param(
            [
                AccessList(address=Address(1), storage_keys=[Hash(0)]),
                AccessList(address=Address(1), storage_keys=[Hash(0)]),
            ],
            id="duplicate_access_list_entries",
        ),
    ],
)
@pytest.mark.parametrize(
    "to",
    [pytest.param("eoa", id="")],
    indirect=True,
)
def test_duplicate_access_list_entries(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    tx_expected_gas_used: int,
    tx_gas_delta: int,
) -> None:
    """
    Test that duplicate access list entries are charged multiple times.

    According to EIP-2930, non-unique addresses and storage keys are allowed
    and charged multiple times. EIP-7981 should maintain this behavior.
    """
    tx = tx.copy(gas_limit=tx_expected_gas_used + max(tx_gas_delta, 1000))
    tx.expected_receipt = TransactionReceipt(
        status=1, gas_used=tx_expected_gas_used
    )
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type in (1, 2))
@pytest.mark.parametrize(
    "data",
    [
        pytest.param(b"\x00" * 400, id="zero_calldata"),
        pytest.param(b"\xff" * 400, id="nonzero_calldata"),
    ],
)
@pytest.mark.parametrize(
    "execution_dominates",
    [
        pytest.param(False, id="floor_dominates"),
        pytest.param(True, id="execution_dominates"),
    ],
)
def test_access_list_data_cost_with_execution(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    data: bytes,
    execution_dominates: bool,
) -> None:
    """Charge the full access list surcharge on either side of the maximum."""
    access_list = [
        AccessList(address=Address(1), storage_keys=[Hash(0), Hash(1)])
    ]
    gas_costs = fork.gas_costs()
    surcharge = (
        calculate_access_list_floor_tokens(access_list)
        * gas_costs.TX_DATA_TOKEN_FLOOR
    )
    # Keep execution free of storage changes and refunds so the two
    # gas-used branches can be compared directly.
    code = (Op.PUSH0 + Op.POP) * (10_000 if execution_dominates else 0)
    contract = pre.deploy_contract(code + Op.STOP)
    execution_gas = code.gas_cost(fork)

    intrinsic_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_without_access_list = intrinsic_calculator(
        calldata=data,
        return_cost_deducted_prior_execution=True,
    )
    # The subject is the access-list schedule: derive the surcharge
    # separately from the calculator's handling of access lists.
    entry_charges = (
        gas_costs.TX_ACCESS_LIST_ADDRESS
        + 2 * gas_costs.TX_ACCESS_LIST_STORAGE_KEY
    )
    execution_cost = (
        intrinsic_without_access_list + entry_charges + execution_gas
    )
    calldata_floor = fork.transaction_data_floor_cost_calculator()(data=data)
    assert (execution_cost > calldata_floor) == execution_dominates
    expected_gas_used = max(execution_cost, calldata_floor) + surcharge

    tx = Transaction(
        ty=tx_type,
        sender=pre.fund_eoa(),
        to=contract,
        data=data,
        access_list=access_list,
        # Surplus gas distinguishes actual billing from simply burning
        # a gas limit that happens to equal the expected receipt value.
        gas_limit=expected_gas_used + 1000,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_gas_used
        ),
    )

    state_test(pre=pre, post={}, tx=tx)
