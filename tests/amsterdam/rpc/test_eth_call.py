"""
Tests that pin `eth_call` against a spec-derived expectation.

Every other method this suite derives is a projection: the transition
tool computed the answer and the fixture reformats it. `eth_call` is the
first that is not — the expectation exists only because the message was
executed at fill time, against the state at a block the transaction it
was read from did not run in.

The four shapes here are the ones whose *reporting* differs rather than
whose execution does. A client returns an empty result for a transfer, a
word for a contract that returns one, an error object carrying code `3`
for a revert, and — the case most easily got wrong — an empty result
rather than an error for a call to an account that does not exist. A
suite covering only the third of these would not notice a client that
reported the fourth as a failure.

Derivation replays the first transaction of each block, so each test
needs only to produce a block whose first transaction has the shape
wanted; no call is written here.
"""

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    Op,
    Transaction,
)

pytestmark = [pytest.mark.valid_from("Amsterdam"), pytest.mark.rpc]


def test_call_transfer(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A plain value transfer, which returns nothing.

    The empty result is the assertion. A transfer touches no code, so a
    client with any return data at all to report here is reporting
    something it invented.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[Transaction(sender=sender, to=recipient, value=1)])
        ],
        post={},
    )


def test_call_returning_data(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A contract that returns a word.

    The only shape here whose answer a client could get wrong by
    executing correctly and reporting badly — truncating the return
    data, or hex-encoding it differently — which is why the expectation
    is a specific word rather than merely a non-empty string.
    """
    contract = pre.deploy_contract(Op.MSTORE(0, 0x1234) + Op.RETURN(0, 32))
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[Transaction(sender=sender, to=contract)])],
        post={},
    )


def test_call_reverting(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A contract that reverts with data.

    A revert is not a result. execution-apis assigns it code `3` and
    hangs the revert data off the error object, so a client answering
    with a successful empty result — which is what returning
    `tx_output.return_data` unconditionally would produce — is wrong in a
    way no schema catches. Only the code is asserted; the wording is
    client-specific everywhere in this suite.
    """
    contract = pre.deploy_contract(Op.MSTORE(0, 0xDEAD) + Op.REVERT(0, 32))
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[Transaction(sender=sender, to=contract)])],
        post={},
    )


def test_call_missing_account(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A call to an account that does not exist.

    The state is a total function, so an unallocated address has no code
    and a call to it succeeds with empty return data rather than failing.
    This is the counterpart to the reverting case: both answer `0x`
    worth of data, and a client conflating them reports one of the two
    incorrectly.
    """
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=sender, to=0x0BAD_0BAD, data=b"\x01")]
            )
        ],
        post={},
    )
