"""Helpers for EIP-8141 public mempool tests."""

from enum import Enum, unique
from typing import Any, Dict, List, Sequence, Tuple

from execution_testing import (
    EOA,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    Fork,
    Frame,
    FrameSignature,
    Hash,
    Initcode,
    Op,
    Transaction,
    compute_deterministic_create2_address,
)

from .helpers import verify_frame
from .spec import Spec

DEPLOYED_SENDER_BALANCE = 10**16
"""
Balance of a sender deployed by a deploy frame, which pays for its own
transaction. A counterfactual address cannot be funded on demand, so
the amount is fixed with headroom for live network fees.
"""

PAYMASTER_BALANCE = 10**16
"""Balance of a paymaster contract, fixed for the same reason."""


def validation_prefix(frames: Sequence[Frame]) -> Sequence[Frame]:
    """
    Return the validation prefix: the frames up to and including the
    first `VERIFY` frame allowed to approve payment.
    """
    for index, frame in enumerate(frames):
        if (
            int(frame.mode) == Spec.MODE_VERIFY
            and int(frame.flags) & Spec.APPROVE_PAYMENT
        ):
            return frames[: index + 1]
    return frames


def verify_gas(
    fork: Fork, frames: Sequence[Frame], signatures: Sequence[FrameSignature]
) -> int:
    """
    Return the validation work the public mempool bounds by
    `MAX_VERIFY_GAS`: the execution budgets of the validation prefix
    plus the verification gas of every signature entry.
    """
    return sum(
        int(frame.gas_limit) for frame in validation_prefix(frames)
    ) + fork.frame_signature_verification_gas_calculator()(
        signatures=signatures
    )


def verify_state_gas(frames: Sequence[Frame]) -> int:
    """
    Return the state gas the public mempool bounds by
    `MAX_VERIFY_STATE_GAS`: the state budgets of the validation prefix.
    """
    prefix = validation_prefix(frames)
    return sum(int(frame.state_gas_limit) for frame in prefix)


def default_code_signature(signer: EOA) -> FrameSignature:
    """
    Return the secp256k1 entry by `signer` over the canonical signature
    hash that the default code of `signer` checks.
    """
    return FrameSignature(
        scheme=Spec.SCHEME_SECP256K1,
        signer=Bytes(signer),
        msg=Bytes(b""),
        secret_key=signer.key,
    )


def frame_gas(fork: Fork, code: Bytecode, *, target_warm: bool) -> int:
    """
    Return the execution budget a frame running `code` at its target
    consumes in full: the target's access at entry plus the code.
    """
    return fork.frame_entry_gas_calculator()(
        target_warm=target_warm
    ) + code.gas_cost(fork)


def deploy_frame(
    pre: Alloc, fork: Fork, runtime: Bytecode
) -> Tuple[Frame, Address]:
    """
    Return a `deploy` frame installing `runtime` at a counterfactual
    sender through the deterministic factory, and that sender.

    The salt is a fresh address, so every run deploys a new sender on
    a live network.
    """
    salt = Hash(bytes(pre.nonexistent_account()).rjust(32, b"\x00"))
    initcode = Initcode(deploy_code=runtime)
    sender = compute_deterministic_create2_address(
        salt=salt, initcode=initcode, fork=fork
    )
    frame = Frame(
        mode=Spec.MODE_DEFAULT,
        target=fork.deterministic_factory_contract_address(),
        gas_limit=0,
        data=Bytes(salt) + Bytes(initcode),
    )
    return frame, sender


@unique
class PrefixShape(Enum):
    """A validation prefix the public mempool recognizes."""

    SELF_VERIFY = "self_verify"
    DEPLOY_SELF_VERIFY = "deploy_self_verify"
    ONLY_VERIFY_PAY = "only_verify_pay"
    DEPLOY_ONLY_VERIFY_PAY = "deploy_only_verify_pay"

    def __str__(self) -> str:
        """Return the shape's name as the test id."""
        return self.value

    @property
    def deploys(self) -> bool:
        """Return whether the prefix opens with a `deploy` frame."""
        return self in (
            PrefixShape.DEPLOY_SELF_VERIFY,
            PrefixShape.DEPLOY_ONLY_VERIFY_PAY,
        )


