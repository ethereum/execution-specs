"""
abstract: Crafted tests for mainnet of [EIP-7623: Increase calldata cost](https://eips.ethereum.org/EIPS/eip-7623).
"""  # noqa: E501

import pytest
from ethereum_test_tools import (
    AccessList,
    Address,
    Alloc,
    Hash,
    StateTestFiller,
    Transaction,
    add_kzg_version,
)

from ...cancun.eip4844_blobs.spec import Spec as EIP_4844_Spec
from .helpers import DataTestType
from .spec import ref_spec_7623

REFERENCE_SPEC_GIT_PATH = ref_spec_7623.git_path
REFERENCE_SPEC_VERSION = ref_spec_7623.version

pytestmark = [pytest.mark.valid_at("Prague"), pytest.mark.mainnet]


@pytest.mark.parametrize(
    "ty,protected,access_list,blob_versioned_hashes,authorization_list",
    [
        pytest.param(0, True, None, None, None, id="type_0_protected"),
        pytest.param(0, False, None, None, None, id="type_0_unprotected"),
        pytest.param(
            1,
            True,
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            None,
            None,
            id="type_1",
        ),
        pytest.param(
            2,
            True,
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            None,
            None,
            id="type_2",
        ),
        pytest.param(
            3,
            True,
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            add_kzg_version(
                [Hash(x) for x in range(1)],
                EIP_4844_Spec.BLOB_COMMITMENT_VERSION_KZG,
            ),
            None,
            id="type_3",
            marks=pytest.mark.execute(
                pytest.mark.skip(reason="Blob txs not supported by execute")
            ),
        ),
        pytest.param(
            4,
            True,
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            None,
            [Address(1)],
            id="type_4",
        ),
    ],
    indirect=["authorization_list"],
)
@pytest.mark.parametrize(
    "tx_gas_delta",
    [
        pytest.param(0, id=""),
    ],
)
@pytest.mark.parametrize(
    "to",
    [
        pytest.param("eoa", id=""),
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    "data_test_type",
    [
        pytest.param(
            DataTestType.FLOOR_GAS_COST_GREATER_THAN_INTRINSIC_GAS,
            id="",
        ),
    ],
)
def test_eip_7623(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
) -> None:
    """
    Test transaction validity for transactions without access lists
    and contract creation.
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )
