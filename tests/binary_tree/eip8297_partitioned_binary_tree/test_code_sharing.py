"""
Code-sharing tests for the EIP-8297 partitioned binary tree: code is
content-addressed, so byte-identical contracts and same-target
delegations share their chunk leaves, and removing one holder's code
-- by account deletion or by a code change -- must never take a
surviving holder's bytecode with it.

Fixtures observe only per-account state and roots, so these tests pin
execution survival across the events that trigger the shared-leaf
removal check; the leaf-level sharing and removal oracles live in
`tests/binary_trie/test_state_pbt.py`.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Initcode,
    Op,
    Transaction,
    compute_create_address,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_8297

REFERENCE_SPEC_GIT_PATH = ref_spec_8297.git_path
REFERENCE_SPEC_VERSION = ref_spec_8297.version

pytestmark = pytest.mark.valid_from("BinaryTree")


def test_shared_code_survives_sibling_same_tx_selfdestruct(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a contract keeps executing after a byte-identical twin is
    created and self-destructed within one transaction (EIP-6780
    deletes such an account), across the block boundary where the
    tree commits.

    The twin's deletion is the event that triggers the shared-code
    removal check: both contracts hold the same content-addressed
    chunks, so removing the twin must leave the survivor's bytecode
    in place. The twin must self-destruct from its *deployed* code,
    called in its creation transaction -- a SELFDESTRUCT inside
    initcode never deploys, never holds the shared code hash, and
    would exercise nothing.
    """
    slot, value = 1, 0xC0DE
    # calldata[0] != 0 self-destructs; calldata[0] == 0 stores
    # calldata[32:64]. The JUMPDEST lands at byte 13, asserted below.
    branchy = (
        Op.JUMPI(13, Op.CALLDATALOAD(0))
        + Op.SSTORE(slot, Op.CALLDATALOAD(32))
        + Op.STOP
        + Op.JUMPDEST
        + Op.SELFDESTRUCT(Op.CALLER)
    )
    shared_code = branchy + Op.INVALID * (100 - len(branchy))
    assert bytes(shared_code)[13] == 0x5B
    assert len(shared_code) == 100  # four chunks, shared by both twins

    survivor = pre.deploy_contract(code=shared_code)

    # The driver CREATEs the twin from calldata, then CALLs it with a
    # nonzero flag so the twin self-destructs in its own creation
    # transaction.
    driver = pre.deploy_contract(
        code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(0, Op.CREATE(0, 0, Op.CALLDATASIZE))
        + Op.MSTORE(0, 1)
        + Op.SSTORE(
            1,
            Op.CALL(address=Op.SLOAD(0), args_offset=0, args_size=32),
        )
        + Op.STOP
    )
    twin = compute_create_address(address=driver, nonce=1)
    sender = pre.fund_eoa()

    create_and_destroy = Transaction(
        sender=sender,
        to=driver,
        data=bytes(Initcode(deploy_code=shared_code)),
    )
    exercise_survivor = Transaction(
        sender=sender,
        to=survivor,
        data=b"\x00" * 32 + value.to_bytes(32, "big"),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[create_and_destroy]),
            Block(txs=[exercise_survivor]),
        ],
        post={
            driver: Account(nonce=2, storage={0: twin, 1: 1}),
            twin: Account.NONEXISTENT,
            survivor: Account(code=shared_code, storage={slot: value}),
        },
    )


def test_shared_designator_survives_peer_redelegation(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify two EOAs delegating to the same target -- whose designators
    are byte-identical code, one shared chunk in the tree -- stay
    independent when one re-delegates to a different target: the
    other's delegation keeps executing afterwards.

    The re-delegation changes the first authority's code hash, the
    event that triggers the shared-leaf removal check for the old
    designator while its peer still holds it. The two delegates write
    distinct slots and values, so which code each authority executes
    is observable in the post state.
    """
    slot_1, value_1 = 1, 0xD1
    slot_2, value_2 = 2, 0xD2
    delegate_1 = pre.deploy_contract(code=Op.SSTORE(slot_1, value_1) + Op.STOP)
    delegate_2 = pre.deploy_contract(code=Op.SSTORE(slot_2, value_2) + Op.STOP)

    authority_a = pre.fund_eoa(0, delegation=delegate_1)
    authority_b = pre.fund_eoa(0, delegation=delegate_1)
    a_nonce = authority_a.nonce
    sender = pre.fund_eoa()

    redelegate = Transaction(
        sender=sender,
        to=sender,
        authorization_list=[
            AuthorizationTuple(
                address=delegate_2,
                nonce=a_nonce,
                signer=authority_a,
            )
        ],
    )
    exercise_a = Transaction(sender=sender, to=authority_a)
    exercise_b = Transaction(sender=sender, to=authority_b)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[redelegate]),
            Block(txs=[exercise_a, exercise_b]),
        ],
        post={
            authority_a: Account(
                nonce=a_nonce + 1,
                code=Spec7702.delegation_designation(delegate_2),
                storage={slot_2: value_2},
            ),
            authority_b: Account(
                code=Spec7702.delegation_designation(delegate_1),
                storage={slot_1: value_1},
            ),
            delegate_1: Account(storage={}),
            delegate_2: Account(storage={}),
        },
    )
