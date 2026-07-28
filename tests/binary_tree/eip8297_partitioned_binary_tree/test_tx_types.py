"""
Transaction-type tests for the EIP-8297 partitioned binary tree: every
transaction envelope the fork supports -- and the blob-carrying
transaction specifically -- must reach the same storage-writing post
state and correct gas accounting, proving the binary tree commitment
swap is invisible to the transaction layer as well as to execution.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
    add_kzg_version,
)

from ...cancun.eip4844_blobs.spec import Spec as Spec4844
from .spec import ref_spec_8297

REFERENCE_SPEC_GIT_PATH = ref_spec_8297.git_path
REFERENCE_SPEC_VERSION = ref_spec_8297.version

pytestmark = pytest.mark.valid_from("BinaryTree")


@pytest.mark.with_all_tx_types
def test_all_tx_types_write_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
) -> None:
    """
    Verify a storage-writing call transaction of every type the fork
    supports (legacy, access-list, dynamic-fee, blob and set-code)
    leaves the storage-writing contract in the same post state,
    proving the binary tree commitment swap does not depend on which
    transaction envelope carries the call. Type 3 additionally burns
    blob gas and type 4 bumps the authority's nonce, so this checks
    only the one account below, not that the whole transaction's post
    state is identical across types.
    """
    slot, value = 0, 1
    contract = pre.deploy_contract(code=Op.SSTORE(slot, value) + Op.STOP)
    sender = pre.fund_eoa()

    tx_kwargs: dict = {
        "ty": tx_type,
        "sender": sender,
        "to": contract,
    }

    if tx_type >= 1:
        # Type 1+: EIP-2930 access list envelope field.
        tx_kwargs["access_list"] = []
    if tx_type == 3:
        # Type 3: EIP-4844 blob transaction.
        tx_kwargs["max_fee_per_blob_gas"] = fork.min_base_fee_per_blob_gas()
        tx_kwargs["blob_versioned_hashes"] = add_kzg_version(
            [0], Spec4844.BLOB_COMMITMENT_VERSION_KZG
        )
    elif tx_type == 4:
        # Type 4: EIP-7702 set-code transaction.
        signer = pre.fund_eoa(amount=0)
        tx_kwargs["authorization_list"] = [
            AuthorizationTuple(signer=signer, address=Address(0), nonce=0)
        ]

    tx = Transaction(**tx_kwargs)
    post = {contract: Account(storage={slot: value})}
    state_test(pre=pre, post=post, tx=tx)


def test_blob_transaction_writes_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify a blob-carrying (EIP-4844) transaction's call still writes
    storage exactly as any other transaction type would, and that the
    receipt's blob-gas accounting reflects only the attached blob,
    unaffected by the binary tree commitment swap.
    """
    slot, value = 0, 1
    contract = pre.deploy_contract(code=Op.SSTORE(slot, value) + Op.STOP)
    sender = pre.fund_eoa()

    blob_count = 1
    tx = Transaction(
        ty=3,
        sender=sender,
        to=contract,
        max_fee_per_blob_gas=fork.min_base_fee_per_blob_gas(),
        blob_versioned_hashes=add_kzg_version(
            [0] * blob_count, Spec4844.BLOB_COMMITMENT_VERSION_KZG
        ),
        expected_receipt=TransactionReceipt(
            blob_gas_used=fork.blob_gas_per_blob() * blob_count
        ),
    )

    post = {contract: Account(storage={slot: value})}
    state_test(pre=pre, post=post, tx=tx)
