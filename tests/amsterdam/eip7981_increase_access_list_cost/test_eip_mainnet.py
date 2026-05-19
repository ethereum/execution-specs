"""
abstract: Crafted tests for mainnet of [EIP-7981: Increase Access List Cost](https://eips.ethereum.org/EIPS/eip-7981).
"""  # noqa: E501

import pytest
from execution_testing import (
    AccessList,
    Address,
    Alloc,
    Hash,
    StateTestFiller,
    Transaction,
)

from .spec import ref_spec_7981

REFERENCE_SPEC_GIT_PATH = ref_spec_7981.git_path
REFERENCE_SPEC_VERSION = ref_spec_7981.version

pytestmark = [pytest.mark.valid_at("EIP7981"), pytest.mark.mainnet]


@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type >= 1)
@pytest.mark.parametrize(
    "access_list",
    [
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            id="single_address_single_key",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(1),
                    storage_keys=[Hash(0), Hash(1), Hash(2)],
                )
            ],
            id="single_address_multiple_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(1), storage_keys=[Hash(0)]),
                AccessList(address=Address(2), storage_keys=[Hash(1)]),
            ],
            id="multiple_addresses",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(
                        0xDE0B295669A9FD93D5F28D9EC85E40F4CB697BAE
                    ),
                    storage_keys=[
                        Hash(
                            0x0000000000000000000000000000000000000000000000000000000000000003
                        ),
                        Hash(
                            0x0000000000000000000000000000000000000000000000000000000000000007
                        ),
                    ],
                )
            ],
            id="realistic_address_and_keys",
        ),
    ],
)
@pytest.mark.parametrize(
    "to",
    [
        pytest.param("eoa", id="to_eoa"),
    ],
    indirect=True,
)
def test_access_list_gas_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
) -> None:
    """
    Test that transactions with access lists are charged correctly
    according to EIP-7981.

    The test verifies that:
    1. Access lists are charged for storage access (existing behavior)
    2. Access lists are charged for their data footprint (new in EIP-7981)
    3. Access list data contributes to the floor gas cost
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
                AccessList(
                    address=Address(0),
                    storage_keys=[Hash(0) for _ in range(10)],
                )
            ],
            id="all_zero_bytes",
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
                        for _ in range(5)
                    ],
                )
            ],
            id="all_nonzero_bytes",
        ),
    ],
)
@pytest.mark.parametrize(
    "to",
    [
        pytest.param("eoa", id=""),
    ],
    indirect=True,
)
def test_access_list_data_cost_edge_cases(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
) -> None:
    """
    Test edge cases for access list data costs.

    Tests include:
    - All zero bytes in access list
    - All non-zero bytes in access list
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )
