"""
Tests for EIP-4758 fork transition behavior.

Before the fork, a contract created and self-destructed in the same
transaction is deleted; from the fork on, it persists and its address can
never be reused.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Hash,
    Initcode,
    Op,
    Transaction,
    compute_create_address,
)
from execution_testing import (
    Macros as Om,
)

from .spec import ref_spec_4758

REFERENCE_SPEC_GIT_PATH = ref_spec_4758.git_path
REFERENCE_SPEC_VERSION = ref_spec_4758.version

VICTIM_BALANCE = 0x1234
CANARY = 0xC0DE
SALT = 0
RESULT_OFFSET = 0x100


@pytest.mark.valid_at_transition_to("EIP4758")
def test_same_tx_selfdestruct_across_transition(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Run the same create-and-destroy transaction on both sides of the fork.

    The pre-fork victim is deleted; the post-fork victims persist with
    their code, nonce, and storage.
    """
    beneficiary = pre.fund_eoa(amount=1)
    victim_code = Op.SSTORE(0, CANARY) + Op.SELFDESTRUCT(beneficiary)
    initcode = Initcode(deploy_code=victim_code)
    assert len(initcode) <= RESULT_OFFSET

    factory = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + Op.MSTORE(
            RESULT_OFFSET,
            Op.CREATE(value=VICTIM_BALANCE, size=len(initcode)),
        )
        + Op.SSTORE(Op.CALLDATALOAD(0), Op.MLOAD(RESULT_OFFSET))
        + Op.POP(Op.CALL(address=Op.MLOAD(RESULT_OFFSET))),
        balance=3 * VICTIM_BALANCE,
    )
    victims = [
        compute_create_address(address=factory, nonce=nonce)
        for nonce in (1, 2, 3)
    ]

    sender = pre.fund_eoa()
    blocks = [
        Block(
            timestamp=timestamp,
            txs=[Transaction(sender=sender, to=factory, data=Hash(slot))],
        )
        for slot, timestamp in enumerate((14_999, 15_000, 15_001))
    ]

    persisted = Account(
        nonce=1, code=victim_code, balance=0, storage={0: CANARY}
    )
    post = {
        factory: Account(storage=dict(enumerate(victims))),
        victims[0]: Account.NONEXISTENT,
        victims[1]: persisted,
        victims[2]: persisted,
        beneficiary: Account(balance=1 + 3 * VICTIM_BALANCE),
    }

    blockchain_test(pre=pre, post=post, blocks=blocks)


@pytest.mark.valid_at_transition_to("EIP4758")
def test_create2_recreate_freed_address_across_transition(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Recreate a pre-fork-destroyed CREATE2 address across the fork.

    The pre-fork destruction frees the address, so the first post-fork
    CREATE2 with the same salt succeeds; once that incarnation is swept
    and persists, every further attempt collides.
    """
    beneficiary = pre.fund_eoa(amount=1)
    victim_code = Op.SSTORE(0, CANARY) + Op.SELFDESTRUCT(beneficiary)
    initcode = Initcode(deploy_code=victim_code)
    assert len(initcode) <= RESULT_OFFSET

    canary = 0xDEAD
    factory = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + Op.MSTORE(
            RESULT_OFFSET,
            Op.CREATE2(value=VICTIM_BALANCE, size=len(initcode), salt=SALT),
        )
        + Op.SSTORE(Op.CALLDATALOAD(0), Op.MLOAD(RESULT_OFFSET))
        + Op.POP(Op.CALL(address=Op.MLOAD(RESULT_OFFSET))),
        balance=3 * VICTIM_BALANCE,
        storage=dict.fromkeys(range(3), canary),
    )
    victim = compute_create_address(
        address=factory,
        opcode=Op.CREATE2,
        salt=SALT,
        initcode=initcode,
    )

    sender = pre.fund_eoa()
    blocks = [
        Block(
            timestamp=timestamp,
            txs=[Transaction(sender=sender, to=factory, data=Hash(slot))],
        )
        for slot, timestamp in enumerate((14_999, 15_000, 15_001))
    ]

    post = {
        factory: Account(storage={0: victim, 1: victim, 2: 0}),
        victim: Account(
            nonce=1, code=victim_code, balance=0, storage={0: CANARY}
        ),
        beneficiary: Account(balance=1 + 2 * VICTIM_BALANCE),
    }

    blockchain_test(pre=pre, post=post, blocks=blocks)
