"""
Test leanSPHINCS signatures in
[EIP-8141](https://eips.ethereum.org/EIPS/eip-8141) frame transactions.

A `SPHINCS` signature entry carries the 32-byte public key followed by
the 7740-byte signature, and its signer is the address the public key
hashes to. The protocol validates it before any frame executes, like
the other protocol-validated schemes, and the default code accepts it
at the authorizing index, so a codeless account at that address can
send frame transactions. The `SPHINCS_VERIFY` precompile verifies the
same signatures for contracts, such as a wallet that reads an
`ARBITRARY` entry.

An EOA migrates to a leanSPHINCS wallet by adopting the wallet's code
with `SETCODEFROM` ([EIP-8298](https://eips.ethereum.org/EIPS/eip-8298)),
after which its secp256k1 key no longer authorizes it.

Key generation and signing take tens of seconds each; the framework
caches both on disk, so only the first fill of a test pays for them.
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
    Conditional,
    Fork,
    FrameSignature,
    Hash,
    Op,
    SphincsKey,
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

KEY = SphincsKey(bytes((37 * i + 11) % 256 for i in range(32)))
"""
The key of the leanSPHINCS known answer pinned by EthLib's proofs.
"""

KNOWN_ANSWER_MESSAGE = Hash(bytes(7 * i + 3 for i in range(32)))
"""The message of the leanSPHINCS known answer."""

PUBLIC_KEY_LENGTH = 32
SIGNATURE_LENGTH = 7740
ENTRY_SIGNATURE_LENGTH = PUBLIC_KEY_LENGTH + SIGNATURE_LENGTH

SPHINCS_VERIFY = Address(0x101)
"""Address of the `SPHINCS_VERIFY` precompile."""

SPHINCS_VERIFY_GAS = 29_520
"""Gas charged by the `SPHINCS_VERIFY` precompile."""

SLOT_EXECUTED = 0x01
"""Storage slot used by target contracts to record execution."""

APPROVE_ALL = Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT)
"""Approve the transaction's execution and payment."""


def sphincs_entry(
    key: SphincsKey = KEY, *, msg: bytes = b"", signer: bool = True
) -> FrameSignature:
    """
    Return a `SPHINCS` entry signed with `key`, over the canonical
    signature hash when `msg` is empty.

    `signer=False` leaves the signer empty, resolving it to the sender.
    """
    return FrameSignature(
        scheme=Spec.SCHEME_SPHINCS,
        signer=Bytes(key.address) if signer else Bytes(b""),
        msg=Bytes(msg),
        sphincs_key=key,
    )


def signed_entry(
    msg: bytes = bytes(KNOWN_ANSWER_MESSAGE),
    signature: Optional[Callable[[bytes], bytes]] = None,
    signer: Optional[bytes] = None,
) -> Callable[[], FrameSignature]:
    """
    Return a factory for a `SPHINCS` entry of `KEY` over the explicit
    digest `msg`, with its raw signature bytes passed through
    `signature` and its signer replaced by `signer`.

    The entry is built when the test runs, so collection never signs.
    """

    def build() -> FrameSignature:
        raw = KEY.entry_signature(bytes(KNOWN_ANSWER_MESSAGE))
        if signature is not None:
            raw = signature(raw)
        return FrameSignature(
            scheme=Spec.SCHEME_SPHINCS,
            signer=Bytes(KEY.address if signer is None else signer),
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


def sphincs_wallet(address: Address) -> Bytecode:
    """
    Return wallet code that approves the transaction's execution and
    payment in its first frame when signature entry 0 is a protocol-
    validated `SPHINCS` signature from `address` over the canonical
    signature hash, and reverts otherwise.
    """
    authorized = Op.AND(
        Op.EQ(Op.SIGPARAM(0, Spec.SIGPARAM_SCHEME), Spec.SCHEME_SPHINCS),
        Op.AND(
            Op.EQ(Op.SIGPARAM(0, Spec.SIGPARAM_RESOLVED_SIGNER), address),
            Op.ISZERO(Op.SIGPARAM(0, Spec.SIGPARAM_MSG)),
        ),
    )
    return Conditional(
        condition=authorized,
        if_true=APPROVE_ALL,
        if_false=Op.REVERT(0, 0),
    )


def verifier_wallet(address: Address) -> Bytecode:
    """
    Return wallet code that approves the transaction's execution and
    payment when signature entry 0 is an `ARBITRARY` entry carrying a
    leanSPHINCS public key that hashes to `address`, followed by its
    signature of the canonical signature hash, as checked by the
    `SPHINCS_VERIFY` precompile.

    Memory holds the precompile's input: the signature hash, then the
    entry's raw bytes.
    """
    input_length = 32 + ENTRY_SIGNATURE_LENGTH
    verify = (
        Op.MSTORE(0, Op.TXPARAM(Spec.TXPARAM_SIG_HASH))
        + Op.SIGDATACOPY(32, 0, ENTRY_SIGNATURE_LENGTH, 0)
        + Op.MSTORE(
            input_length,
            Op.EQ(
                Op.AND(Op.SHA3(32, PUBLIC_KEY_LENGTH), 2**160 - 1),
                address,
            ),
        )
        + Op.POP(Op.STATICCALL(Op.GAS, SPHINCS_VERIFY, 0, input_length, 0, 32))
    )
    authorized = Op.AND(Op.MLOAD(input_length), Op.EQ(Op.MLOAD(0), 1))
    return verify + Conditional(
        condition=authorized,
        if_true=APPROVE_ALL,
        if_false=Op.REVERT(0, 0),
    )


@pytest.mark.parametrize(
    "explicit_signer",
    [
        pytest.param(True, id="explicit_signer"),
        pytest.param(False, id="empty_signer"),
    ],
)
def test_codeless_sphincs_sender(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    explicit_signer: bool,
) -> None:
    """
    Send a frame transaction from the codeless account at a leanSPHINCS
    key's address: the default code approves execution and payment on
    the `SPHINCS` entry at index 0, and a `SENDER` frame executes.

    An empty signer resolves to the sender, which is the key's address.
    """
    pre.fund_address(KEY.address, 10**18)
    target_code = Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP
    target = pre.deploy_contract(code=target_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=KEY.address,
        frames=[
            verify_frame(),
            sender_frame(target=target, code=target_code),
        ],
        signatures=[sphincs_entry(signer=explicit_signer)],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            KEY.address: Account(nonce=1),
            target: Account(storage={SLOT_EXECUTED: 1}),
        },
    )


