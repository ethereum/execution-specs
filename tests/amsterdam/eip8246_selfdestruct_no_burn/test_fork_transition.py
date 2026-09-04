"""
Fork transition tests for [EIP-8246: Remove SELFDESTRUCT Burn](https://eips.ethereum.org/EIPS/eip-8246).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Hash,
    Op,
    Transaction,
    compute_create_address,
)
from execution_testing import (
    Macros as Om,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8246

REFERENCE_SPEC_GIT_PATH = ref_spec_8246.git_path
REFERENCE_SPEC_VERSION = ref_spec_8246.version


@pytest.mark.valid_at_transition_to("EIP8246")
@EIPChecklist.Opcode.Test.ForkTransition.At()
def test_selfdestruct_to_self_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    A contract created in the transaction self-destructs to itself. Before
    the fork its balance is burned and the account is deleted; from the fork
    block on the account stays behind holding that balance.
    """
    endowment = 5
    sender = pre.fund_eoa()
    initcode = Op.SELFDESTRUCT(Op.ADDRESS)
    factory = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + Op.SSTORE(
            Op.CALLDATALOAD(0),
            Op.CREATE(value=Op.CALLVALUE, offset=0, size=len(initcode)),
        )
        + Op.STOP
    )
    before = compute_create_address(address=factory, nonce=1)
    at = compute_create_address(address=factory, nonce=2)
    after = compute_create_address(address=factory, nonce=3)

    def create_tx(index: int) -> Transaction:
        return Transaction(
            sender=sender, to=factory, value=endowment, data=Hash(index)
        )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(timestamp=14_999, txs=[create_tx(1)]),
            Block(timestamp=15_000, txs=[create_tx(2)]),
            Block(timestamp=15_001, txs=[create_tx(3)]),
        ],
        post={
            factory: Account(nonce=4, storage={1: before, 2: at, 3: after}),
            before: Account.NONEXISTENT,
            at: Account(balance=endowment, nonce=0, code=b"", storage={}),
            after: Account(balance=endowment, nonce=0, code=b"", storage={}),
        },
    )
