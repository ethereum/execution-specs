"""
abstract: Tests for transaction validity with [EIP-7981: Increase Access List Cost](https://eips.ethereum.org/EIPS/eip-7981).
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
)

from .spec import ref_spec_7981

REFERENCE_SPEC_GIT_PATH = ref_spec_7981.git_path
REFERENCE_SPEC_VERSION = ref_spec_7981.version

pytestmark = pytest.mark.valid_at("EIP7981")


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
    - Floor cost including access list tokens
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


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
    Test that the floor cost validation includes access list tokens.

    According to EIP-7981:
    - Any transaction with a gas limit below the floor cost is invalid
    - Floor cost = TX_BASE_COST + TOTAL_COST_FLOOR_PER_TOKEN *
      total_floor_data_tokens
    - total_floor_data_tokens =
      floor_tokens_in_calldata + floor_tokens_in_access_list
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


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
    """
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
            [AccessList(address=Address(0), storage_keys=[Hash(0)] * 100)],
            Bytes(b"\x00" * 1000),
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
                    * 50,
                )
            ],
            Bytes(b"\xff" * 500),
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
    tx: Transaction,
) -> None:
    """
    Test floor cost calculation with mixed zero and non-zero bytes.

    This ensures floor gas uses floor token counting:
    - Each data byte contributes 4 floor tokens
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


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
