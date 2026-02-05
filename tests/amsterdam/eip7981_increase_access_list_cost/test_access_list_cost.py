"""
abstract: Tests for access list cost calculations in [EIP-7981: Increase Access List Cost](https://eips.ethereum.org/EIPS/eip-7981).
"""  # noqa: E501

import pytest
from execution_testing import (
    AccessList,
    Address,
    Alloc,
    Bytes,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .helpers import calculate_access_list_tokens
from .spec import ref_spec_7981

REFERENCE_SPEC_GIT_PATH = ref_spec_7981.git_path
REFERENCE_SPEC_VERSION = ref_spec_7981.version

pytestmark = pytest.mark.valid_at("Amsterdam")


@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type >= 1)
@pytest.mark.parametrize(
    "access_list,expected_tokens",
    [
        pytest.param(
            [AccessList(address=Address(0), storage_keys=[])],
            # 20 bytes, all zeros: 20 * 1 = 20 tokens
            20,
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
            # 20 bytes, all non-zero: 20 * 4 = 80 tokens
            80,
            id="single_nonzero_address_no_keys",
        ),
        pytest.param(
            [AccessList(address=Address(0), storage_keys=[Hash(0)])],
            # Address: 20 zeros = 20 tokens
            # Storage key: 32 zeros = 32 tokens
            # Total: 52 tokens
            52,
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
            # Address: 20 non-zero = 80 tokens
            # Storage key: 32 non-zero = 128 tokens
            # Total: 208 tokens
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
            # Address: 19 zeros + 1 non-zero = 19 + 4 = 23 tokens
            # Key 0: 32 zeros = 32 tokens
            # Key 1: 31 zeros + 1 non-zero = 31 + 4 = 35 tokens
            # Key 2: 31 zeros + 1 non-zero = 31 + 4 = 35 tokens
            # Total: 23 + 32 + 35 + 35 = 125 tokens
            125,
            id="one_address_three_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(1), storage_keys=[Hash(0)]),
                AccessList(address=Address(2), storage_keys=[Hash(1)]),
            ],
            # Address 1: 19 zeros + 1 non-zero = 23 tokens
            # Key 0: 32 zeros = 32 tokens
            # Address 2: 19 zeros + 1 non-zero = 23 tokens
            # Key 1: 31 zeros + 1 non-zero = 35 tokens
            # Total: 23 + 32 + 23 + 35 = 113 tokens
            113,
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
    pre: Alloc,
    tx: Transaction,
    access_list: list,
    expected_tokens: int,
) -> None:
    """
    Test that access list tokens are calculated correctly.

    This test verifies the token counting mechanism:
    - Zero bytes contribute 1 token each
    - Non-zero bytes contribute 4 tokens each
    """
    # Verify our helper calculates tokens correctly
    calculated_tokens = calculate_access_list_tokens(access_list)
    assert calculated_tokens == expected_tokens, (
        f"Expected {expected_tokens} tokens, got {calculated_tokens}"
    )

    # The transaction should be valid with correct gas
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
    - total_data_tokens = tokens_in_calldata + tokens_in_access_list
    - floor_gas = TX_BASE_COST + total_data_tokens * TOTAL_COST_FLOOR_PER_TOKEN
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
    2. Data footprint costs (10 per token)
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