@pytest.mark.exception_test
def test_default_code_rejects_explicit_digest(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a frame transaction whose only `SPHINCS` entry signs an
    explicit digest: the entry is valid, but the default code only
    accepts signatures of the canonical signature hash.
    """
    pre.fund_address(KEY.address, 10**18)

    tx = Transaction(
        sender=KEY.address,
        frames=[verify_frame()],
        signatures=[sphincs_entry(msg=bytes(KNOWN_ANSWER_MESSAGE))],
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )

    state_test(pre=pre, tx=tx, post={KEY.address: Account(nonce=0)})


@pytest.mark.exception_test
def test_default_code_rejects_other_signer(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a frame transaction from an EOA whose `SPHINCS` entry at
    index 0 is valid but signed by a different key: the default code
    requires the entry's resolved signer to be the frame's target.
    """
    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        frames=[verify_frame()],
        signatures=[sphincs_entry()],
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=0)})


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
            signed_entry(signature=flip_byte(PUBLIC_KEY_LENGTH)),
            TransactionException.TYPE_6_INVALID_SIGNATURE,
            id="tampered_randomizer",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            signed_entry(signature=flip_byte(ENTRY_SIGNATURE_LENGTH - 1)),
            TransactionException.TYPE_6_INVALID_SIGNATURE,
            id="tampered_top_path",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            # The tampered public key no longer hashes to the signer.
            signed_entry(signature=flip_byte(0)),
            TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
            id="tampered_public_key",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            signed_entry(signature=lambda raw: raw[:-1]),
            TransactionException.TYPE_6_INVALID_SIGNATURE,
            id="truncated",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            signed_entry(signature=lambda raw: raw + b"\x00"),
            TransactionException.TYPE_6_INVALID_SIGNATURE,
            id="extended",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            # The empty signer resolves to the sender, whose address
            # the public key does not hash to.
            signed_entry(signer=b""),
            TransactionException.TYPE_6_INVALID_FRAME_FORMAT,
            id="empty_signer",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_sphincs_entry_validation(
    state_test: StateTestFiller,
    pre: Alloc,
    entry: Callable[[], FrameSignature],
    error: Optional[TransactionException],
) -> None:
    """
    Vary a `SPHINCS` entry over an explicit digest, appended after the
    secp256k1 entry consumed by the sender's default code, and check
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


def test_sphincs_signer_introspection(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Read a `SPHINCS` entry's metadata with `SIGPARAM`: its scheme, its
    explicit digest and its resolved signer, the address its public key
    hashes to.
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
                    slot: Spec.SCHEME_SPHINCS,
                    slot + 1: KNOWN_ANSWER_MESSAGE,
                    slot + 2: KEY.address,
                }
            )
        },
    )


def test_sphincs_wallet_sender(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Send a frame transaction from a wallet contract that approves on a
    protocol-validated `SPHINCS` entry from its owner's key, read with
    `SIGPARAM`.
    """
    sender = pre.deploy_contract(
        code=sphincs_wallet(KEY.address), balance=10**18
    )
    target_code = Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP
    target = pre.deploy_contract(code=target_code)

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[verify_frame(), sender_frame(target=target)],
        signatures=[sphincs_entry()],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=2),
            target: Account(storage={SLOT_EXECUTED: 1}),
        },
    )


