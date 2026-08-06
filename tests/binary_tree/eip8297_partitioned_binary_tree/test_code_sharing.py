"""
Code-sharing tests for the EIP-8297 partitioned binary tree:
contract code is content-addressed, so byte-identical contracts
share their chunk leaves and removing one holder's code must never
take a surviving holder's bytecode with it. Delegation indicators
are deliberately outside that scheme -- each lives in its own
account's header -- so an authority's delegation is private to it.

Fixtures observe only per-account state and roots, so what these
tests pin is execution survival plus the fixture root a conforming
client must reproduce; the leaf-level oracles live in
`tests/binary_trie/test_state_pbt.py`. Neither test drives the
shared-leaf removal check while filling: a same-transaction twin
never enters the block's pre-state, and a delegation reaches no
shared leaf at all.
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
    StateTestFiller,
    Transaction,
    compute_create_address,
    keccak256,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_8297

REFERENCE_SPEC_GIT_PATH = ref_spec_8297.git_path
REFERENCE_SPEC_VERSION = ref_spec_8297.version

CODE_HASHING_TO_THE_DELEGATION_MARKER = bytes.fromhex(
    "61c0de60015500000000000000000000000000002d6a99"
)
"""
Deployable contract, 23 bytes, whose Keccak hash begins `0xef0100`.

`SSTORE(1, 0xC0DE)` then `STOP`, padded with a ground suffix. It is
both the length of a delegation indicator and hashed to look like
one, so it defeats a discriminator reading the code hash's leading
bytes even where that reader also requires `code_size == 23`.
"""

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

    The twin's deletion never reaches the shared-code removal check
    in this implementation: created and destroyed within one
    transaction, the twin is absent from the block's pre-state, so
    there is no previous account to read a code hash from. Under
    EIP-6780 that is true of every SELFDESTRUCT deletion, which is
    why the removal check's deletion arm lives in handcrafted-diff
    unit tests rather than here. What this fixture pins is the
    committed root: a client that strips the shared chunks when the
    twin goes -- taking the survivor's bytecode with them -- commits
    to a different state root and fails the fixture. The twin still
    must self-destruct from its *deployed* code, called in its
    creation transaction: a SELFDESTRUCT inside initcode never
    deploys and nets the account out of the diff entirely.
    """
    slot, value = 1, 0xC0DE
    # A nonzero first calldata WORD self-destructs; zero stores
    # calldata[32:64]. JUMPI reads the full 32-byte word -- the
    # driver's flag word leaves calldata byte 0 itself as 0x00. The
    # JUMPDEST lands at byte 13, asserted below.
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
    are byte-identical -- stay independent when one re-delegates to a
    different target: the other's delegation keeps executing
    afterwards.

    Each authority holds its designator in its own account header, so
    re-delegating rewrites one leaf and touches nothing the peer
    owns. The two delegates write distinct slots and values, so which
    code each authority executes is observable in the post state; the
    separation of the leaves themselves is pinned in
    `test_state_pbt.py`, and shows up here only in the committed
    root, which a client that shared one leaf between the two would
    not reproduce.
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


def test_contract_hashing_to_the_delegation_marker_executes_as_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a contract whose CODE HASH begins with the delegation
    marker still executes as code.

    This is the attack the header placement is designed against.
    Grinding bytecode until its hash begins `0xef0100` costs about
    2**24 offline hashes, so if a client decided "delegated" by
    reading the leading bytes of the leaf holding the code hash, an
    attacker could deploy this contract and have every such client
    treat it as delegated to an address of their choosing -- here
    bytes 3 through 23 of the hash, which holds no code.

    The difference is visible in the alloc, not only in the state
    root: a conforming client runs the code and the `SSTORE` lands,
    while a client reading the value instead of the key dispatches
    to a codeless address, returns successfully, and writes nothing.
    """
    slot, value = 1, 0xC0DE
    code = CODE_HASHING_TO_THE_DELEGATION_MARKER
    assert keccak256(code)[:3] == b"\xef\x01\x00"
    assert len(code) == 23
    assert code[0] != 0xEF  # deployable: EIP-3541 rejects only 0xEF

    target = pre.deploy_contract(code=code)
    caller = pre.deploy_contract(
        code=Op.SSTORE(0, Op.CALL(address=target)) + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    post = {
        caller: Account(storage={0: 1}),
        target: Account(code=code, storage={slot: value}),
    }
    state_test(pre=pre, post=post, tx=tx)
