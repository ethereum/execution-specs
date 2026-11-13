"""
Test leanSPHINCS signatures in
[EIP-8141](https://eips.ethereum.org/EIPS/eip-8141) frame transactions.

A `LEANSPHINCS` signature entry carries its 32-byte public key as its
`signer` and its 7740-byte signature as its raw bytes. The protocol
validates it before any frame executes, like the other
protocol-validated schemes, and its resolved signer is the public key
itself, which `SIGPARAM` returns in one word. The default code accepts
only secp256k1 entries, so leanSPHINCS authorizes accounts with code,
such as a wallet that stores its owner's public key.

Such a wallet attests signatures to other contracts with
[EIP-1271](https://eips.ethereum.org/EIPS/eip-1271)'s
`isValidSignature` from a `LEANSPHINCS` entry over an explicit digest in
the current frame transaction, since the EVM cannot verify leanSPHINCS
signatures itself.

An EOA migrates to a leanSPHINCS wallet by adopting the wallet's code
with `SETCODEFROM` ([EIP-8298](https://eips.ethereum.org/EIPS/eip-8298)),
after which its secp256k1 key no longer authorizes it.
"""

from typing import Callable, Optional

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Bytes,
    Fork,
    FrameSignature,
    Hash,
    LeanSphincsKey,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
)

from ..eip8298_setcodefrom.helpers import (
    ADOPT_FROM_CALLDATA,
    RESULT_SLOT,
    SENTINEL,
    word,
)
from .helpers import FrameTransaction, sender_frame, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

KEY = LeanSphincsKey(bytes((37 * i + 11) % 256 for i in range(32)))
"""
The key of the leanSPHINCS known answer pinned by EthLib's proofs.
"""

KNOWN_ANSWER_MESSAGE = Hash(bytes(7 * i + 3 for i in range(32)))
"""The message of the leanSPHINCS known answer."""

PUBLIC_KEY_LENGTH = 32
SIGNATURE_LENGTH = 7740

SLOT_EXECUTED = 0x01
"""Storage slot used by target contracts to record execution."""

APPROVE_ALL = Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT)
"""Approve the transaction's execution and payment."""


def leansphincs_entry(
    key: LeanSphincsKey = KEY, *, msg: bytes = b""
) -> FrameSignature:
    """
    Return a `LEANSPHINCS` entry signed with `key`, over the canonical
    signature hash when `msg` is empty.
    """
    return FrameSignature(
        scheme=Spec.SCHEME_LEANSPHINCS,
        signer=Bytes(key.public_key),
        msg=Bytes(msg),
        leansphincs_key=key,
    )


def signed_entry(
    msg: bytes = bytes(KNOWN_ANSWER_MESSAGE),
    signature: Optional[Callable[[bytes], bytes]] = None,
    signer: Optional[Callable[[bytes], bytes]] = None,
) -> Callable[[], FrameSignature]:
    """
    Return a factory for a `LEANSPHINCS` entry of `KEY` over the
    explicit digest `msg`, with its signature passed through `signature`
    and its signer, the public key, passed through `signer`.

    The entry is built when the test runs, so collection never signs.
    """

    def build() -> FrameSignature:
        raw = KEY.sign(bytes(KNOWN_ANSWER_MESSAGE))
        if signature is not None:
            raw = signature(raw)
        public_key = KEY.public_key
        if signer is not None:
            public_key = signer(public_key)
        return FrameSignature(
            scheme=Spec.SCHEME_LEANSPHINCS,
            signer=Bytes(public_key),
            msg=Bytes(msg),
            signature=Bytes(raw),
        )

    return build


def flip_byte(offset: int) -> Callable[[bytes], bytes]:
    """Return a function flipping the lowest bit of byte `offset`."""

    def flip(raw: bytes) -> bytes:
        tampered = bytearray(raw)
        tampered[offset] ^= 0x01
        return bytes(tampered)

    return flip


def public_key_word(key: LeanSphincsKey) -> int:
    """Return `key`'s public key as the word `SIGPARAM` pushes."""
    return int.from_bytes(key.public_key, "big")


