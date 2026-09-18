"""
Accounts created and destroyed in the same transaction, across a reorg.

Port of erigon ``TestReorgOverSelfDestruct`` adjusted for EIP-6780: a
``SELFDESTRUCT`` only deletes the account when it runs in the transaction that
created it, so the destroyed account here is built by a factory that creates
the contract and calls it back within one transaction.

The ``CREATE2`` salt and initcode are the same on every branch, so the
contract always lands on the same address and the branches differ only in
whether it survives. Two shapes are covered:

- the account is destroyed on one branch and alive on its sibling, with the
  head moving between them;
- the account is destroyed and recreated inside a single block, the pattern
  erigon's own comment says its parallel executor does not yet handle
  (``execution/execmodule/execmoduletester/exec_module_tester.go``).
"""

from typing import List, Tuple

import pytest
from execution_testing import (
    Address,
    Alloc,
    Conditional,
    Hash,
    Initcode,
    Op,
    Transaction,
    compute_create2_address,
)
from execution_testing.fixtures.reorg import (
    AccountExpectation,
    AssertHeadStep,
    AssertStateStep,
    ForkchoiceUpdatedStep,
    NewPayloadStep,
    Step,
)
from execution_testing.specs import ReorgBlock, ReorgTestFiller

SALT = 0
SLOT = 0
STORED = 0x2A
ENDOWMENT = 10**15
BENEFICIARY = 0x0BE0
GAS = 500_000

#: Deployed code: self-destruct, sending the balance to a fixed beneficiary.
RUNTIME = Op.SELFDESTRUCT(BENEFICIARY)

#: Identical on every branch, so the CREATE2 address is too.
INITCODE = bytes(
    Initcode(deploy_code=RUNTIME, initcode_prefix=Op.SSTORE(SLOT, STORED))
)
assert len(INITCODE) <= 32, (
    f"initcode must fit one word, is {len(INITCODE)} bytes"
)

#: ``calldata[0] != 0`` also destroys the contract, in the creating call.
FACTORY = (
    Op.MSTORE(0, int.from_bytes(INITCODE, "big"))
    + Op.MSTORE(
        0x20, Op.CREATE2(ENDOWMENT, 32 - len(INITCODE), len(INITCODE), SALT)
    )
    + Conditional(
        condition=Op.CALLDATALOAD(0),
        if_true=Op.POP(Op.CALL(Op.GAS, Op.MLOAD(0x20), 0, 0, 0, 0, 0)),
    )
)

DESTROYED = AccountExpectation(balance=0, storage={Hash(SLOT): Hash(0)})
ALIVE = AccountExpectation(
    balance=ENDOWMENT, storage={Hash(SLOT): Hash(STORED)}
)


def _factory(pre: Alloc) -> Tuple[Address, Address]:
    """Deploy the factory, funded for several creations."""
    factory = pre.deploy_contract(code=FACTORY, balance=ENDOWMENT * 8)
    return factory, compute_create2_address(factory, SALT, INITCODE)


@pytest.mark.valid_from("Cancun")
def test_reorg_over_same_tx_selfdestruct(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    The account exists on one branch and not on its sibling.

    ``x1`` creates and destroys it in one transaction; its sibling ``y1``
    creates it and leaves it alive; ``x2`` extends ``x1`` and recreates it at
    the same address.

    Every head move is either a forward extension or a switch between two
    blocks of the same height, so that a client which declines to rewind to a
    canonical ancestor (reth, paradigmxyz/reth#27244) fails this test only on
    the state it reports, not on the shape of the script.
    """
    factory, contract = _factory(pre)
    sender = pre.fund_eoa()

    def call(nonce: int, destroy: bool) -> Transaction:
        return Transaction(
            sender=sender,
            nonce=nonce,
            to=factory,
            data=Hash(destroy),
            gas_limit=GAS,
        )

    blocks = [
        ReorgBlock(label="x1", parent="genesis", txs=[call(0, destroy=True)]),
        ReorgBlock(label="x2", txs=[call(1, destroy=False)]),
        ReorgBlock(label="y1", parent="genesis", txs=[call(0, destroy=False)]),
    ]
    steps: List[Step] = [
        NewPayloadStep(block="x1"),
        ForkchoiceUpdatedStep(head="x1"),
        AssertStateStep(accounts={contract: DESTROYED}),
        NewPayloadStep(block="y1"),
        ForkchoiceUpdatedStep(head="y1"),
        AssertStateStep(accounts={contract: ALIVE}),
        # Sibling switch, back to the branch where it was destroyed.
        ForkchoiceUpdatedStep(head="x1"),
        AssertHeadStep(latest="x1"),
        AssertStateStep(accounts={contract: DESTROYED}),
        # Forward extension of that same branch, recreating it.
        NewPayloadStep(block="x2"),
        ForkchoiceUpdatedStep(head="x2"),
        AssertHeadStep(latest="x2"),
        AssertStateStep(accounts={contract: ALIVE}),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_reorg_over_same_block_destroy_and_recreate(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    The account is destroyed and recreated within one block, then reorged.

    ``z1`` holds both transactions, so the account is written, deleted and
    written again at the same address inside one block; its sibling ``w1``
    never creates it, so moving the head between them has to add and remove
    the recreated account.
    """
    factory, contract = _factory(pre)
    sender = pre.fund_eoa()
    other = pre.fund_eoa()
    blocks = [
        ReorgBlock(
            label="z1",
            parent="genesis",
            txs=[
                Transaction(
                    sender=sender,
                    nonce=0,
                    to=factory,
                    data=Hash(1),
                    gas_limit=GAS,
                ),
                Transaction(
                    sender=sender,
                    nonce=1,
                    to=factory,
                    data=Hash(0),
                    gas_limit=GAS,
                ),
            ],
        ),
        ReorgBlock(
            label="w1",
            parent="genesis",
            txs=[Transaction(sender=other, nonce=0, to=BENEFICIARY, value=1)],
        ),
    ]
    steps: List[Step] = [
        NewPayloadStep(block="z1"),
        ForkchoiceUpdatedStep(head="z1"),
        AssertStateStep(accounts={contract: ALIVE}),
        NewPayloadStep(block="w1"),
        ForkchoiceUpdatedStep(head="w1"),
        AssertStateStep(accounts={contract: DESTROYED}),
        ForkchoiceUpdatedStep(head="z1"),
        AssertStateStep(accounts={contract: ALIVE}),
        AssertHeadStep(latest="z1"),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})
