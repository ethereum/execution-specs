"""
Transaction total gas limit cap tests for EIP-8037.

EIP-8037 applies the EIP-7825 cap to execution gas only and instead
caps ``tx.gas`` as a whole at ``TX_MAX_TOTAL_GAS_LIMIT``. The cap is a
transaction validity rule, so every test here raises the block gas limit
above it: the block's per-dimension capacity check then cannot be the
reason a transaction is rejected, and the only rule an above-cap
transaction breaks is the cap itself.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Environment,
    Fork,
    Hash,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    add_kzg_version,
)

from ...cancun.eip4844_blobs.spec import Spec as EIP4844_Spec
from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "gas_delta, error",
    [
        pytest.param(0, None, id="at_cap"),
        pytest.param(
            1,
            TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
            id="above_cap",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.with_all_tx_types
@pytest.mark.valid_from("EIP8037")
def test_tx_total_gas_limit_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    gas_delta: int,
    error: TransactionException | None,
) -> None:
    """
    Accept a transaction at ``TX_MAX_TOTAL_GAS_LIMIT`` and reject one a
    single unit of gas above it, for every transaction type.
    """
    total_cap = fork.transaction_total_gas_limit_cap()
    assert total_cap is not None, "fork does not cap tx.gas as a whole"
    gas_limit = total_cap + gas_delta

    storage = Storage()
    contract = pre.deploy_contract(code=Op.SSTORE(storage.store_next(1), 1))

    tx_kwargs: dict = {}
    if tx_type == 1:
        tx_kwargs["access_list"] = [
            AccessList(address=contract, storage_keys=[Hash(0)])
        ]
    elif tx_type == 2:
        tx_kwargs["access_list"] = []
    elif tx_type == 3:
        tx_kwargs["blob_versioned_hashes"] = add_kzg_version(
            [Hash(1)], EIP4844_Spec.BLOB_COMMITMENT_VERSION_KZG
        )
        tx_kwargs["max_fee_per_blob_gas"] = fork.min_base_fee_per_blob_gas()
    elif tx_type == 4:
        tx_kwargs["authorization_list"] = [
            AuthorizationTuple(
                signer=pre.fund_eoa(amount=0), address=Address(1)
            )
        ]

    tx = Transaction(
        ty=tx_type,
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        error=error,
        **tx_kwargs,
    )

    state_test(
        # Keep the block capacity rule out of the picture: the block has
        # room for the above-cap transaction, so only the cap rejects it.
        env=Environment(gas_limit=2 * total_cap),
        pre=pre,
        post={contract: Account(storage=storage if error is None else {})},
        tx=tx,
    )