def approving_path(key: LeanSphincsKey, offset: int = 0) -> Bytecode:
    """
    Return the part of `leansphincs_wallet(key)` that runs when it
    approves, which prices the wallet's `VERIFY` frame, placed at
    `offset` in the wallet's code.
    """
    authorized = Op.AND(
        Op.EQ(Op.SIGPARAM(0, Spec.SIGPARAM_SCHEME), Spec.SCHEME_LEANSPHINCS),
        Op.AND(
            Op.EQ(
                Op.SIGPARAM(0, Spec.SIGPARAM_RESOLVED_SIGNER),
                public_key_word(key),
            ),
            Op.ISZERO(Op.SIGPARAM(0, Spec.SIGPARAM_MSG)),
        ),
    )
    rejected = Op.ISZERO(authorized)
    # `rejected`, then PUSH1 of the destination and JUMPI.
    length = len(rejected) + 3 + len(APPROVE_ALL)
    path = Op.JUMPI(offset + length, rejected) + APPROVE_ALL
    assert len(path) == length
    return path


def leansphincs_wallet(key: LeanSphincsKey) -> Bytecode:
    """
    Return wallet code that approves the transaction's execution and
    payment in its first frame when signature entry 0 is a protocol-
    validated `LEANSPHINCS` signature under `key`'s public key over the
    canonical signature hash, and reverts otherwise.
    """
    return approving_path(key) + Op.JUMPDEST + Op.REVERT(0, 0)


@pytest.mark.parametrize(
    "entry,error",
    [
        pytest.param(signed_entry(), None, id="valid"),
        pytest.param(
            signed_entry(msg=b"\x01" * 32),
            TransactionException.TYPE_6_INVALID_SIGNATURE,
            id="other_message",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            signed_entry(signature=flip_byte(0)),
            TransactionException.TYPE_6_INVALID_SIGNATURE,
            id="tampered_randomizer",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            signed_entry(signature=flip_byte(SIGNATURE_LENGTH - 1)),
            TransactionException.TYPE_6_INVALID_SIGNATURE,
            id="tampered_top_path",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            signed_entry(signer=flip_byte(0)),
            TransactionException.TYPE_6_INVALID_SIGNATURE,
            id="other_public_key",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            signed_entry(signature=lambda raw: raw[:-1]),
            TransactionException.TYPE_6_INVALID_SIGNATURE,
            id="truncated_signature",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            signed_entry(signature=lambda raw: raw + b"\x00"),
            TransactionException.TYPE_6_INVALID_SIGNATURE,
            id="extended_signature",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            # A `LEANSPHINCS` signer never resolves to the sender.
            signed_entry(signer=lambda _: b""),
            TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
            id="empty_signer",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            signed_entry(signer=lambda pk: pk[12:]),
            TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
            id="address_length_signer",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            signed_entry(signer=lambda pk: pk[:-1]),
            TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
            id="short_signer",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            signed_entry(signer=lambda pk: pk + b"\x00"),
            TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
            id="long_signer",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_leansphincs_entry_validation(
    state_test: StateTestFiller,
    pre: Alloc,
    entry: Callable[[], FrameSignature],
    error: Optional[TransactionException],
) -> None:
    """
    Vary a `LEANSPHINCS` entry over an explicit digest, appended after
    the secp256k1 entry consumed by the sender's default code, and check
    that the protocol rejects the transaction before execution unless
    the entry is valid.
    """
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[verify_frame()],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
            entry(),
        ],
        error=error,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=0 if error else 1)},
    )


@pytest.mark.exception_test
def test_default_code_rejects_leansphincs(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a frame transaction from an EOA whose only entry is a valid
    `LEANSPHINCS` signature of the canonical signature hash: the
    default code accepts only secp256k1 entries.
    """
    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        frames=[verify_frame()],
        signatures=[leansphincs_entry()],
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=0)})


def test_leansphincs_introspection(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Read a `LEANSPHINCS` entry's metadata with `SIGPARAM`: its scheme,
    its explicit digest and its resolved signer, the full public key.
    """
    sender = pre.fund_eoa()
    slot = 0x10
    target_code = (
        Op.SSTORE(slot, Op.SIGPARAM(1, Spec.SIGPARAM_SCHEME))
        + Op.SSTORE(slot + 1, Op.SIGPARAM(1, Spec.SIGPARAM_MSG))
        + Op.SSTORE(slot + 2, Op.SIGPARAM(1, Spec.SIGPARAM_RESOLVED_SIGNER))
        + Op.STOP
    )
    target = pre.deploy_contract(code=target_code)

    tx = Transaction(
        sender=sender,
        frames=[verify_frame(), sender_frame(target=target)],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
            signed_entry()(),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            target: Account(
                storage={
                    slot: Spec.SCHEME_LEANSPHINCS,
                    slot + 1: KNOWN_ANSWER_MESSAGE,
                    slot + 2: public_key_word(KEY),
                }
            )
        },
    )