def prefix_frames(
    pre: Alloc, fork: Fork, shape: PrefixShape
) -> Tuple[Address | EOA, List[Frame], List[FrameSignature]]:
    """
    Return a sender, the validation prefix of `shape` with each frame's
    execution budget just covering its work, and the signature entries
    its default code checks.

    A `deploy` frame starts with no execution budget, as its work is
    left to the remainder of the validation budget.
    """
    if shape == PrefixShape.SELF_VERIFY:
        sender = pre.fund_eoa()
        return (
            sender,
            [
                verify_frame(
                    gas_limit=frame_gas(fork, Bytecode(), target_warm=True),
                    state_gas_limit=0,
                )
            ],
            [default_code_signature(sender)],
        )
    if shape == PrefixShape.ONLY_VERIFY_PAY:
        # The sender must exist, or the payment approval would charge
        # its account creation to the `pay` frame's state budget.
        sender = pre.fund_eoa(amount=1)
        sponsor = pre.fund_eoa()
        return (
            sender,
            [
                verify_frame(
                    flags=Spec.APPROVE_EXECUTION,
                    gas_limit=frame_gas(fork, Bytecode(), target_warm=True),
                    state_gas_limit=0,
                ),
                verify_frame(
                    target=sponsor,
                    flags=Spec.APPROVE_PAYMENT,
                    gas_limit=frame_gas(fork, Bytecode(), target_warm=False),
                    state_gas_limit=0,
                ),
            ],
            [default_code_signature(sender), default_code_signature(sponsor)],
        )
    if shape == PrefixShape.DEPLOY_SELF_VERIFY:
        runtime = Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT)
        deploy, deployed = deploy_frame(pre, fork, runtime)
        pre.fund_address(deployed, DEPLOYED_SENDER_BALANCE)
        return (
            deployed,
            [
                deploy,
                verify_frame(
                    gas_limit=frame_gas(fork, runtime, target_warm=True),
                    state_gas_limit=0,
                ),
            ],
            [],
        )
    runtime = Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION)
    deploy, deployed = deploy_frame(pre, fork, runtime)
    paymaster_code = Op.APPROVE(0, 0, Spec.APPROVE_PAYMENT)
    paymaster = pre.deploy_contract(
        code=paymaster_code, balance=PAYMASTER_BALANCE
    )
    return (
        deployed,
        [
            deploy,
            verify_frame(
                flags=Spec.APPROVE_EXECUTION,
                gas_limit=frame_gas(fork, runtime, target_warm=True),
                state_gas_limit=0,
            ),
            verify_frame(
                target=paymaster,
                flags=Spec.APPROVE_PAYMENT,
                gas_limit=frame_gas(fork, paymaster_code, target_warm=False),
                state_gas_limit=0,
            ),
        ],
        [],
    )


def prefix_transaction(
    pre: Alloc,
    fork: Fork,
    shape: PrefixShape,
    *,
    total_verify_gas: int = Spec.MAX_VERIFY_GAS,
    total_verify_state_gas: int | None = None,
    extra_signatures: Sequence[FrameSignature] = (),
    after: Sequence[Frame] = (),
) -> Transaction:
    """
    Return a frame transaction opening with the validation prefix of
    `shape`, followed by the frames in `after`.

    The prefix's first frame absorbs the remainder of
    `total_verify_gas` and the payment-approving frame the remainder of
    `total_verify_state_gas`, so the prefix totals exactly those
    amounts. An unset state total leaves each frame's state budget as
    built.
    """
    sender, frames, signatures = prefix_frames(pre, fork, shape)
    signatures += list(extra_signatures)
    slack = total_verify_gas - verify_gas(fork, frames, signatures)
    assert slack >= 0, "validation budget below the prefix's work"
    frames[0] = frames[0].model_copy(
        update={"gas_limit": int(frames[0].gas_limit) + slack}
    )
    if total_verify_state_gas is not None:
        slack = total_verify_state_gas - verify_state_gas(frames)
        assert slack >= 0, "state budget below the prefix's needs"
        frames[-1] = frames[-1].model_copy(
            update={"state_gas_limit": int(frames[-1].state_gas_limit) + slack}
        )
    kwargs: Dict[str, Any] = {}
    if shape.deploys:
        # A counterfactual sender does not exist before the deploy.
        kwargs["nonce"] = 0
    return Transaction(
        sender=sender,
        frames=frames + list(after),
        signatures=signatures,
        **kwargs,
    )
