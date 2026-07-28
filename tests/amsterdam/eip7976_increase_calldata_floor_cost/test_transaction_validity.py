"""
Test [EIP-7976: Increase calldata floor cost](https://eips.ethereum.org/EIPS/eip-7976).
"""

import pytest
from execution_testing import (
    AccessList,
    Address,
    Alloc,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
    add_kzg_version,
)

from ...osaka.eip7594_peerdas.spec import Spec as EIP_7594_Spec
from .helpers import DataTestType
from .spec import ref_spec_7976

REFERENCE_SPEC_GIT_PATH = ref_spec_7976.git_path
REFERENCE_SPEC_VERSION = ref_spec_7976.version

pytestmark = [pytest.mark.valid_from("EIP7976")]


# All tests in this file are parametrized with the following parameters:
pytestmark += [
    pytest.mark.parametrize(
        "tx_gas_delta",
        [
            # Test the case where the included gas is greater than the
            # intrinsic gas to verify that the data floor does not consume more
            # gas than it should.
            pytest.param(1, id="extra_gas"),
            pytest.param(0, id="exact_gas"),
            pytest.param(
                -1, id="insufficient_gas", marks=pytest.mark.exception_test
            ),
        ],
    ),
    pytest.mark.parametrize(
        "data_test_type",
        [
            pytest.param(
                DataTestType.FLOOR_GAS_COST_LESS_THAN_OR_EQUAL_TO_INTRINSIC_GAS,
                id="floor_gas_less_than_or_equal_to_intrinsic_gas",
            ),
            pytest.param(
                DataTestType.FLOOR_GAS_COST_GREATER_THAN_INTRINSIC_GAS,
                id="floor_gas_greater_than_intrinsic_gas",
            ),
        ],
    ),
]


@pytest.mark.parametrize(
    "protected",
    [
        pytest.param(True, id="protected"),
        pytest.param(False, id="unprotected"),
    ],
)
@pytest.mark.parametrize(
    "ty",
    [pytest.param(0, id="type_0")],
)
@pytest.mark.parametrize(
    "to",
    [
        pytest.param("eoa", id="to_eoa"),
        pytest.param(None, id="contract_creating"),
        pytest.param(Op.STOP, id=""),
    ],
    indirect=True,
)
def test_transaction_validity_type_0(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
) -> None:
    """
    Test transaction validity for transactions without access lists and
    contract creation.
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.parametrize(
    "to",
    [
        pytest.param("eoa", id="to_eoa"),
        pytest.param(None, id="contract_creating"),
        pytest.param(Op.STOP, id=""),
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    "access_list",
    [
        pytest.param(
            None,
            id="no_access_list",
        ),
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[])],
            id="single_access_list_no_storage_keys",
        ),
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            id="single_access_list_single_storage_key",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(1),
                    storage_keys=[Hash(k) for k in range(10)],
                )
            ],
            id="single_access_list_multiple_storage_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(a), storage_keys=[])
                for a in range(10)
            ],
            id="multiple_access_lists_no_storage_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(a), storage_keys=[Hash(0)])
                for a in range(10)
            ],
            id="multiple_access_lists_single_storage_key",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(a),
                    storage_keys=[Hash(k) for k in range(10)],
                )
                for a in range(10)
            ],
            id="multiple_access_lists_multiple_storage_keys",
        ),
    ],
)
@pytest.mark.parametrize(
    "ty",
    [pytest.param(1, id="type_1"), pytest.param(2, id="type_2")],
)
def test_transaction_validity_type_1_type_2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
) -> None:
    """
    Test transaction validity for transactions with access lists and contract
    creation.
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.parametrize(
    "access_list",
    [
        pytest.param(
            None,
            id="no_access_list",
        ),
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[])],
            id="single_access_list_no_storage_keys",
        ),
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            id="single_access_list_single_storage_key",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(1),
                    storage_keys=[Hash(k) for k in range(10)],
                )
            ],
            id="single_access_list_multiple_storage_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(a), storage_keys=[])
                for a in range(10)
            ],
            id="multiple_access_lists_no_storage_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(a), storage_keys=[Hash(0)])
                for a in range(10)
            ],
            id="multiple_access_lists_single_storage_key",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(a),
                    storage_keys=[Hash(k) for k in range(10)],
                )
                for a in range(10)
            ],
            id="multiple_access_lists_multiple_storage_keys",
        ),
    ],
)
@pytest.mark.parametrize(
    # Blobs don't really have an effect because the blob gas does is not
    # considered in the intrinsic gas calculation, but we still test it to make
    # sure that the transaction is correctly processed.
    "blob_versioned_hashes",
    [
        pytest.param(
            add_kzg_version(
                [Hash(x) for x in range(1)],
                EIP_7594_Spec.BLOB_COMMITMENT_VERSION_KZG,
            ),
            id="single_blob",
        ),
        pytest.param(
            add_kzg_version(
                [Hash(x) for x in range(6)],
                EIP_7594_Spec.BLOB_COMMITMENT_VERSION_KZG,
            ),
            id="multiple_blobs",
        ),
    ],
)
@pytest.mark.parametrize(
    "ty",
    [pytest.param(3, id="type_3")],
)
def test_transaction_validity_type_3(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
) -> None:
    """
    Test transaction validity for transactions with access lists, blobs, but no
    contract creation.
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.parametrize(
    "access_list",
    [
        pytest.param(
            None,
            id="no_access_list",
        ),
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[])],
            id="single_access_list_no_storage_keys",
        ),
        pytest.param(
            [AccessList(address=Address(1), storage_keys=[Hash(0)])],
            id="single_access_list_single_storage_key",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(1),
                    storage_keys=[Hash(k) for k in range(10)],
                )
            ],
            id="single_access_list_multiple_storage_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(a), storage_keys=[])
                for a in range(10)
            ],
            id="multiple_access_lists_no_storage_keys",
        ),
        pytest.param(
            [
                AccessList(address=Address(a), storage_keys=[Hash(0)])
                for a in range(10)
            ],
            id="multiple_access_lists_single_storage_key",
        ),
        pytest.param(
            [
                AccessList(
                    address=Address(a),
                    storage_keys=[Hash(k) for k in range(10)],
                )
                for a in range(10)
            ],
            id="multiple_access_lists_multiple_storage_keys",
        ),
    ],
)
@pytest.mark.parametrize(
    "authorization_list",
    [
        pytest.param(
            [Address(1)],
            id="single_authorization",
        ),
        pytest.param(
            [Address(i + 1) for i in range(10)],
            id="multiple_authorizations",
        ),
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    "ty",
    [pytest.param(4, id="type_4")],
)
def test_transaction_validity_type_4(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
) -> None:
    """
    Test transaction validity for transactions with access lists, authorization
    lists, but no contract creation.
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.parametrize(
    "ty",
    [pytest.param(0, id="type_0"), pytest.param(2, id="type_2")],
)
@pytest.mark.parametrize(
    "to",
    [
        pytest.param(
            Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.PUSH0
            + Op.CREATE2
            + Op.STOP,
            id="contract_with_create2",
        ),
    ],
    indirect=True,
)
def test_transaction_validity_with_create2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
) -> None:
    """
    Test transaction validity for transactions calling a contract that uses
    CREATE2 internally. This verifies that internal contract creation via
    CREATE2 doesn't interfere with the floor gas cost mechanism.
    """
    state_test(
        pre=pre,
        post={},
        tx=tx,
    )