@pytest.mark.parametrize(
    "read",
    [
        pytest.param(
            Op.POP(Op.SIGPARAM(1, Spec.SIGPARAM_SIGNATURE_LENGTH)),
            id="sigparam_signature_length",
        ),
        pytest.param(Op.SIGDATACOPY(0, 0, 32, 1), id="sigdatacopy"),
    ],
)
def test_leansphincs_signature_not_introspectable(
    state_test: StateTestFiller,
    pre: Alloc,
    read: Bytecode,
) -> None:
    """
    Halt a frame that reads the length or the bytes of a `LEANSPHINCS`
    entry's signature, which protocol-validated schemes do not expose:
    the frame's write before the read is reverted.
    """
    sender = pre.fund_eoa()
    target_code = Op.SSTORE(SLOT_EXECUTED, 1) + read + Op.STOP
    target = pre.deploy_contract(code=target_code)

    tx = Transaction(
        sender=sender,
        frames=[verify_frame(), sender_frame(target=target)],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
            signed_entry()(),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={target: Account(storage={SLOT_EXECUTED: 0})},
    )


def test_leansphincs_wallet_sender(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Send a frame transaction from a wallet contract that approves on a
    protocol-validated `LEANSPHINCS` entry under its owner's public key,
    read with `SIGPARAM`.

    The transaction's receipt pins the entry's intrinsic cost.
    """
    wallet_code = leansphincs_wallet(KEY)
    sender = pre.deploy_contract(code=wallet_code, balance=10**18)
    target_code = Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP
    target = pre.deploy_contract(code=target_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[
            verify_frame(code=approving_path(KEY)),
            sender_frame(target=target, code=target_code),
        ],
        signatures=[leansphincs_entry()],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=2),
            target: Account(storage={SLOT_EXECUTED: 1}),
        },
    )


@pytest.mark.exception_test
def test_leansphincs_wallet_rejects_other_key(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a frame transaction whose valid `LEANSPHINCS` entry is under
    a public key other than the wallet owner's.
    """
    other = LeanSphincsKey(bytes(range(32)))
    sender = pre.deploy_contract(code=leansphincs_wallet(KEY), balance=10**18)

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[verify_frame()],
        signatures=[leansphincs_entry(other)],
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


def migrate(eoa: EOA, shell: Address, source: Address) -> Transaction:
    """
    Return the self-sponsored type-4 transaction that delegates `eoa` to
    `shell` and calls it to adopt the code of `source`.
    """
    return Transaction(
        sender=eoa,
        to=eoa,
        data=word(source),
        authorization_list=[
            AuthorizationTuple(address=shell, nonce=1, signer=eoa)
        ],
    )


def test_eoa_migrates_to_leansphincs_wallet(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Migrate a secp256k1 EOA to a leanSPHINCS wallet and send a frame
    transaction from it with a `LEANSPHINCS` signature.

    The EOA delegates to a shell that adopts the wallet's code with
    `SETCODEFROM`. The EOA then holds the wallet's code, not a
    delegation, so its address is kept while the wallet's leanSPHINCS
    owner authorizes it.
    """
    wallet_code = leansphincs_wallet(KEY)
    wallet = pre.deploy_contract(code=wallet_code)
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    eoa = pre.fund_eoa()
    target_code = Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP
    target = pre.deploy_contract(code=target_code)

    frame_tx = Transaction(
        sender=eoa,
        nonce=2,
        frames=[verify_frame(), sender_frame(target=target)],
        signatures=[leansphincs_entry()],
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[migrate(eoa, shell, wallet)]),
            Block(txs=[frame_tx]),
        ],
        post={
            eoa: Account(code=wallet_code, nonce=3, storage={RESULT_SLOT: 1}),
            target: Account(storage={SLOT_EXECUTED: 1}),
        },
    )


@pytest.mark.exception_test
def test_migrated_eoa_rejects_secp256k1(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a frame transaction authorized by the secp256k1 key of an EOA
    that migrated to a leanSPHINCS wallet: the EOA has code, so the
    default code no longer runs, and the wallet rejects the entry.
    """
    wallet_code = leansphincs_wallet(KEY)
    wallet = pre.deploy_contract(code=wallet_code)
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    eoa = pre.fund_eoa()

    frame_tx = Transaction(
        sender=eoa,
        nonce=2,
        frames=[verify_frame()],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(eoa)),
        ],
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[migrate(eoa, shell, wallet)]),
            Block(
                txs=[frame_tx],
                exception=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
            ),
        ],
        post={eoa: Account(code=wallet_code, nonce=2)},
    )


IS_VALID_SIGNATURE = 0x1626BA7E
"""
Selector of `isValidSignature(bytes32,bytes)`, which is also the value it
returns for a valid signature.
"""

VALID = IS_VALID_SIGNATURE << 224
"""The word `isValidSignature` returns for a valid signature."""

SLOT_CALL_SUCCESS = 0x10
SLOT_RESULT = 0x11

CHECK_GAS = 20_000
"""Gas the verifier gives `isValidSignature`."""

VERIFIER_CODE = (
    Op.CALLDATACOPY(0, 32, Op.SUB(Op.CALLDATASIZE, 32))
    + Op.SSTORE(
        SLOT_CALL_SUCCESS,
        Op.STATICCALL(
            CHECK_GAS,
            Op.CALLDATALOAD(0),
            0,
            Op.SUB(Op.CALLDATASIZE, 32),
            0x100,
            32,
        ),
    )
    + Op.SSTORE(SLOT_RESULT, Op.MLOAD(0x100))
    + Op.STOP
)
"""
Contract that asks the account in its first calldata word whether a
signature is valid, forwarding the rest of its calldata, and stores
whether the call succeeded and what it returned.
"""


def attested_hash(wallet: Address, digest: Hash) -> Hash:
    """Return the digest the owner signs to attest `digest` to `wallet`."""
    return Hash(Bytes(bytes(wallet) + bytes(digest)).keccak256())


def attesting_path(key: LeanSphincsKey) -> Bytecode:
    """
    Return code answering `isValidSignature(hash, signature)`, where
    `signature` is the index of a signature entry of the current
    transaction: valid when the entry is a `LEANSPHINCS` entry under
    `key`'s public key over `attested_hash(ADDRESS, hash)`.
    """
    # Calldata: selector, hash, offset and length of `signature`, index.
    index = Op.CALLDATALOAD(100)
    valid = Op.AND(
        Op.EQ(
            Op.SIGPARAM(index, Spec.SIGPARAM_SCHEME), Spec.SCHEME_LEANSPHINCS
        ),
        Op.AND(
            Op.EQ(
                Op.SIGPARAM(index, Spec.SIGPARAM_RESOLVED_SIGNER),
                public_key_word(key),
            ),
            Op.EQ(Op.SIGPARAM(index, Spec.SIGPARAM_MSG), Op.SHA3(12, 52)),
        ),
    )
    return (
        Op.MSTORE(0, Op.ADDRESS)
        + Op.MSTORE(32, Op.CALLDATALOAD(4))
        + Op.MSTORE(0, Op.MUL(valid, VALID))
        + Op.RETURN(0, 32)
    )


def attesting_wallet(key: LeanSphincsKey) -> Bytecode:
    """
    Return `leansphincs_wallet(key)` extended to answer
    `isValidSignature` when called with calldata.
    """
    dispatch_length = len(Op.JUMPI(0xFF, Op.CALLDATASIZE))
    rejecting = (
        approving_path(key, offset=dispatch_length)
        + Op.JUMPDEST
        + Op.REVERT(0, 0)
    )
    destination = dispatch_length + len(rejecting)
    assert destination < 0x100
    return (
        Op.JUMPI(destination, Op.CALLDATASIZE)
        + rejecting
        + Op.JUMPDEST
        + attesting_path(key)
    )


def is_valid_signature_call(
    wallet: Address, digest: Hash, index: int
) -> Bytes:
    """
    Return the verifier's calldata asking `wallet` whether signature
    entry `index` signs `digest`.
    """
    return Bytes(
        bytes(word(wallet))
        + IS_VALID_SIGNATURE.to_bytes(4, "big")
        + bytes(digest)
        + (0x40).to_bytes(32, "big")
        + (32).to_bytes(32, "big")
        + index.to_bytes(32, "big")
    )


ATTESTED = Hash(0xA77E57ED)
"""The hash a dapp asks the wallet about."""


