"""
Blob-carrying keyed frame transactions submitted in their network wrapper,
for [EIP-8250: Keyed Nonces](https://eips.ethereum.org/EIPS/eip-8250).

EIP-8250 replaces every EIP-8141 public mempool dependency on the sender
nonce with the sequence of each selected nonce key. These tests submit
blob-carrying frame transactions on non-zero nonce keys through
`eth_sendRawTransaction`, in their EIP-7594 network wrapper, and check
that the client serves their blobs through `engine_getBlobsV*`.

A contract sender's account nonce is one while a fresh key's sequence is
zero, so a pool that checks the account nonce instead of the selected
keys' sequence rejects its transaction.
"""

from typing import List

import pytest
from execution_testing import (
    Address,
    Alloc,
    Blob,
    BlobsTestFiller,
    Fork,
    NetworkWrappedTransaction,
    Op,
    Transaction,
)

from ..eip8141_frame_transactions.helpers import verify_frame
from ..eip8141_frame_transactions.spec import Spec as Spec8141
from .helpers import NONCE_KEY, OTHER_KEY
from .spec import ref_spec_8250

REFERENCE_SPEC_GIT_PATH = ref_spec_8250.git_path
REFERENCE_SPEC_VERSION = ref_spec_8250.version

pytestmark = pytest.mark.valid_from("Bogota")

CONTRACT_SENDER_BALANCE = 10**17
"""
Balance of a contract sender, which execute mode cannot fund from the
transaction's gas price as it does an EOA: enough for the small
transaction below at devnet gas prices.
"""


def sender(pre: Alloc, contract_sender: bool) -> Address:
    """
    Return a fresh EOA running the default code, or a contract sender
    whose code approves execution and payment and whose account nonce is
    therefore one.
    """
    if contract_sender:
        return pre.deploy_contract(
            code=Op.APPROVE(0, 0, Spec8141.APPROVE_EXECUTION_AND_PAYMENT),
            balance=CONTRACT_SENDER_BALANCE,
        )
    return pre.fund_eoa()


@pytest.mark.parametrize(
    "nonce_keys",
    [[NONCE_KEY], [NONCE_KEY, OTHER_KEY]],
    ids=["one_key", "two_keys"],
)
@pytest.mark.parametrize(
    "contract_sender",
    [False, True],
    ids=["eoa_sender", "contract_sender"],
)
@pytest.mark.exception_test
def test_get_blobs_of_keyed_frame_tx(
    blobs_test: BlobsTestFiller,
    pre: Alloc,
    fork: Fork,
    nonce_keys: List[int],
    contract_sender: bool,
) -> None:
    """
    Submit a blob-carrying frame transaction on fresh non-zero nonce keys
    in its network wrapper and retrieve its blobs by versioned hash.

    The keys' shared sequence is zero. For a contract sender the account
    nonce is one, so the transaction is admissible only when the pool
    checks the selected keys' sequence, as EIP-8250 requires.
    """
    blobs = [Blob.from_fork(fork)]
    tx = Transaction(
        sender=sender(pre, contract_sender),
        nonce_keys=nonce_keys,
        nonce=0,
        # The validation prefix leaves room for signature verification
        # within MAX_VERIFY_GAS, so a public mempool admits it.
        frames=[verify_frame(gas_limit=Spec8141.MAX_VERIFY_GAS // 2)],
        blob_versioned_hashes=[blob.versioned_hash for blob in blobs],
    )
    blobs_test(
        pre=pre,
        txs=[
            NetworkWrappedTransaction(
                tx=tx,
                blob_objects=blobs,
                wrapper_version=fork.full_blob_tx_wrapper_version(),
            )
        ],
    )
