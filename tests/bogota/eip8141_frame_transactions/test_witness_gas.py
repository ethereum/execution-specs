"""
Test the gas charged for the segregated witnesses of a frame
transaction's claims.

A witness is not part of the transaction, so the canonical signature
hash never covers it. It is priced as calldata whose bytes are all
non-zero, by its resolved length: fixed for a protocol verifier, the
claim's `witness_len` for a custom one. The verification gas of a claim
is fixed for a protocol verifier and is the claim's whole `gas_limit`
for a custom one, however much of it the verifier uses. Nothing a
witness holds can therefore change what the payer is charged.
"""

from typing import Callable, Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Claim,
    Fork,
    Frame,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .claim_helpers import DIGEST, P256_SIGNER, signed_digest_claim
from .helpers import APPROVE_ALL
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

CUSTOM_VERIFIER_GAS = 50_000
"""
Gas limit of the custom verifier claims, far above the cold access and
`STOP` the accepting verifier uses, all of which is charged.
"""

WITNESS_GAS_PER_BYTE = 16
"""
Gas per witness byte: four calldata tokens per byte, as a non-zero
byte, at four gas per token.
"""

FLOOR_GAS_PER_BYTE = 64
"""
Calldata floor gas per charged byte: four tokens per byte at the floor
price of sixteen gas per token.
"""


def custom_claim(verifier: Address, witness: bytes) -> Claim:
    """Return a claim of `verifier` over `DIGEST` with `witness`."""
    return Claim(
        verifier=verifier,
        msg=Bytes(DIGEST),
        gas_limit=CUSTOM_VERIFIER_GAS,
        witness_len=len(witness),
        witness=Bytes(witness),
    )


CLAIM_KINDS: Dict[str, Callable[[Address], Claim]] = {
    "secp256k1": lambda _verifier: signed_digest_claim(Hash(7)),
    "p256": lambda _verifier: Claim(
        verifier=Spec.P256_VERIFIER,
        key=Bytes(P256_SIGNER),
        msg=Bytes(DIGEST),
        witness=P256_SIGNER.sign_message(DIGEST),
    ),
    "custom_empty_witness": lambda verifier: custom_claim(verifier, b""),
    "custom_zero_byte": lambda verifier: custom_claim(verifier, b"\x00"),
    "custom_zero_bytes": lambda verifier: custom_claim(verifier, bytes(32)),
    "custom_nonzero_bytes": lambda verifier: custom_claim(
        verifier, b"\xab" * 32
    ),
    # A length of 256 is the first that RLP-encodes in two bytes.
    "custom_two_byte_length": lambda verifier: custom_claim(
        verifier, b"\xab" * 256
    ),
}
"""Claims of each verifier kind, keyed by the case they price."""


@pytest.mark.parametrize("kind", list(CLAIM_KINDS))
def test_witness_priced_by_resolved_length(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    kind: str,
) -> None:
    """
    Charge a claim's verification gas and its witness by its resolved
    length, whatever the witness bytes: a protocol verifier's fixed gas
    and length, or a custom verifier's whole `gas_limit` and
    `witness_len`, the zero bytes of its witness priced as non-zero.
    """
    # Validation burns enough execution gas for the standard cost to
    # exceed the calldata floor, which prices every byte alike.
    verify_code = (
        Op.POP(Op.BALANCE(address=Op.ADDRESS, address_warm=True)) * 300
        + APPROVE_ALL
    )
    sender = pre.deploy_contract(code=verify_code, balance=10**18)
    verifier = pre.deploy_contract(code=Op.STOP)
    claim = CLAIM_KINDS[kind](verifier)
    verify_gas = fork.frame_entry_gas_calculator()(
        target_warm=True
    ) + verify_code.execution_cost(fork)
    frames = [Frame.verify(gas_limit=verify_gas, state_gas_limit=0)]

    intrinsic_cost = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=frames,
        claims=[claim],
        return_cost_deducted_prior_execution=True,
    )
    calldata_gas = fork.calldata_gas_calculator()
    claim_gas = {
        Spec.SECP256K1_VERIFIER: Spec.SECP256K1_VERIFICATION_GAS,
        Spec.P256_VERIFIER: Spec.P256_VERIFICATION_GAS,
    }.get(Address(claim.verifier), CUSTOM_VERIFIER_GAS)
    gas_costs = fork.gas_costs()
    assert intrinsic_cost == (
        gas_costs.TX_FRAME_INTRINSIC
        + gas_costs.TX_PER_FRAME
        + claim_gas
        + calldata_gas(data=Bytes(claim.verifier))
        + calldata_gas(data=claim.key)
        + calldata_gas(data=claim.msg)
        + WITNESS_GAS_PER_BYTE * claim.witness_length
    )
    gas_used = intrinsic_cost + verify_gas
    assert gas_used > fork.frame_transaction_data_floor_cost_calculator()(
        frames=frames, claims=[claim]
    )

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=frames,
        claims=[claim],
        expected_receipt=TransactionReceipt(
            payer=sender, cumulative_gas_used=gas_used
        ),
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=2)})


def test_witness_counts_toward_calldata_floor(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Count a witness's resolved length toward the calldata floor, which
    a long witness and a cheap validation make bind. The floor carries
    the claim's verification gas too.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**18)
    verifier = pre.deploy_contract(code=Op.STOP)
    claim = custom_claim(verifier, b"\xab" * 2048)
    verify_gas = fork.frame_entry_gas_calculator()(
        target_warm=True
    ) + APPROVE_ALL.execution_cost(fork)
    frames = [Frame.verify(gas_limit=verify_gas, state_gas_limit=0)]

    floor = fork.frame_transaction_data_floor_cost_calculator()(
        frames=frames, claims=[claim]
    )
    gas_costs = fork.gas_costs()
    charged_bytes = (
        len(claim.verifier)
        + len(claim.key)
        + len(claim.msg)
        + claim.witness_length
    )
    assert floor == (
        gas_costs.TX_FRAME_INTRINSIC
        + gas_costs.TX_PER_FRAME
        + CUSTOM_VERIFIER_GAS
        + FLOOR_GAS_PER_BYTE * charged_bytes
    )
    standard = (
        fork.frame_transaction_intrinsic_cost_calculator()(
            frames=frames,
            claims=[claim],
            return_cost_deducted_prior_execution=True,
        )
        + verify_gas
    )
    assert floor > standard

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=frames,
        claims=[claim],
        expected_receipt=TransactionReceipt(
            payer=sender, cumulative_gas_used=floor
        ),
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=2)})


@pytest.mark.parametrize(
    "witness",
    [
        pytest.param(bytes(32), id="zero_bytes"),
        pytest.param(b"\xab" * 32, id="nonzero_bytes"),
    ],
)
def test_sig_hash_ignores_witness(
    state_test: StateTestFiller,
    pre: Alloc,
    witness: bytes,
) -> None:
    """
    Read the canonical signature hash of a transaction carrying a custom
    verifier claim, which covers the claim but not its witness: two
    witnesses of the same length give the same hash.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**18)
    verifier = pre.deploy_contract(code=Op.STOP)
    probe = pre.deploy_contract(
        code=Op.SSTORE(0, Op.TXPARAM(Spec.TXPARAM_SIG_HASH)) + Op.STOP
    )

    def carrying(raw: bytes) -> Transaction:
        return Transaction(
            sender=sender,
            nonce=1,
            frames=[Frame.verify(), Frame.default(target=probe)],
            claims=[custom_claim(verifier, raw)],
        )

    sig_hash = carrying(bytes(len(witness))).rlp_signing_bytes().keccak256()

    state_test(
        pre=pre,
        tx=carrying(witness),
        post={probe: Account(storage={0: sig_hash})},
    )
