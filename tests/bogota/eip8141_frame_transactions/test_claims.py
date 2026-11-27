"""
Tests for the declarative claims of
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A claim names a verifier, a key and a message; the witness that
satisfies it is segregated from the transaction and travels in the
block's dependency proof. Every claim must be satisfied before any frame
executes, and frames test for one with `HASCLAIM`.

The rules decidable from the transaction body alone are in
`test_static_validity.py`, and the gas a witness costs in
`test_witness_gas.py`.
"""

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import pytest
from ethereum_rlp import rlp
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Bytecode,
    Bytes,
    Claim,
    Conditional,
    Fork,
    Frame,
    Hash,
    Header,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    compute_create_address,
    keccak256,
)

from .claim_helpers import (
    DIGEST,
    P256_S,
    P256_SIGNATURE,
    P256_SIGNER,
    SECP256K1N,
    SECP256R1N,
    canonical_claim,
    high_s_complement,
    p256_claim,
    resized_witness,
    signed_digest_claim,
    valid_p256_claim,
    with_tampered_components,
)
from .helpers import APPROVE_ALL
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

FOREIGN_KEY = Address(0x1234)
"""An address no test key signs for."""

OTHER_KEY = Hash(0x0BAD)
"""A key signing claims on behalf of an account other than the sender."""

VERIFIER_GAS = 100_000
"""Gas limit of the custom verifier claims, ample for every verifier."""

SLOT_RESULT = 0x01
"""Storage slot a probe writes what it read into."""


def custom_claim(
    verifier: Address, witness: bytes = b"", **overrides: Any
) -> Claim:
    """
    Return a claim of the custom contract `verifier` over `DIGEST` with
    `witness`, overridden field by field.
    """
    fields: Dict[str, Any] = dict(
        verifier=verifier,
        msg=Bytes(DIGEST),
        gas_limit=VERIFIER_GAS,
        witness_len=len(witness),
        witness=Bytes(witness),
    )
    fields.update(overrides)
    return Claim(**fields)


# --- Witness verification --- #