@pytest.mark.parametrize(
    "tamper",
    [
        pytest.param(False, id="valid"),
        pytest.param(True, id="tampered", marks=pytest.mark.exception_test),
    ],
)
def test_verifier_wallet_sender(
    state_test: StateTestFiller,
    pre: Alloc,
    tamper: bool,
) -> None:
    """
    Send a frame transaction from a wallet contract that verifies a
    leanSPHINCS signature itself: the signature travels in an
    `ARBITRARY` entry, which the protocol does not validate, and the
    wallet passes it to the `SPHINCS_VERIFY` precompile.

    A tampered signature fails the precompile, so the wallet reverts
    its `VERIFY` frame and the transaction is invalid.
    """
    sender = pre.deploy_contract(
        code=verifier_wallet(KEY.address), balance=10**18
    )
    target_code = Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP
    target = pre.deploy_contract(code=target_code)

    entry = FrameSignature(
        scheme=Spec.SCHEME_ARBITRARY,
        sphincs_key=KEY,
    )
    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[
            verify_frame(gas_limit=200_000),
            sender_frame(target=target),
        ],
        signatures=[entry],
        error=(
            TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
            if tamper
            else None
        ),
    )
    if tamper:
        # The canonical signature hash commits only to the length of
        # the entry's bytes, so flipping one keeps the hash it signs.
        tx.sign()
        assert tx.signatures is not None
        raw = bytearray(tx.signatures[0].signature)
        raw[-1] ^= 0x01
        tx.signatures[0].signature = Bytes(bytes(raw))
        tx.signatures[0].sphincs_key = None

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1 if tamper else 2),
            target: Account(storage={SLOT_EXECUTED: 0 if tamper else 1}),
        },
    )


def precompile_input(
    message: bytes = bytes(KNOWN_ANSWER_MESSAGE),
    tamper: Optional[Callable[[bytes], bytes]] = None,
) -> Callable[[], bytes]:
    """
    Return a factory for `SPHINCS_VERIFY` input: `message`, then `KEY`'s
    public key and its signature of the known answer message, passed
    through `tamper`.
    """

    def build() -> bytes:
        raw = message + KEY.entry_signature(bytes(KNOWN_ANSWER_MESSAGE))
        return tamper(raw) if tamper is not None else raw

    return build


@pytest.mark.parametrize(
    "call_input,gas_delta,valid",
    [
        pytest.param(precompile_input(), 0, True, id="valid"),
        pytest.param(precompile_input(), -1, False, id="out_of_gas"),
        pytest.param(
            precompile_input(message=b"\x00" * 32),
            0,
            False,
            id="other_message",
        ),
        pytest.param(
            precompile_input(tamper=flip_byte(32)),
            0,
            False,
            id="tampered_public_key",
        ),
        pytest.param(
            precompile_input(
                tamper=flip_byte(32 + ENTRY_SIGNATURE_LENGTH - 1)
            ),
            0,
            False,
            id="tampered_signature",
        ),
        pytest.param(
            precompile_input(tamper=lambda raw: raw[:-1]),
            0,
            False,
            id="short_input",
        ),
        pytest.param(
            precompile_input(tamper=lambda raw: raw + b"\x00"),
            0,
            False,
            id="long_input",
        ),
        pytest.param(lambda: b"", 0, False, id="empty_input"),
    ],
)
def test_sphincs_verify_precompile(
    state_test: StateTestFiller,
    pre: Alloc,
    call_input: Callable[[], bytes],
    gas_delta: int,
    valid: bool,
) -> None:
    """
    Call the `SPHINCS_VERIFY` precompile with exactly its gas cost, or
    one less, and check that it returns `1` as a 32-byte word for a
    valid signature, and empty output for anything else.

    The precompile charges its gas for every input, so only running
    out of gas fails the call.
    """
    caller_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            0,
            Op.STATICCALL(
                SPHINCS_VERIFY_GAS + gas_delta,
                SPHINCS_VERIFY,
                0,
                Op.CALLDATASIZE,
                0,
                32,
            ),
        )
        + Op.SSTORE(1, Op.RETURNDATASIZE)
        + Op.SSTORE(2, Op.MLOAD(0))
        + Op.STOP
    )
    caller = pre.deploy_contract(code=caller_code, storage={2: SENTINEL})
    sender = pre.fund_eoa()
    data = call_input()

    tx = Transaction(
        sender=sender,
        to=caller,
        data=data,
        gas_limit=1_000_000,
    )

    # Without output, the first word of memory keeps the input's.
    first_word = int.from_bytes(data[:32], "big")
    if valid:
        storage = {0: 1, 1: 32, 2: 1}
    elif gas_delta < 0:
        storage = {0: 0, 1: 0, 2: first_word}
    else:
        storage = {0: 1, 1: 0, 2: first_word}

    state_test(pre=pre, tx=tx, post={caller: Account(storage=storage)})


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


def test_eoa_migrates_to_sphincs_wallet(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Migrate a secp256k1 EOA to a leanSPHINCS wallet and send a frame
    transaction from it with a `SPHINCS` signature.

    The EOA delegates to a shell that adopts the wallet's code with
    `SETCODEFROM`. The EOA then holds the wallet's code, not a
    delegation, so its address is kept while the wallet's `SPHINCS`
    owner authorizes it.
    """
    wallet_code = sphincs_wallet(KEY.address)
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
        signatures=[sphincs_entry()],
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
    wallet_code = sphincs_wallet(KEY.address)
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