@pytest.mark.parametrize("submitter", ["relayer", "wallet"])
def test_leansphincs_wallet_attests_signature(
    state_test: StateTestFiller,
    pre: Alloc,
    submitter: str,
) -> None:
    """
    Attest a hash from a leanSPHINCS wallet to a contract that calls its
    `isValidSignature`, with the owner's `LEANSPHINCS` entry over the
    attested hash in the frame transaction that makes the call.

    The transaction is sent by a relayer or by the wallet itself.
    """
    wallet = pre.deploy_contract(code=attesting_wallet(KEY), balance=10**18)
    verifier = pre.deploy_contract(
        code=VERIFIER_CODE,
        storage={SLOT_CALL_SUCCESS: SENTINEL, SLOT_RESULT: SENTINEL},
    )
    attestation = leansphincs_entry(msg=attested_hash(wallet, ATTESTED))
    call = sender_frame(
        target=verifier, data=is_valid_signature_call(wallet, ATTESTED, 1)
    )

    if submitter == "relayer":
        relayer = pre.fund_eoa()
        tx = Transaction(
            sender=relayer,
            frames=[verify_frame(), call],
            signatures=[
                FrameSignature(
                    scheme=Spec.SCHEME_SECP256K1, signer=Bytes(relayer)
                ),
                attestation,
            ],
        )
    elif submitter == "wallet":
        tx = Transaction(
            sender=wallet,
            nonce=1,
            frames=[verify_frame(), call],
            signatures=[leansphincs_entry(), attestation],
        )
    else:
        raise ValueError(submitter)

    state_test(
        pre=pre,
        tx=tx,
        post={
            verifier: Account(
                storage={SLOT_CALL_SUCCESS: 1, SLOT_RESULT: VALID}
            )
        },
    )


@pytest.mark.parametrize(
    "case",
    ["other_hash", "other_wallet", "other_key", "missing_entry"],
)
def test_leansphincs_wallet_rejects_attestation(
    state_test: StateTestFiller,
    pre: Alloc,
    case: str,
) -> None:
    """
    Answer `isValidSignature` as invalid when the referenced entry does
    not attest the hash to the wallet under the owner's key, and fail
    the call when the entry does not exist.

    Two wallets of the same key do not share attestations, since the
    owner signs the hash bound to one wallet's address.
    """
    wallet = pre.deploy_contract(code=attesting_wallet(KEY))
    verifier = pre.deploy_contract(
        code=VERIFIER_CODE,
        storage={SLOT_CALL_SUCCESS: SENTINEL, SLOT_RESULT: SENTINEL},
    )
    relayer = pre.fund_eoa()
    key, signed, asked, queried, index = KEY, wallet, ATTESTED, wallet, 1
    call_success = 1

    if case == "other_hash":
        asked = Hash(0xA77E57EE)
    elif case == "other_wallet":
        queried = pre.deploy_contract(code=attesting_wallet(KEY))
    elif case == "other_key":
        key = LeanSphincsKey(bytes(range(32)))
    elif case == "missing_entry":
        # `SIGPARAM` halts on an out-of-bounds index.
        index, call_success = 2, 0
    else:
        raise ValueError(case)

    tx = Transaction(
        sender=relayer,
        frames=[
            verify_frame(),
            sender_frame(
                target=verifier,
                data=is_valid_signature_call(queried, asked, index),
            ),
        ],
        signatures=[
            FrameSignature(
                scheme=Spec.SCHEME_SECP256K1, signer=Bytes(relayer)
            ),
            leansphincs_entry(key, msg=attested_hash(signed, ATTESTED)),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            verifier: Account(
                storage={SLOT_CALL_SUCCESS: call_success, SLOT_RESULT: 0}
            )
        },
    )


@pytest.mark.frame_tx_incompatible
def test_leansphincs_wallet_cannot_attest_outside_frame_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Fail a leanSPHINCS wallet's `isValidSignature` in a transaction that
    is not a frame transaction, which has no signature entries for
    `SIGPARAM` to read.
    """
    wallet = pre.deploy_contract(code=attesting_wallet(KEY))
    verifier = pre.deploy_contract(
        code=VERIFIER_CODE,
        storage={SLOT_CALL_SUCCESS: SENTINEL, SLOT_RESULT: SENTINEL},
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=verifier,
        data=is_valid_signature_call(wallet, ATTESTED, 0),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            verifier: Account(storage={SLOT_CALL_SUCCESS: 0, SLOT_RESULT: 0})
        },
    )