WITNESS_CASES = [
    # secp256k1 witnesses, built from a valid signature over an
    # explicit digest and tampered in a single component.
    pytest.param(
        lambda _pre, sender: [signed_digest_claim(sender.key)],
        None,
        id="secp256k1_digest_claim",
    ),
    pytest.param(
        lambda _pre, sender: [
            resized_witness(signed_digest_claim(sender.key), 64)
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_witness_too_short",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            resized_witness(signed_digest_claim(sender.key), 66)
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_witness_too_long",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            resized_witness(signed_digest_claim(sender.key), 0)
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_witness_empty",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            with_tampered_components(signed_digest_claim(sender.key), v=2)
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_v_2",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The legacy transaction v encoding is not valid here.
        lambda _pre, sender: [
            with_tampered_components(signed_digest_claim(sender.key), v=27)
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_v_27",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            with_tampered_components(signed_digest_claim(sender.key), r=0)
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_r_zero",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            with_tampered_components(
                signed_digest_claim(sender.key), r=SECP256K1N
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_r_at_curve_order",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            with_tampered_components(
                signed_digest_claim(sender.key), r=SECP256K1N - 1
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_r_not_on_curve",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            with_tampered_components(
                signed_digest_claim(sender.key), r=SECP256K1N - 2
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_r_recovers_stranger",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            with_tampered_components(signed_digest_claim(sender.key), s=0)
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_s_zero",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda _pre, sender: [
            high_s_complement(signed_digest_claim(sender.key))
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_high_s",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # A valid signature under a key other than the one recovered.
        lambda _pre, sender: [
            signed_digest_claim(sender.key, key=Bytes(FOREIGN_KEY))
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_key_mismatch",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # An empty key resolves to the sender, but the witness is signed
        # with an unrelated key.
        lambda _pre, _sender: [signed_digest_claim(OTHER_KEY, key=Bytes())],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="secp256k1_empty_key_wrong_signer",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The resolved key, not the declared one, is what the witness
        # must match: the sender's address padded to a word.
        lambda _pre, sender: [
            signed_digest_claim(
                sender.key, key=Bytes(bytes(12) + bytes(sender))
            )
        ],
        None,
        id="secp256k1_word_key",
    ),
    # P-256 witnesses.
    pytest.param(
        [
            Claim(
                verifier=Spec.P256_VERIFIER,
                key=Bytes(P256_SIGNER),
                msg=Bytes(DIGEST),
                witness=Bytes(P256_SIGNATURE),
            )
        ],
        None,
        id="p256_valid_claim",
    ),
    pytest.param(
        [
            Claim(
                verifier=Spec.P256_VERIFIER,
                key=Bytes(P256_SIGNER),
                msg=Bytes(DIGEST),
                witness=Bytes(P256_SIGNATURE[:127]),
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_witness_too_short",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            Claim(
                verifier=Spec.P256_VERIFIER,
                key=Bytes(P256_SIGNER),
                msg=Bytes(DIGEST),
                witness=Bytes(P256_SIGNATURE + b"\x00"),
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_witness_too_long",
        marks=pytest.mark.exception_test,
    ),
    # Each claim below keeps the valid public key words and the key they
    # hash to, so only the rule on the tampered component is broken.
    pytest.param(
        [valid_p256_claim(r=0)],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_r_zero",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [valid_p256_claim(r=SECP256R1N)],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_r_at_curve_order",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [valid_p256_claim(s=0)],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_s_zero",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The high-`s` complement is algebraically valid but rejected by
        # the canonical-encoding rule, as for secp256k1.
        [valid_p256_claim(s=SECP256R1N - P256_S)],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_high_s",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The empty key resolves to the sender, which never matches the
        # hash of the witness's public key words.
        [p256_claim(r=1, s=1)],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_key_mismatch",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The key matches the public key words, but (0, 0) is not a point
        # on the P-256 curve.
        [p256_claim(r=1, s=1, key=Bytes(keccak256(b"\x00" * 64)[12:]))],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_not_on_curve",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # A well-formed signature over a different digest than the
        # claim's msg.
        [
            Claim(
                verifier=Spec.P256_VERIFIER,
                key=Bytes(P256_SIGNER),
                msg=Bytes(b"\x02" * 32),
                witness=Bytes(P256_SIGNATURE),
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="p256_signature_over_different_digest",
        marks=pytest.mark.exception_test,
    ),
    # leanSPHINCS witnesses.
    pytest.param(
        [
            Claim(
                verifier=Spec.LEANSPHINCS_VERIFIER,
                key=Bytes(b"\x01" * 32),
                msg=Bytes(DIGEST),
                witness=Bytes(bytes(Spec.LEANSPHINCS_SIGNATURE_SIZE - 1)),
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="leansphincs_witness_too_short",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        [
            Claim(
                verifier=Spec.LEANSPHINCS_VERIFIER,
                key=Bytes(b"\x01" * 32),
                msg=Bytes(DIGEST),
                witness=Bytes(bytes(Spec.LEANSPHINCS_SIGNATURE_SIZE)),
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="leansphincs_invalid_signature",
        marks=pytest.mark.exception_test,
    ),
    # Custom verifier witnesses must be exactly `witness_len` long.
    pytest.param(
        lambda pre, _sender: [
            custom_claim(
                pre.deploy_contract(code=Op.STOP),
                witness=b"\x01" * 4,
                witness_len=5,
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="custom_witness_shorter_than_declared",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        lambda pre, _sender: [
            custom_claim(
                pre.deploy_contract(code=Op.STOP),
                witness=b"\x01" * 6,
                witness_len=5,
            )
        ],
        TransactionException.TYPE_6_INVALID_SIGNATURE,
        id="custom_witness_longer_than_declared",
        marks=pytest.mark.exception_test,
    ),
    # Repeated claims share one dependency.
    pytest.param(
        lambda _pre, sender: [
            signed_digest_claim(sender.key),
            signed_digest_claim(sender.key),
        ],
        None,
        id="repeated_claim",
    ),
]
"""
Witnesses of a claim appended after the sender's claim, each with the
exception the transaction must be rejected with, or `None` where the
witness satisfies its claim.
"""


@pytest.mark.parametrize("claims,error", WITNESS_CASES)
def test_witness_verification(
    state_test: StateTestFiller,
    pre: Alloc,
    claims: List[Claim] | Callable[[Alloc, EOA], List[Claim]],
    error: Optional[TransactionException],
) -> None:
    """
    Verify the witness of a claim appended to a minimal frame
    transaction against its protocol or custom verifier: a witness that
    does not satisfy its claim invalidates the transaction.
    """
    sender = pre.fund_eoa()
    case_claims = claims(pre, sender) if callable(claims) else claims
    tx = Transaction(
        sender=sender,
        frames=[Frame.verify()],
        claims=[sender, *case_claims],
        error=error,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=0 if error else 1)},
    )


@pytest.mark.exception_test
@pytest.mark.parametrize(
    "witnesses",
    [
        pytest.param(lambda _signed: [], id="no_witnesses"),
        pytest.param(lambda signed: signed[:1], id="one_witness_missing"),
    ],
)
def test_missing_witness(
    state_test: StateTestFiller,
    pre: Alloc,
    witnesses: Callable[[List[Bytes]], List[Bytes]],
) -> None:
    """
    Reject a transaction whose claims are not all matched by a witness:
    a claim without a witness is unsatisfied.
    """
    sender = pre.fund_eoa()
    unsigned = Transaction(
        sender=sender,
        frames=[Frame.verify()],
        claims=[sender, signed_digest_claim(OTHER_KEY)],
    )
    signed = unsigned.with_signature_and_sender().witnesses
    assert signed is not None
    tx = Transaction(
        sender=sender,
        frames=[Frame.verify()],
        claims=[sender, signed_digest_claim(OTHER_KEY)],
        witnesses=witnesses(signed),
        error=TransactionException.TYPE_6_INVALID_SIGNATURE,
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=0)})


# --- HASCLAIM --- #

CUSTOM_KEY = Bytes(b"\x11" * 32)
"""Key of the custom verifier claim `HASCLAIM` is probed against."""

CUSTOM_MSG = Bytes(b"\x22" * 32)
"""Message of the custom verifier claim `HASCLAIM` is probed against."""

VERIFIER_HIGH_BIT = 1 << 160
"""A bit above the 20 address bytes of a `HASCLAIM` verifier operand."""


def word(operand: Any) -> int | Bytecode:
    """
    Return a `HASCLAIM` operand as a stack word: bytes left-padded to 32
    bytes, an integer or bytecode as given.
    """
    if isinstance(operand, (int, Bytecode)):
        return operand
    return int.from_bytes(bytes(operand).rjust(32, b"\x00"), "big")


@pytest.mark.parametrize(
    "query,expected",
    [
        pytest.param(
            lambda s, _o, _v: (Spec.SECP256K1_VERIFIER, s, 0),
            1,
            id="sender_over_sig_hash",
        ),
        pytest.param(
            lambda s, _o, _v: (Spec.SECP256K1_VERIFIER, s, DIGEST),
            0,
            id="sender_over_digest",
        ),
        pytest.param(
            lambda _s, o, _v: (Spec.SECP256K1_VERIFIER, o, DIGEST),
            1,
            id="other_over_digest",
        ),
        pytest.param(
            lambda _s, o, _v: (Spec.SECP256K1_VERIFIER, o, 0),
            0,
            id="other_over_sig_hash",
        ),
        pytest.param(
            # A non-zero message matches only explicit messages, so the
            # signature hash itself never matches a claim over it.
            lambda s, _o, _v: (
                Spec.SECP256K1_VERIFIER,
                s,
                Op.TXPARAM(Spec.TXPARAM_SIG_HASH),
            ),
            0,
            id="sender_over_explicit_sig_hash",
        ),
        pytest.param(
            lambda _s, _o, _v: (Spec.P256_VERIFIER, P256_SIGNER, DIGEST),
            1,
            id="p256_signer_over_digest",
        ),
        pytest.param(
            lambda _s, o, _v: (Spec.P256_VERIFIER, o, DIGEST),
            0,
            id="other_under_wrong_verifier",
        ),
        pytest.param(
            lambda _s, _o, v: (v, CUSTOM_KEY, CUSTOM_MSG),
            1,
            id="custom_claim",
        ),
        pytest.param(
            lambda _s, _o, v: (v, CUSTOM_KEY, DIGEST),
            0,
            id="custom_claim_other_msg",
        ),
        pytest.param(
            lambda _s, _o, v: (v, Bytes(b"\x11" * 31), CUSTOM_MSG),
            0,
            id="custom_claim_other_key",
        ),
        pytest.param(
            lambda s, _o, _v: (
                int.from_bytes(Spec.SECP256K1_VERIFIER, "big")
                | VERIFIER_HIGH_BIT,
                s,
                0,
            ),
            0,
            id="verifier_with_upper_bytes",
        ),
    ],
)
def test_hasclaim(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    query: Callable[[EOA, EOA, Address], Tuple[Any, Any, Any]],
    expected: int,
) -> None:
    """
    Test for a claim with `HASCLAIM` from a `DEFAULT` frame. The
    transaction declares the sender's claim over the canonical signature
    hash, another account's and a P-256 key's claims over an explicit
    digest, and a custom verifier's claim under a 32-byte key.

    The frame's receipt pins the instruction's gas cost.
    """
    sender = pre.fund_eoa()
    other = EOA(key=OTHER_KEY)
    verifier = pre.deploy_contract(code=Op.STOP)
    probe_code = (
        # Store one more than the result, so both results write a
        # non-zero value at the same price.
        Op.SSTORE(
            SLOT_RESULT,
            Op.ADD(
                1,
                Op.HASCLAIM(
                    *(
                        word(operand)
                        for operand in query(sender, other, verifier)
                    )
                ),
            ),
        )
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)

    tx = Transaction(
        sender=sender,
        frames=[
            Frame.verify(),
            Frame.default(target=probe, code=probe_code),
        ],
        claims=[
            sender,
            signed_digest_claim(OTHER_KEY),
            Claim(
                verifier=Spec.P256_VERIFIER,
                key=Bytes(P256_SIGNER),
                msg=Bytes(DIGEST),
                witness=Bytes(P256_SIGNATURE),
            ),
            custom_claim(verifier, key=CUSTOM_KEY, msg=CUSTOM_MSG),
        ],
    ).resolve_frames(fork)

    state_test(
        pre=pre,
        tx=tx,
        post={probe: Account(storage={SLOT_RESULT: expected + 1})},
    )


def test_hasclaim_outside_frame_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Halt on `HASCLAIM` outside a frame transaction. The probe writes a
    marker before the instruction, so a `HASCLAIM` that returned instead
    of halting would leave the marker behind.
    """
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_RESULT, 1) + Op.POP(Op.HASCLAIM(0, 0, 0))
    )
    tx = Transaction(sender=pre.fund_eoa(), to=probe, gas_limit=100_000)

    state_test(
        pre=pre,
        tx=tx,
        post={probe: Account(storage={SLOT_RESULT: 0})},
    )


# --- Default code --- #


@pytest.mark.exception_test
def test_default_code_requires_empty_frame_data(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a `VERIFY` frame running default code with data: default code
    reverts, invalidating the transaction, although the sender's claim is
    declared.
    """
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[Frame.verify(data=Bytes(b"\x00"))],
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=0)})


@pytest.mark.parametrize(
    "claims",
    [
        pytest.param(
            lambda sender, _verifier: [
                signed_digest_claim(OTHER_KEY),
                Claim(
                    verifier=Spec.P256_VERIFIER,
                    key=Bytes(P256_SIGNER),
                    msg=Bytes(DIGEST),
                    witness=Bytes(P256_SIGNATURE),
                ),
                sender,
            ],
            id="sender_claim_last",
        ),
        pytest.param(
            lambda sender, _verifier: [canonical_claim(sender)],
            id="sender_address_as_key",
        ),
        pytest.param(
            lambda sender, _verifier: [
                canonical_claim(sender, key=Bytes(bytes(12) + bytes(sender)))
            ],
            id="sender_address_padded_as_key",
        ),
    ],
)
def test_default_code_finds_claim(
    state_test: StateTestFiller,
    pre: Alloc,
    claims: Callable[[EOA, Address], List[Claim | EOA]],
) -> None:
    """
    Approve through default code whatever the position of the sender's
    claim among the others, and however its key spells the sender: the
    claim is found by its verifier, resolved key and message.
    """
    sender = pre.fund_eoa()
    verifier = pre.deploy_contract(code=Op.STOP)
    tx = Transaction(
        sender=sender,
        frames=[Frame.verify()],
        claims=claims(sender, verifier),
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


@pytest.mark.exception_test
@pytest.mark.parametrize(
    "claim",
    [
        pytest.param(
            # A custom verifier that accepts anything vouches for the
            # sender's key over the canonical hash, but default code only
            # trusts the secp256k1 protocol verifier.
            lambda sender, verifier: custom_claim(
                verifier, key=Bytes(sender), msg=Bytes()
            ),
            id="custom_verifier",
        ),
        pytest.param(
            # A satisfied claim over the canonical hash, keyed by another
            # account than the sender.
            lambda _sender, _verifier: canonical_claim(EOA(key=OTHER_KEY)),
            id="other_key",
        ),
    ],
)
def test_default_code_refuses_claim(
    state_test: StateTestFiller,
    pre: Alloc,
    claim: Callable[[EOA, Address], Claim],
) -> None:
    """
    Refuse approval through default code without a satisfied
    `SECP256K1_VERIFIER` claim keyed by the sender over the canonical
    hash, invalidating the transaction.
    """
    sender = pre.fund_eoa()
    verifier = pre.deploy_contract(code=Op.STOP)
    tx = Transaction(
        sender=sender,
        frames=[Frame.verify()],
        claims=[claim(sender, verifier)],
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=0)})


# --- Custom verifiers and the pure context --- #

PURE_CONTEXT_CASES = [
    # Instructions reading the call's context, other accounts, the chain,
    # the block or the transaction.
    *(
        pytest.param(
            code,
            False,
            id=f"forbidden_{name}",
            marks=pytest.mark.exception_test,
        )
        for name, code in [
            ("address", Op.POP(Op.ADDRESS)),
            ("balance", Op.POP(Op.BALANCE(0))),
            ("origin", Op.POP(Op.ORIGIN)),
            ("caller", Op.POP(Op.CALLER)),
            ("gasprice", Op.POP(Op.GASPRICE)),
            ("extcodesize", Op.POP(Op.EXTCODESIZE(0))),
            ("extcodecopy", Op.EXTCODECOPY(0, 0, 0, 0)),
            ("extcodehash", Op.POP(Op.EXTCODEHASH(0))),
            ("blockhash", Op.POP(Op.BLOCKHASH(0))),
            ("coinbase", Op.POP(Op.COINBASE)),
            ("timestamp", Op.POP(Op.TIMESTAMP)),
            ("number", Op.POP(Op.NUMBER)),
            ("prevrandao", Op.POP(Op.PREVRANDAO)),
            ("gaslimit", Op.POP(Op.GASLIMIT)),
            ("chainid", Op.POP(Op.CHAINID)),
            ("selfbalance", Op.POP(Op.SELFBALANCE)),
            ("basefee", Op.POP(Op.BASEFEE)),
            ("blobhash", Op.POP(Op.BLOBHASH(0))),
            ("blobbasefee", Op.POP(Op.BLOBBASEFEE)),
            ("slotnum", Op.POP(Op.SLOTNUM)),
            ("sload", Op.POP(Op.SLOAD(0))),
            ("tload", Op.POP(Op.TLOAD(0))),
            ("approve", Op.APPROVE(0, 0, 0)),
            ("txparam", Op.POP(Op.TXPARAM(Spec.TXPARAM_SIG_HASH))),
            ("framedataload", Op.POP(Op.FRAMEDATALOAD(0, 0))),
            ("framedatacopy", Op.FRAMEDATACOPY(0, 0, 0, 0)),
            ("frameparam", Op.POP(Op.FRAMEPARAM(0, 0))),
            ("hasclaim", Op.POP(Op.HASCLAIM(0, 0, 0))),
            # Calls other than `STATICCALL` to an active precompile.
            ("call_precompile", Op.POP(Op.CALL(gas=Op.GAS, address=4))),
            ("callcode", Op.POP(Op.CALLCODE(gas=Op.GAS, address=4))),
            (
                "delegatecall",
                Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=4)),
            ),
            (
                "staticcall_account",
                Op.POP(Op.STATICCALL(gas=Op.GAS, address=0x5A5A)),
            ),
            # The restrictions of a static call.
            ("sstore", Op.SSTORE(0, 1)),
            ("tstore", Op.TSTORE(0, 1)),
            ("log0", Op.LOG0(0, 0)),
            ("create", Op.POP(Op.CREATE(0, 0, 0))),
            ("selfdestruct", Op.SELFDESTRUCT(0)),
        ]
    ),
    # What a pure function of the input and the verifier's code may use.
    *(
        pytest.param(code, True, id=f"allowed_{name}")
        for name, code in [
            ("callvalue", Op.POP(Op.CALLVALUE)),
            ("calldataload", Op.POP(Op.CALLDATALOAD(0))),
            ("calldatasize", Op.POP(Op.CALLDATASIZE)),
            ("calldatacopy", Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)),
            ("codesize", Op.POP(Op.CODESIZE)),
            ("codecopy", Op.CODECOPY(0, 0, Op.CODESIZE)),
            ("gas", Op.POP(Op.GAS)),
            ("keccak256", Op.POP(Op.SHA3(0, 32))),
            ("returndatasize", Op.POP(Op.RETURNDATASIZE)),
            (
                "staticcall_identity",
                Op.POP(
                    Op.STATICCALL(
                        gas=Op.GAS, address=4, args_offset=0, args_size=32
                    )
                ),
            ),
            (
                "staticcall_sha256",
                Op.POP(
                    Op.STATICCALL(
                        gas=Op.GAS, address=2, args_offset=0, args_size=32
                    )
                ),
            ),
        ]
    ),
]
"""
Code a custom verifier runs before `STOP`, with whether the pure context
lets it succeed.
"""


@pytest.mark.parametrize("code,succeeds", PURE_CONTEXT_CASES)
def test_pure_context(
    state_test: StateTestFiller,
    pre: Alloc,
    code: Bytecode,
    succeeds: bool,
) -> None:
    """
    Run a custom verifier in the pure context: an instruction that reads
    anything but the verifier's input and its own code, a call other
    than a `STATICCALL` to an active precompile, or a state change halts
    the verifier, leaving its claim unsatisfied.
    """
    sender = pre.fund_eoa()
    verifier = pre.deploy_contract(code=code + Op.STOP)
    tx = Transaction(
        sender=sender,
        frames=[Frame.verify()],
        claims=[sender, custom_claim(verifier)],
        error=(
            None if succeeds else TransactionException.TYPE_6_INVALID_SIGNATURE
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1 if succeeds else 0)},
    )


def test_pure_verifier_input(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Call a custom verifier with `resolved_key || resolved_msg || witness`
    as its calldata: the verifier succeeds only on the exact bytes, an
    empty key resolving to the sender left-padded to a word.
    """
    sender = pre.fund_eoa()
    witness = b"\xde\xad\xbe\xef"
    expected_input = bytes(12) + bytes(sender) + bytes(DIGEST) + witness
    verifier = pre.deploy_contract(
        code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Conditional(
            condition=Op.EQ(
                Op.SHA3(0, Op.CALLDATASIZE), keccak256(expected_input)
            ),
            if_true=Op.STOP,
            if_false=Op.REVERT(0, 0),
        )
    )
    tx = Transaction(
        sender=sender,
        frames=[Frame.verify()],
        claims=[sender, custom_claim(verifier, witness, key=Bytes())],
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


@pytest.mark.parametrize(
    "verifier_code,succeeds",
    [
        pytest.param(Op.STOP, True, id="stop"),
        # The claim holds whatever the verifier returns.
        pytest.param(Op.RETURN(0, 32), True, id="returns_zero_word"),
        pytest.param(
            Op.REVERT(0, 0),
            False,
            id="reverts",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            Op.INVALID,
            False,
            id="invalid_opcode",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_custom_verifier_outcome(
    state_test: StateTestFiller,
    pre: Alloc,
    verifier_code: Bytecode,
    succeeds: bool,
) -> None:
    """
    Satisfy a custom verifier's claim if and only if the verifier's call
    succeeds.
    """
    sender = pre.fund_eoa()
    verifier = pre.deploy_contract(code=verifier_code)
    tx = Transaction(
        sender=sender,
        frames=[Frame.verify()],
        claims=[sender, custom_claim(verifier)],
        error=(
            None if succeeds else TransactionException.TYPE_6_INVALID_SIGNATURE
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1 if succeeds else 0)},
    )


IDENTITY_PRECOMPILE = Address(0x04)
"""The identity precompile, which succeeds on any input."""

BLS12_G1ADD_PRECOMPILE = Address(0x0B)
"""BLS12-381 G1 addition, which fails on input of the wrong length."""


@pytest.mark.parametrize(
    "verifier,succeeds",
    [
        pytest.param(
            lambda _pre: IDENTITY_PRECOMPILE, True, id="identity_precompile"
        ),
        pytest.param(
            lambda _pre: BLS12_G1ADD_PRECOMPILE,
            False,
            id="failing_precompile",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            lambda pre: pre.fund_eoa(),
            False,
            id="eoa",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            lambda _pre: Address(0x5A5A5A),
            False,
            id="empty_account",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            lambda pre: pre.fund_eoa(
                delegation=pre.deploy_contract(code=Op.STOP)
            ),
            False,
            id="delegated_account",
            marks=pytest.mark.exception_test,
        ),
        # The code of a verifier that starts with `0xEF` cannot run.
        pytest.param(
            lambda pre: pre.deploy_contract(code=Bytes(b"\xef\x00")),
            False,
            id="ef_prefixed_code",
            marks=pytest.mark.exception_test,
        ),
        # Protocol verifiers are claim-only: a claim naming one is
        # verified natively, so the addresses carry no code to call.
        pytest.param(
            lambda _pre: Spec.SECP256K1_VERIFIER,
            True,
            id="protocol_verifier_reference",
        ),
    ],
)
def test_verifier_account(
    state_test: StateTestFiller,
    pre: Alloc,
    verifier: Callable[[Alloc], Address],
    succeeds: bool,
) -> None:
    """
    Dispatch a claim to an active precompile directly, and refuse a
    custom verifier without code, with a delegation, or whose code
    cannot run. The protocol verifier case checks that a claim naming a
    protocol verifier is verified natively against its witness.
    """
    sender = pre.fund_eoa()
    verifier_address = verifier(pre)
    if verifier_address == Spec.SECP256K1_VERIFIER:
        claim = signed_digest_claim(OTHER_KEY)
    else:
        claim = custom_claim(verifier_address)
    tx = Transaction(
        sender=sender,
        frames=[Frame.verify()],
        claims=[sender, claim],
        error=(
            None if succeeds else TransactionException.TYPE_6_INVALID_SIGNATURE
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1 if succeeds else 0)},
    )


@pytest.mark.parametrize(
    "shortfall",
    [
        pytest.param(0, id="exact_gas"),
        pytest.param(1, id="one_gas_short", marks=pytest.mark.exception_test),
    ],
)
@pytest.mark.parametrize(
    "precompile",
    [
        pytest.param(False, id="contract"),
        pytest.param(True, id="precompile"),
    ],
)
def test_verifier_gas_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    shortfall: int,
    precompile: bool,
) -> None:
    """
    Draw the verifier's access from the claim's gas limit, cold for a
    contract and warm for a precompile, in access sets of the
    verification's own: a gas limit one short of the access plus the
    verifier's work leaves the claim unsatisfied.
    """
    sender = pre.fund_eoa()
    gas_costs = fork.gas_costs()
    if precompile:
        verifier = IDENTITY_PRECOMPILE
        # Identity's cost over the 64-byte `key || msg` input.
        gas = (
            gas_costs.WARM_ACCESS
            + gas_costs.PRECOMPILE_IDENTITY_BASE
            + 2 * gas_costs.PRECOMPILE_IDENTITY_PER_WORD
        )
    else:
        verifier = pre.deploy_contract(code=Op.STOP)
        gas = gas_costs.COLD_ACCOUNT_ACCESS
    tx = Transaction(
        sender=sender,
        frames=[Frame.verify()],
        claims=[sender, custom_claim(verifier, gas_limit=gas - shortfall)],
        error=(
            TransactionException.TYPE_6_INVALID_SIGNATURE
            if shortfall
            else None
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=0 if shortfall else 1)},
    )


def test_verification_warms_nothing_for_frames(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Keep a custom verifier cold for the frames after verifying a claim
    with it: the verification's access sets are discarded. The frame's
    receipt pins a cold access.
    """
    sender = pre.fund_eoa()
    verifier = pre.deploy_contract(code=Op.STOP)
    probe_code = Op.POP(Op.BALANCE(address=verifier, address_warm=False))
    probe = pre.deploy_contract(code=probe_code)
    tx = Transaction(
        sender=sender,
        frames=[
            Frame.verify(),
            Frame.default(target=probe, code=probe_code),
        ],
        claims=[sender, custom_claim(verifier)],
    ).resolve_frames(fork)

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


@pytest.mark.parametrize(
    "same_block",
    [
        pytest.param(False, id="earlier_block"),
        pytest.param(True, id="same_block", marks=pytest.mark.exception_test),
    ],
)
def test_verifier_deployed_before_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    same_block: bool,
) -> None:
    """
    Verify claims against the block's pre-state: a custom verifier
    deployed earlier in the same block has no code yet, so its claim is
    unsatisfied, while one deployed in an earlier block verifies.
    """
    deployer = pre.fund_eoa()
    deploy_tx = Transaction(
        sender=deployer,
        to=None,
        data=Initcode(deploy_code=Op.STOP),
    )
    verifier = compute_create_address(address=deployer, nonce=0)
    sender = pre.fund_eoa()
    claim_tx = Transaction(
        sender=sender,
        frames=[Frame.verify()],
        claims=[sender, custom_claim(verifier)],
        error=(
            TransactionException.TYPE_6_INVALID_SIGNATURE
            if same_block
            else None
        ),
    )
    if same_block:
        blocks = [
            Block(
                txs=[deploy_tx, claim_tx],
                exception=TransactionException.TYPE_6_INVALID_SIGNATURE,
            )
        ]
        post: Dict[Address, Account | None] = {
            sender: Account(nonce=0),
            verifier: Account.NONEXISTENT,
        }
    else:
        blocks = [Block(txs=[deploy_tx]), Block(txs=[claim_tx])]
        post = {sender: Account(nonce=1), verifier: Account(code=Op.STOP)}

    blockchain_test(pre=pre, blocks=blocks, post=post)


# --- Dependency proof --- #


def dependency_proof(txs: Sequence[Transaction]) -> bytes:
    """
    Return the dependency proof of a block of `txs`: `0x00 ||
    rlp(witnesses)` over the block's deduplicated, sorted dependencies,
    or the empty proof when the block has none.
    """
    witnesses: Dict[Tuple[bytes, bytes, bytes, int, int], bytes] = {}
    for tx in txs:
        if tx.claims is None:
            continue
        signed = tx.with_signature_and_sender()
        assert signed.witnesses is not None
        sig_hash = tx.rlp_signing_bytes().keccak256()
        for claim, witness in zip(tx.claims, signed.witnesses, strict=True):
            key = bytes(claim.key)
            if len(key) == 0:
                assert tx.sender is not None
                key = bytes(tx.sender)
            fixed_gas = {
                Spec.SECP256K1_VERIFIER: Spec.SECP256K1_VERIFICATION_GAS,
                Spec.P256_VERIFIER: Spec.P256_VERIFICATION_GAS,
                Spec.LEANSPHINCS_VERIFIER: Spec.LEANSPHINCS_VERIFICATION_GAS,
            }.get(Address(claim.verifier))
            dependency = (
                bytes(claim.verifier),
                key.rjust(32, b"\x00"),
                bytes(claim.msg) if len(claim.msg) else bytes(sig_hash),
                fixed_gas if fixed_gas is not None else int(claim.gas_limit),
                claim.witness_length,
            )
            witnesses.setdefault(dependency, bytes(witness))
    if not witnesses:
        return b""
    return Spec.DEPENDENCY_PROOF_VERSION_RAW + rlp.encode(
        [witnesses[dependency] for dependency in sorted(witnesses)]
    )


def claiming_transactions(
    pre: Alloc, claim_lists: Sequence[Sequence[Callable[[], Claim]]]
) -> List[Transaction]:
    """
    Return one frame transaction per entry of `claim_lists`, each from a
    fresh sender declaring its own claim and the listed ones.
    """
    txs = []
    for claims in claim_lists:
        sender = pre.fund_eoa()
        txs.append(
            Transaction(
                sender=sender,
                frames=[Frame.verify()],
                claims=[sender, *(claim() for claim in claims)],
            )
        )
    return txs


SHARED_CLAIM = lambda: signed_digest_claim(OTHER_KEY)  # noqa: E731
"""An explicit-digest claim two transactions can share."""

THIRD_PARTY_CLAIM = lambda: signed_digest_claim(Hash(0x0C0FFEE))  # noqa: E731
"""Another explicit-digest claim, under a third key."""


@pytest.mark.parametrize(
    "claim_lists",
    [
        pytest.param([], id="no_transactions"),
        pytest.param([[]], id="sender_claim_only"),
        pytest.param([[SHARED_CLAIM]], id="explicit_digest_claim"),
        pytest.param(
            [[SHARED_CLAIM], [SHARED_CLAIM]],
            id="claim_shared_across_transactions",
        ),
        pytest.param(
            [[SHARED_CLAIM, THIRD_PARTY_CLAIM], [THIRD_PARTY_CLAIM]],
            id="claims_declared_out_of_order",
        ),
    ],
)
def test_block_commits_to_dependency_proof(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    claim_lists: Sequence[Sequence[Callable[[], Claim]]],
) -> None:
    """
    Commit the header to the dependency proof of the block's claims: one
    witness per deduplicated dependency, in sorted order, behind the raw
    version byte, or the empty proof when the block declares none. A
    contract sender's transaction and a legacy one declare no claims.
    """
    contract_sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**18)
    legacy_sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    claiming = claiming_transactions(pre, claim_lists)
    txs = [
        Transaction(sender=legacy_sender, to=recipient, value=1),
        Transaction(sender=contract_sender, nonce=1, frames=[Frame.verify()]),
        *claiming,
    ]
    proof = dependency_proof(claiming)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                header_verify=Header(dependency_proof_hash=keccak256(proof)),
            )
        ],
        post={recipient: Account(balance=1)},
    )


def proof_of(*witnesses: bytes) -> bytes:
    """Return a raw dependency proof carrying `witnesses`."""
    return Spec.DEPENDENCY_PROOF_VERSION_RAW + rlp.encode(list(witnesses))


def proof_witnesses(proof: bytes) -> List[bytes]:
    """Return the witnesses a raw dependency proof carries."""
    assert proof[:1] == Spec.DEPENDENCY_PROOF_VERSION_RAW
    decoded = rlp.decode(proof[1:])
    assert isinstance(decoded, list)
    return [bytes(witness) for witness in decoded]


@pytest.mark.exception_test
@pytest.mark.parametrize(
    "claim_lists,replacement",
    [
        pytest.param(
            [[SHARED_CLAIM]],
            lambda _proof: b"",
            id="empty_proof_with_claims",
        ),
        pytest.param(
            [],
            lambda _proof: proof_of(),
            id="proof_without_claims",
        ),
        pytest.param(
            [[SHARED_CLAIM]],
            lambda proof: b"\x01" + proof[1:],
            id="unknown_version",
        ),
        pytest.param(
            [[SHARED_CLAIM]],
            lambda proof: proof + b"\x00",
            id="trailing_byte",
        ),
        pytest.param(
            [[SHARED_CLAIM]],
            lambda _proof: Spec.DEPENDENCY_PROOF_VERSION_RAW + b"\xff",
            id="malformed_rlp",
        ),
        pytest.param(
            [[SHARED_CLAIM]],
            lambda proof: proof_of(*proof_witnesses(proof)[:-1]),
            id="witness_missing",
        ),
        pytest.param(
            [[SHARED_CLAIM]],
            lambda proof: proof_of(*proof_witnesses(proof), b"\x00" * 65),
            id="extra_witness",
        ),
        pytest.param(
            [[SHARED_CLAIM], [SHARED_CLAIM]],
            lambda proof: proof_of(
                *proof_witnesses(proof), proof_witnesses(proof)[0]
            ),
            id="shared_claim_witnessed_twice",
        ),
        pytest.param(
            [[SHARED_CLAIM]],
            lambda proof: proof_of(*reversed(proof_witnesses(proof))),
            id="witnesses_out_of_order",
        ),
        pytest.param(
            [[SHARED_CLAIM]],
            lambda proof: proof_of(
                *(
                    witness[:-1] + bytes([witness[-1] ^ 1])
                    for witness in proof_witnesses(proof)
                )
            ),
            id="witnesses_tampered",
        ),
    ],
)
def test_invalid_dependency_proof(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    claim_lists: Sequence[Sequence[Callable[[], Claim]]],
    replacement: Callable[[bytes], bytes],
) -> None:
    """
    Reject a block whose dependency proof the header commits to but
    which does not satisfy the block's dependencies: a proof that is
    empty, malformed, of an unknown version, or that carries a witness
    too few, a witness too many, witnesses out of order, or a witness
    that does not satisfy its dependency.
    """
    claiming = claiming_transactions(pre, claim_lists)
    contract_sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**18)
    txs = [
        Transaction(sender=contract_sender, nonce=1, frames=[Frame.verify()]),
        *claiming,
    ]
    proof = replacement(dependency_proof(claiming))

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                dependency_proof=Bytes(proof),
                rlp_modifier=Header(dependency_proof_hash=keccak256(proof)),
                exception=BlockException.INVALID_DEPENDENCY_PROOF,
            )
        ],
        post={contract_sender: Account(nonce=1)},
    )


@pytest.mark.exception_test
@pytest.mark.parametrize(
    "commitment",
    [
        pytest.param(lambda _proof: keccak256(b""), id="empty_proof_hash"),
        pytest.param(
            lambda proof: keccak256(proof + b"\x00"), id="other_proof_hash"
        ),
    ],
)
def test_dependency_proof_hash_mismatch(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    commitment: Callable[[bytes], bytes],
) -> None:
    """
    Reject a block whose header does not commit to the dependency proof
    received with it.
    """
    claiming = claiming_transactions(pre, [[SHARED_CLAIM]])
    proof = dependency_proof(claiming)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=claiming,
                rlp_modifier=Header(dependency_proof_hash=commitment(proof)),
                exception=BlockException.INVALID_DEPENDENCY_PROOF_HASH,
            )
        ],
        post={},
    )


@pytest.mark.exception_test
def test_dependency_proof_above_max_size(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a block whose dependency proof exceeds
    `MAX_DEPENDENCY_PROOF_BYTES`, though the header commits to it.
    """
    claiming = claiming_transactions(pre, [[]])
    proof = dependency_proof(claiming)
    oversized = proof + bytes(Spec.MAX_DEPENDENCY_PROOF_BYTES + 1 - len(proof))

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=claiming,
                dependency_proof=Bytes(oversized),
                rlp_modifier=Header(
                    dependency_proof_hash=keccak256(oversized)
                ),
                exception=BlockException.INVALID_DEPENDENCY_PROOF,
            )
        ],
        post={},
    )
