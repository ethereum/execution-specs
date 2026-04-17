"""
abstract: Tests for access list cost calculations in [EIP-7981: Increase Access List Cost](https://eips.ethereum.org/EIPS/eip-7981).
"""  # noqa: E501

import pytest
from execution_testing import (
    AccessList,
    Address,
    Alloc,
    Bytes,
    Fork,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .helpers import calculate_access_list_floor_tokens
from .spec import ref_spec_7981

REFERENCE_SPEC_GIT_PATH = ref_spec_7981.git_path
REFERENCE_SPEC_VERSION = ref_spec_7981.version

pytestmark = pytest.mark.valid_at("EIP7981")


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
        expected_floor_tokens * gas_costs.GAS_TX_DATA_TOKEN_FLOOR
        + gas_costs.GAS_TX_BASE
    )
    actual_floor_cost = fork.transaction_data_floor_cost_calculator()(
        data=b"", access_list=access_list
    )
    assert actual_floor_cost == expected_floor_cost

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


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
    tx_intrinsic_gas_cost_including_floor_data_cost: int,
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
    tx.expected_receipt = TransactionReceipt(
        cumulative_gas_used=tx_intrinsic_gas_cost_including_floor_data_cost
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


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
) -> None:
    """
    Test gas costs for large access lists.

    With EIP-7981, large access lists should incur:
    1. Storage access costs (2400 per address + 1900 per key)
    2. Data footprint costs (16 per floor token)
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


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
) -> None:
    """
    Test that duplicate access list entries are charged multiple times.

    According to EIP-2930, non-unique addresses and storage keys are allowed
    and charged multiple times. EIP-7981 should maintain this behavior.
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )
