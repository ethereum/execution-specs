"""Stateless input transaction public-key tests."""

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    Prehashed,
    encode_dss_signature,
)
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    Transaction,
)
from execution_testing.test_types.execution_witness.modifiers import (
    replace_public_key_at,
)
from spec256k1 import PublicKey

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def test_stateless_input_public_keys_are_constructed(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """A public key is included for each payload transaction."""
    recipient = pre.fund_eoa()
    sender_a = pre.fund_eoa()
    sender_b = pre.fund_eoa()
    tx_a = Transaction(
        sender=sender_a,
        to=recipient,
        value=0,
        gas_limit=500_000,
    )
    tx_b = Transaction(
        sender=sender_b,
        to=recipient,
        value=0,
        gas_limit=500_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx_a, tx_b],
                # For accepted blocks, the filler verifies stateless input
                # public keys against the recovered payload transaction keys.
                expected_stateless_validation_success=True,
            )
        ],
        post={
            sender_a: Account(nonce=1),
            sender_b: Account(nonce=1),
        },
    )


def test_stateless_input_invalid_public_key_is_rejected(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """A wrong but SSZ-valid public key fails stateless validation."""
    recipient = pre.fund_eoa()
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        gas_limit=500_000,
    )
    invalid_public_key = Bytes(b"\x04" + b"\x00" * 64)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                stateless_input_public_keys_modifier=(
                    replace_public_key_at(0, invalid_public_key)
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )


def test_stateless_input_opposite_y_parity_public_key_is_rejected(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    An ECDSA-valid key from the other recovery candidate is rejected.

    This catches implementations that only verify the supplied key against
    ``(r, s, message_hash)`` without also binding it to the transaction's
    y-parity bit.
    """
    recipient = pre.fund_eoa()
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        gas_limit=21_000,
        max_fee_per_gas=10,
        max_priority_fee_per_gas=0,
    ).with_signature_and_sender()
    invalid_public_key = _opposite_y_parity_public_key(tx)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                stateless_input_public_keys_modifier=(
                    replace_public_key_at(0, invalid_public_key)
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )


def _recover_public_key(
    tx: Transaction,
    y_parity: int,
    signing_hash: bytes,
) -> Bytes:
    """Recover an uncompressed SEC1 public key for ``y_parity``."""
    signature = (
        int(tx.r).to_bytes(32, byteorder="big")
        + int(tx.s).to_bytes(32, byteorder="big")
        + bytes([y_parity])
    )
    public_key = PublicKey.from_signature_and_message(
        signature,
        signing_hash,
    )
    return Bytes(public_key.format(compressed=False))


def _opposite_y_parity_public_key(tx: Transaction) -> Bytes:
    """Recover the other ECDSA-valid public key for a typed transaction."""
    signed_tx = tx.with_signature_and_sender()
    if int(signed_tx.ty) == 0:
        raise AssertionError("expected a typed transaction")

    y_parity = int(signed_tx.v)
    if y_parity not in (0, 1):
        raise AssertionError(f"expected y_parity 0 or 1, got {y_parity}")

    signing_hash = bytes(signed_tx.rlp_signing_bytes().keccak256())
    canonical_public_key = _recover_public_key(
        signed_tx,
        y_parity,
        signing_hash,
    )
    alternate_public_key = _recover_public_key(
        signed_tx,
        y_parity ^ 1,
        signing_hash,
    )
    if alternate_public_key == canonical_public_key:
        raise AssertionError("alternate recovery id produced canonical key")
    if _address_from_public_key(canonical_public_key) != signed_tx.sender:
        raise AssertionError("canonical public key does not derive sender")
    if _address_from_public_key(alternate_public_key) == signed_tx.sender:
        raise AssertionError("alternate public key derives sender")
    if not _signature_verifies(signed_tx, alternate_public_key, signing_hash):
        raise AssertionError("alternate public key does not verify signature")
    return alternate_public_key


def _address_from_public_key(public_key: Bytes) -> Address:
    """Derive the sender address from an uncompressed SEC1 public key."""
    return Address(Bytes(public_key[1:]).keccak256()[12:])


def _signature_verifies(
    tx: Transaction,
    public_key: Bytes,
    signing_hash: bytes,
) -> bool:
    """Return whether ``public_key`` verifies the transaction signature."""
    der_signature = encode_dss_signature(int(tx.r), int(tx.s))
    verifying_key = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP256K1(),
        bytes(public_key),
    )
    try:
        verifying_key.verify(
            der_signature,
            signing_hash,
            ec.ECDSA(Prehashed(hashes.SHA256())),
        )
    except InvalidSignature:
        return False
    return True
