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

Derivation replays the first transaction of each block, so the first
four tests need only produce a block whose opening transaction has the
shape wanted, and write no call at all. The fifth declares its message,
because asking the *same* message of several states is the one thing
replay cannot express.
"""

import pytest
from execution_testing import (
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Op,
    Transaction,
)
from execution_testing.specs.blockchain import RPCExpectation

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


def test_declared_call_at_historical_states(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    One declared message, asked of three different states.

    Derivation reads its parameters off the chain, so it can only replay
    a message the chain contained. A message the chain never contained —
    and, more to the point, the *same* message asked of several states —
    has to be declared.

    That is what makes this the case for historical state. The three
    answers differ only because the states do, so a client resolving
    every block to its head passes the first assertion and fails the
    other two. A single call at `latest` could not tell the two apart.

    The probe reads a balance rather than storage because the value has
    to change from block to block without the chain writing any: what is
    being asserted is which state the client picked, not what a contract
    computed from it.
    """
    recipient = pre.fund_eoa(amount=0)
    probe = pre.deploy_contract(
        Op.MSTORE(0, Op.BALANCE(recipient)) + Op.RETURN(0, 32)
    )
    sender = pre.fund_eoa()
    message = {"from": sender, "to": probe}

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[Transaction(sender=sender, to=recipient, value=5)]),
            Block(txs=[Transaction(sender=sender, to=recipient, value=7)]),
        ],
        post={},
        rpc_checks=[
            RPCExpectation(
                method="eth_call", params=[message, "0x0"], derive_result=True
            ),
            RPCExpectation(
                method="eth_call", params=[message, "0x1"], derive_result=True
            ),
            RPCExpectation(
                method="eth_call",
                params=[message, "latest"],
                derive_result=True,
            ),
        ],
    )


def test_declared_call_from_a_contract(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A call whose `from` is a contract, which no key can sign for.

    A sender recovered from a signature is necessarily an externally
    owned account, so this message cannot exist as a transaction at all;
    a client answers it anyway. The probe returns `CALLER`, so the
    expectation pins which address the EVM saw rather than merely that
    something ran.
    """
    probe = pre.deploy_contract(Op.MSTORE(0, Op.CALLER) + Op.RETURN(0, 32))
    # Funded because the message is priced at the block's base fee, the
    # one admission check a derived call does not relax.
    contract = pre.deploy_contract(Op.STOP, balance=10**18)
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[Transaction(sender=sender, to=probe)])],
        post={},
        rpc_checks=[
            RPCExpectation(
                method="eth_call",
                params=[{"from": contract, "to": probe}, "0x0"],
                derive_result=True,
            )
        ],
    )


def test_declared_call_from_the_zero_address(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A call whose `from` is the zero address.

    The commonest `from` in real usage, and the one address no key will
    ever recover to. The probe returns its caller's balance rather than
    its address, so an empty word cannot pass for an answer: the value
    is the funded balance less the gas the message bought.
    """
    probe = pre.deploy_contract(
        Op.MSTORE(0, Op.BALANCE(Op.CALLER)) + Op.RETURN(0, 32)
    )
    pre.fund_address(Address(0), 10**18)
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[Transaction(sender=sender, to=probe)])],
        post={},
        rpc_checks=[
            RPCExpectation(
                method="eth_call",
                params=[{"from": Address(0), "to": probe}, "0x0"],
                derive_result=True,
            )
        ],
    )


def test_declared_call_sees_its_own_gas_bought(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A probe reporting the balance of whoever called it.

    The subtlest agreement in the whole method, and the one a derivation
    is most likely to get wrong. A message is charged for its gas before
    its frame runs, exactly as a transaction is, so a contract reading
    its caller's balance sees the debited figure rather than the stored
    one. Deriving the answer from the state as stored would produce a
    value that looks right and is wrong by `gas * gasPrice`.

    It only bites because the message states an explicit price. A client
    left to default `gasPrice` would buy gas for nothing and see the
    undebited balance, which is the concrete reason the price is stated
    rather than left out.
    """
    probe = pre.deploy_contract(
        Op.MSTORE(0, Op.BALANCE(Op.CALLER)) + Op.RETURN(0, 32)
    )
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[Transaction(sender=sender, to=probe)])],
        post={},
        rpc_checks=[
            RPCExpectation(
                method="eth_call",
                params=[{"from": sender, "to": probe}, "0x0"],
                derive_result=True,
            )
        ],
    )
