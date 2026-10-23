"""
Test the raw signature bytes the canonical signature hash elides.

An entry with an empty `msg` is signed over the canonical signature hash,
which therefore cannot commit to the entry's own raw bytes. It commits to
their length instead, and the intrinsic cost prices them by that length
alone, so nothing that rewrites them can change what the payer is charged.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Fork,
    FrameSignature,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .helpers import default_frame, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

APPROVE_ALL = Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT)
"""Validation code of a contract sender that approves unconditionally."""


@pytest.mark.parametrize(
    "witness",
    [
        pytest.param(b"", id="empty"),
        pytest.param(b"\x00" * 5, id="zero_bytes"),
        pytest.param(b"\xab" * 5, id="nonzero_bytes"),
        # A length of 256 is the first that RLP-encodes in two bytes.
        pytest.param(b"\xab" * 256, id="two_byte_length"),
    ],
)
def test_sig_hash_commits_to_elided_length(
    state_test: StateTestFiller,
    pre: Alloc,
    witness: bytes,
) -> None:
    """
    Read the canonical signature hash of a transaction carrying an
    empty-`msg` `ARBITRARY` entry, which commits to the entry's length
    and not to its bytes.

    The transaction carries the witness with every byte flipped and
    still reports the hash computed over the original witness.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**18)
    probe = pre.deploy_contract(
        code=Op.SSTORE(0, Op.TXPARAM(Spec.TXPARAM_SIG_HASH)) + Op.STOP
    )

    def carrying(raw: bytes) -> Transaction:
        return Transaction(
            sender=sender,
            nonce=1,
            frames=[verify_frame(), default_frame(target=probe)],
            signatures=[
                FrameSignature(
                    scheme=Spec.SCHEME_ARBITRARY, signature=Bytes(raw)
                )
            ],
        )

    sig_hash = carrying(witness).rlp_signing_bytes().keccak256()
    # The pinned hash commits to the length, so one more byte changes it.
    longer = carrying(witness + b"\x00").rlp_signing_bytes().keccak256()
    assert longer != sig_hash
    tampered_witness = bytes(byte ^ 0xFF for byte in witness)

    state_test(
        pre=pre,
        tx=carrying(tampered_witness),
        post={probe: Account(storage={0: sig_hash})},
    )


@pytest.mark.parametrize(
    "msg",
    [
        pytest.param(b"", id="empty_msg"),
        pytest.param(b"\x5a" * 32, id="explicit_msg"),
    ],
)
@pytest.mark.parametrize(
    "witness",
    [
        pytest.param(b"\x00" * 32, id="zero_bytes"),
        pytest.param(b"\xab" * 32, id="nonzero_bytes"),
    ],
)
def test_elided_signature_priced_by_length(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    msg: bytes,
    witness: bytes,
) -> None:
    """
    Charge an empty-`msg` entry's raw signature bytes by their length
    alone, so zero bytes cost as much as non-zero ones, while an entry
    with an explicit `msg` keeps the cheaper price for zero bytes.
    """
    # Validation burns enough execution gas for the standard cost to
    # exceed the calldata floor, which prices every byte alike.
    verify_code = (
        Op.POP(Op.BALANCE(address=Op.ADDRESS, address_warm=True)) * 60
        + APPROVE_ALL
    )
    sender = pre.deploy_contract(code=verify_code, balance=10**18)
    verify_gas = fork.frame_entry_gas_calculator()(
        target_warm=True
    ) + verify_code.execution_cost(fork)
    frames = [verify_frame(gas_limit=verify_gas, state_gas_limit=0)]

    intrinsic_calculator = fork.frame_transaction_intrinsic_cost_calculator()
    floor_calculator = fork.frame_transaction_data_floor_cost_calculator()

    def signature(raw: bytes) -> FrameSignature:
        return FrameSignature(
            scheme=Spec.SCHEME_ARBITRARY,
            msg=Bytes(msg),
            signature=Bytes(raw),
        )

    def intrinsic_cost(raw: bytes) -> int:
        return intrinsic_calculator(
            frames=frames,
            signatures=[signature(raw)],
            return_cost_deducted_prior_execution=True,
        )

    zero_cost = intrinsic_cost(bytes(len(witness)))
    nonzero_cost = intrinsic_cost(b"\xab" * len(witness))
    assert (zero_cost < nonzero_cost) == (len(msg) > 0)
    assert zero_cost <= nonzero_cost
    gas_used = intrinsic_cost(witness) + verify_gas
    assert gas_used > floor_calculator(
        frames=frames, signatures=[signature(witness)]
    )

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=frames,
        signatures=[signature(witness)],
        expected_receipt=TransactionReceipt(
            payer=sender, cumulative_gas_used=gas_used
        ),
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=2)})
