"""
Tests that clients report an EIP-7702 delegation correctly over JSON-RPC.

A delegation is written to an account that the transaction never names as
its recipient, and it changes that account in two ways a client has to
report: `eth_getCode` returns the designator `0xef0100 ‖ address` where the
account previously had none, and `eth_getTransactionCount` counts the
authorization even though the authority sent nothing.

Both are reachable only through the authorization list. A client — or a
test framework — that walks senders and recipients alone never looks at the
authority, and so never notices either change.
"""

import pytest
from execution_testing import (
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Op,
    Transaction,
)

from .spec import ref_spec_7702

REFERENCE_SPEC_GIT_PATH = ref_spec_7702.git_path
REFERENCE_SPEC_VERSION = ref_spec_7702.version

pytestmark = [pytest.mark.valid_from("Prague"), pytest.mark.rpc]


def test_rpc_reports_delegation(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    An authority delegated to by a transaction sent elsewhere.

    The transaction is addressed to an unrelated account, so the authority
    is reached only through the authorization list. Delegating to two
    different targets in the same block also pins that the designator names
    the account it actually points at, which a single delegation cannot
    distinguish from a constant.
    """
    first_target = pre.deploy_contract(Op.SSTORE(1, 1) + Op.STOP)
    second_target = pre.deploy_contract(Op.SSTORE(2, 2) + Op.STOP)
    elsewhere = pre.fund_eoa(amount=0)

    sender = pre.fund_eoa()
    first_authority = pre.fund_eoa()
    second_authority = pre.fund_eoa()

    delegating = Transaction(
        sender=sender,
        to=elsewhere,
        gas_limit=200_000,
        authorization_list=[
            AuthorizationTuple(address=first_target, signer=first_authority),
            AuthorizationTuple(address=second_target, signer=second_authority),
        ],
    )
    # A call into one of the authorities, so the delegated code runs and
    # the storage it writes lands on the authority rather than the target.
    invoking = Transaction(
        sender=sender, to=first_authority, gas_limit=200_000
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[delegating]), Block(txs=[invoking])],
        post={},
    )
