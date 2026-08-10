"""
Tests that pin what `eth_estimateGas` is allowed to answer.

The one method in this suite whose answer no specification determines.
A client finds it by search — go-ethereum's own documentation warns that
its estimate "may be significantly more than the amount of gas actually
used" — and execution-apis records the same judgement in its corpus: five
of its six `eth_estimateGas` tests assert the shape of the response and
nothing about its value.

The sixth asserts a value, and that split is what these tests are built
on. A message that names no data and calls no code has nothing to search
for: every limit the fork admits completes it and every limit below is
refused outright, so the answer is the plain cost of putting the
transaction on the chain. Those shapes are pinned exactly. Everything
else is pinned as a *range* — no smaller than the least limit at which
the message completes, no larger than the limit the message itself names
— which is the strongest honest claim available and still catches the
failure that matters, a client whose estimate would leave the
transaction short.

Which of the two a message gets is not asserted here, and is not written
into these tests either. It is decided at fill time by executing the
message at the boundary and seeing whether the limit below is rejected or
merely runs dry; see `rpc.serialization.execution.estimate_gas`. These
tests choose shapes that fall on either side of that line, and the fill
decides which side each landed on.

Derivation replays the first transaction of each block, so most of these
need only produce a block whose opening transaction has the shape wanted,
and write no call at all.

The suite starts at Prague rather than at the current fork, for the reason
recorded beside the `eth_createAccessList` tests: go-ethereum cannot
currently consume an Amsterdam fixture that touches storage.
"""

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    Conditional,
    Op,
    Transaction,
)
from execution_testing.specs.blockchain import RPCExpectation

pytestmark = [pytest.mark.valid_from("Prague"), pytest.mark.rpc]


def test_estimate_a_transfer(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A plain value transfer, whose estimate is its intrinsic cost.

    The one shape execution-apis also pins exactly, and the reason it can
    be: a transfer runs no code, so the least limit that completes it is
    the least limit the fork admits at all. A client that searched would
    find nothing to search for, and one that padded its answer would be
    reporting a cost the transfer does not have.
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


def test_estimate_a_call_to_a_codeless_account(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A message to an account that exists and holds no code.

    Exact for the same reason the transfer is, and worth separating from
    it: the recipient here is an account already on the chain rather than
    one the message brings into being, and it carries neither value nor
    data. Nothing is executed, nothing is charged for beyond putting the
    transaction on the chain, and the answer is the same 21000 — which is
    the assertion, since a client that charged for the recipient, or for
    the message being a call rather than a transfer, would say otherwise.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[Transaction(sender=sender, to=recipient, value=0)])
        ],
        post={},
    )


def test_estimate_a_transfer_carrying_calldata(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A message to an account with no code, carrying calldata it ignores.

    The calldata is charged for even though nothing reads it, and since
    Prague a message carrying any at all is charged a floor that exceeds
    what it otherwise costs — so the least limit that works here is the
    floor, and it is well above the 21000 the same message without data
    would need.

    The specification determines that figure exactly, and this is
    nonetheless a range. Adding data is what makes go-ethereum search
    instead of short-circuiting, and its search stops within a
    sixty-fourth of where it started rather than at the floor; see
    `estimate_gas` for the measurement. The range still catches the
    failure that matters, which for this shape is a client charging the
    older per-byte price and answering below a floor the chain enforces.

    The bytes are a mixture of zero and non-zero on purpose, the two
    being priced differently in both the cost and the floor.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=sender,
                        to=recipient,
                        value=1,
                        data=bytes([0x00, 0xAB] * 48),
                        gas_limit=60_000,
                    )
                ]
            )
        ],
        post={},
    )


def test_estimate_a_contract_call(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A contract that writes a slot, which is where a search begins.

    Nothing in the specification says what a client must answer here, so
    the expectation is a range. Its floor is the least limit at which the
    message completes, established by bisection at fill time, and a
    client answering below it has proposed a limit that runs out of gas.

    The transaction names far more gas than the message needs, so the
    range is wide and a client is free to answer anywhere inside it. That
    is the point: what is asserted is that the answer is *usable*, not
    that it is any particular number.
    """
    probe = pre.deploy_contract(Op.SSTORE(0x1, 0x2A) + Op.STOP)
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=sender, to=probe, gas_limit=500_000)]
            )
        ],
        post={},
    )


def test_estimate_across_a_call(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A contract calling another, where the estimate exceeds the cost.

    The shape that makes an estimate more than an accounting exercise. A
    frame may only pass 63/64ths of what it holds to its callee, so a
    message whose inner frame needs *n* gas can require more than *n*
    available before it will run — and the gas the message ends up
    spending is then strictly less than the limit it needed to be given.
    A client reporting what the message used, rather than what it needed,
    answers below the floor here and is caught.

    The caller reverts when the callee fails, which is what makes the
    shape assertable at all. A caller that ignored the failure would
    still *complete* on a limit that starved its callee, only having done
    less — and a message that does different work depending on what it is
    offered has no honest bound, so the derivation refuses one rather
    than pinning the cheaper path.
    """
    callee = pre.deploy_contract(Op.SSTORE(0x2, 0x2A) + Op.STOP)
    caller = pre.deploy_contract(
        Conditional(
            condition=Op.CALL(Op.GAS, callee, 0, 0, 0, 0, 0),
            if_true=Op.STOP,
            if_false=Op.REVERT(0, 0),
        )
    )
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=sender, to=caller, gas_limit=500_000)]
            )
        ],
        post={},
    )


def test_estimate_a_reverting_call(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A contract that always reverts, which has no estimate at all.

    Neither a value nor a range: no gas limit whatsoever completes this
    message, so there is nothing for a search to converge on and a client
    answers with the revert instead. That makes this the one estimate in
    the suite asserted as an error, under the same code
    `eth_call` reports a revert with.

    A client that answered with a number here would be claiming a limit
    at which the transaction succeeds, and no such limit exists.
    """
    probe = pre.deploy_contract(Op.REVERT(0, 0))
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=sender, to=probe, gas_limit=100_000)]
            )
        ],
        post={},
    )


def test_declared_estimate_at_historical_states(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    One declared message, estimated against two states that differ.

    Derivation replays a message the chain contained; asking the *same*
    message of several states has to be declared. The probe writes to a
    slot the recipient's balance names, and the chain moves that balance
    between the two blocks, so at the earlier state the message clears a
    slot that was set and at the later one it sets a slot that was clear.
    Those cost very different amounts, and a client resolving every block
    to its head answers the later figure for the earlier block.
    """
    recipient = pre.fund_eoa(amount=1)
    probe = pre.deploy_contract(
        Op.SSTORE(Op.BALANCE(recipient), 0x2A) + Op.STOP,
        storage={1: 0x99},
    )
    sender = pre.fund_eoa()
    message = {"from": sender, "to": probe, "gas": hex(500_000)}

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[Transaction(sender=sender, to=recipient, value=5)])
        ],
        post={},
        rpc_checks=[
            RPCExpectation(
                method="eth_estimateGas",
                params=[message, "0x0"],
                derive_result=True,
            ),
            RPCExpectation(
                method="eth_estimateGas",
                params=[message, "latest"],
                derive_result=True,
            ),
        ],
    )
