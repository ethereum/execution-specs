"""Helpers for EIP-8141 public mempool tests."""

from dataclasses import dataclass
from enum import Enum, unique
from typing import Any, List, Sequence, Tuple

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
    compute_create2_address,
)

from .helpers import expiry_frame, verify_frame
from .spec import Spec

CONTRACT_ACCOUNT_BALANCE = 10**16
"""
Balance of a contract sender or paymaster that pays for a transaction.
Execute funds a contract or a counterfactual address with a fixed
amount only, so it carries headroom for live network fees.
"""

EXPIRY_VERIFIER_PATH = (
    Op.PUSH1(Spec.EXPIRY_DATA_LENGTH)
    + Op.CALLDATASIZE
    + Op.EQ
    + Op.PUSH1(0x0A)
    + Op.JUMPI
    + Op.JUMPDEST
    + Op.PUSH0
    + Op.CALLDATALOAD
    + Op.PUSH1(0xC0)
    + Op.SHR
    + Op.TIMESTAMP
    + Op.GT
    + Op.PUSH1(0x16)
    + Op.JUMPI
    + Op.STOP
)
"""
The instructions the expiry verifier executes for a deadline that has
not passed, which price an expiry verifier frame.
"""


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


PINNED_MAX_FEE_PER_GAS = 10**10
"""Maximum fee per gas of transactions whose fees a test pins."""

PINNED_MAX_PRIORITY_FEE_PER_GAS = 10**9
"""Maximum priority fee per gas of transactions whose fees a test pins."""


def frame_max_cost_bounds(fork: Fork, tx: Transaction) -> Tuple[int, int]:
    """
    Return the least and greatest maximum cost a frame transaction
    shaped like `tx` can have, over every value of its signature
    entries' signer and signature bytes, which zero bytes price lower.
    """
    tx.sign()
    assert tx.frames is not None and tx.signatures is not None

    def cost(fill: bytes) -> int:
        assert tx.signatures is not None
        stand_ins = [
            signature.model_copy(
                update={
                    "signer": Bytes(fill * len(signature.signer)),
                    "signature": Bytes(fill * len(signature.signature)),
                }
            )
            for signature in tx.signatures
        ]
        return frame_max_cost(fork, tx, signatures=stand_ins)

    return cost(b"\x00"), cost(b"\xff")


def frame_max_cost(
    fork: Fork,
    tx: Transaction,
    signatures: Sequence[FrameSignature] | None = None,
) -> int:
    """
    Return the maximum cost a frame transaction's payer is charged when
    payment is approved: its derived gas limit at the maximum fee per
    gas.
    """
    tx.sign()
    assert tx.frames is not None and tx.signatures is not None
    max_gas = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=tx.frames,
        signatures=tx.signatures if signatures is None else signatures,
        sender=tx.sender,
        nonce_keys=[int(key) for key in tx.nonce_keys or (0,)],
        nonce_seq=int(tx.nonce),
    )
    return max_gas * int(tx.max_fee_per_gas or 0)


def deploy_frame(
    pre: Alloc,
    fork: Fork,
    runtime: Bytecode,
    *,
    factory: Address | None = None,
    initcode_prefix: Bytecode | None = None,
) -> Tuple[Frame, Address]:
    """
    Return a `deploy` frame installing `runtime` at a counterfactual
    sender, and that sender.

    The frame calls the deterministic factory, or a `factory` sharing
    its calldata layout. The salt is a fresh address, so every run
    deploys a new sender on a live network.
    """
    if factory is None:
        factory = fork.deterministic_factory_contract_address()
    assert factory is not None
    salt = Hash(bytes(pre.nonexistent_account()).rjust(32, b"\x00"))
    initcode = Initcode(deploy_code=runtime, initcode_prefix=initcode_prefix)
    sender = compute_create2_address(
        address=factory, salt=salt, initcode=initcode
    )
    frame = Frame(
        mode=Spec.MODE_DEFAULT,
        target=factory,
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

    @property
    def sponsored(self) -> bool:
        """Return whether a `pay` frame approves the payment."""
        return self in (
            PrefixShape.ONLY_VERIFY_PAY,
            PrefixShape.DEPLOY_ONLY_VERIFY_PAY,
        )


@dataclass
class Prefix:
    """A validation prefix and the accounts it validates."""

    sender: Address
    frames: List[Frame]
    signatures: List[FrameSignature]
    work_frame: int
    """Frame absorbing the rest of the validation budget."""
    nonce: int | None = None
    """Nonce of a sender that is not a funded EOA."""

    def insert(self, index: int, frame: Frame) -> None:
        """Insert `frame` at `index`, keeping the work frame in place."""
        self.frames.insert(index, frame)
        if index <= self.work_frame:
            self.work_frame += 1


def sender_part(
    pre: Alloc,
    fork: Fork,
    shape: PrefixShape,
    sender_code: Bytecode | None,
    factory: Address | None = None,
    initcode_prefix: Bytecode | None = None,
    sender: EOA | None = None,
) -> Prefix:
    """
    Return the frames approving the sender's execution, and payment for
    a shape without a `pay` frame.

    A sender without `sender_code` is an EOA validated by its default
    code; otherwise it is a contract running `sender_code` before
    approving. A `deploy` frame starts with no execution budget, as its
    work is left to the rest of the validation budget.
    """
    scope = (
        Spec.APPROVE_EXECUTION
        if shape.sponsored
        else Spec.APPROVE_EXECUTION_AND_PAYMENT
    )
    if shape.deploys:
        runtime = (sender_code or Bytecode()) + Op.APPROVE(0, 0, scope)
        deploy, deployed = deploy_frame(
            pre,
            fork,
            runtime,
            factory=factory,
            initcode_prefix=initcode_prefix,
        )
        if not shape.sponsored:
            pre.fund_address(deployed, CONTRACT_ACCOUNT_BALANCE)
        verify = verify_frame(
            flags=scope,
            gas_limit=frame_gas(fork, runtime, target_warm=True),
            state_gas_limit=0,
        )
        return Prefix(deployed, [deploy, verify], [], work_frame=0, nonce=0)
    if sender_code is not None:
        code = sender_code + Op.APPROVE(0, 0, scope)
        contract = pre.deploy_contract(
            code=code,
            balance=0 if shape.sponsored else CONTRACT_ACCOUNT_BALANCE,
        )
        verify = verify_frame(
            flags=scope,
            gas_limit=frame_gas(fork, code, target_warm=True),
            state_gas_limit=0,
        )
        # A deployed contract starts at nonce one.
        return Prefix(contract, [verify], [], work_frame=0, nonce=1)
    if sender is not None:
        eoa = sender
    elif shape.sponsored:
        # A sponsored sender must exist, or the payment approval would
        # charge its account creation to the `pay` frame's state budget.
        eoa = pre.fund_eoa(amount=1)
    else:
        eoa = pre.fund_eoa()
    verify = verify_frame(
        flags=scope,
        gas_limit=frame_gas(fork, Bytecode(), target_warm=True),
        state_gas_limit=0,
    )
    return Prefix(eoa, [verify], [default_code_signature(eoa)], work_frame=0)


@dataclass(frozen=True)
class Paymaster:
    """A non-canonical paymaster contract and the code it runs."""

    address: Address
    code: Bytecode


def deploy_paymaster(
    pre: Alloc,
    code: Bytecode | None = None,
    balance: int = CONTRACT_ACCOUNT_BALANCE,
) -> Paymaster:
    """Deploy a paymaster running `code` before approving payment."""
    approving = (code or Bytecode()) + Op.APPROVE(0, 0, Spec.APPROVE_PAYMENT)
    return Paymaster(
        pre.deploy_contract(code=approving, balance=balance), approving
    )


def prefix(
    pre: Alloc,
    fork: Fork,
    shape: PrefixShape,
    *,
    sender_code: Bytecode | None = None,
    paymaster_code: Bytecode | None = None,
    payer: EOA | Paymaster | None = None,
    sender: EOA | None = None,
    expiry: bool = False,
    factory: Address | None = None,
    initcode_prefix: Bytecode | None = None,
) -> Prefix:
    """
    Return the validation prefix of `shape` with each frame's execution
    budget just covering its work.

    A sponsored shape pays from `payer`, an EOA sponsor validated by its
    default code or a paymaster contract. Unset, the payer is a new
    sponsor, or a new paymaster running `paymaster_code` when that is
    given or the sender has no signature entry to precede the
    sponsor's. An EOA `sender` validated by its default code is reused
    instead of a new one. With `expiry`, the prefix opens with an expiry
    verifier frame. A `deploy` frame calls `factory`, the deterministic factory
    by default, with `initcode_prefix` run before the sender's code is
    returned.
    """
    built = sender_part(
        pre, fork, shape, sender_code, factory, initcode_prefix, sender
    )
    if shape.sponsored:
        if payer is None:
            if paymaster_code is None and built.signatures:
                payer = pre.fund_eoa()
            else:
                payer = deploy_paymaster(pre, paymaster_code)
                if paymaster_code is not None and not shape.deploys:
                    built.work_frame = len(built.frames)
        if isinstance(payer, Paymaster):
            built.frames.append(
                verify_frame(
                    target=payer.address,
                    flags=Spec.APPROVE_PAYMENT,
                    gas_limit=frame_gas(fork, payer.code, target_warm=False),
                    state_gas_limit=0,
                )
            )
        else:
            assert built.signatures, "a sponsor's entry must not be first"
            built.frames.append(
                verify_frame(
                    target=payer,
                    flags=Spec.APPROVE_PAYMENT,
                    gas_limit=frame_gas(fork, Bytecode(), target_warm=False),
                    state_gas_limit=0,
                )
            )
            built.signatures.append(default_code_signature(payer))
    if expiry:
        built.insert(0, priced_expiry_frame(fork))
    return built


def priced_expiry_frame(fork: Fork) -> Frame:
    """Return an expiry verifier frame budgeted to its execution."""
    return expiry_frame(
        gas_limit=frame_gas(fork, EXPIRY_VERIFIER_PATH, target_warm=False)
    )


def budgeted_transaction(
    fork: Fork,
    built: Prefix,
    *,
    total_verify_gas: int = Spec.MAX_VERIFY_GAS,
    total_verify_state_gas: int | None = None,
    after: Sequence[Frame] = (),
    **tx_kwargs: Any,
) -> Transaction:
    """
    Return a frame transaction opening with the validation prefix
    `built`, followed by the frames in `after`.

    The work frame absorbs the rest of `total_verify_gas` and the
    payment-approving frame the rest of `total_verify_state_gas`, so
    the prefix totals exactly those amounts. An unset state total
    leaves each frame's state budget as built.
    """
    frames, signatures = list(built.frames), built.signatures
    slack = total_verify_gas - verify_gas(fork, frames, signatures)
    assert slack >= 0, "validation budget below the prefix's work"
    work = frames[built.work_frame]
    frames[built.work_frame] = work.model_copy(
        update={"gas_limit": int(work.gas_limit) + slack}
    )
    if total_verify_state_gas is not None:
        slack = total_verify_state_gas - verify_state_gas(frames)
        assert slack >= 0, "state budget below the prefix's needs"
        payer_index = len(validation_prefix(frames)) - 1
        payer = frames[payer_index]
        frames[payer_index] = payer.model_copy(
            update={"state_gas_limit": int(payer.state_gas_limit) + slack}
        )
    if built.nonce is not None:
        tx_kwargs.setdefault("nonce", built.nonce)
    return Transaction(
        sender=built.sender,
        frames=frames + list(after),
        signatures=signatures,
        **tx_kwargs,
    )


def prefix_transaction(
    pre: Alloc,
    fork: Fork,
    shape: PrefixShape,
    *,
    total_verify_gas: int = Spec.MAX_VERIFY_GAS,
    total_verify_state_gas: int | None = None,
    extra_signatures: Sequence[FrameSignature] = (),
    sender_code: Bytecode | None = None,
    paymaster_code: Bytecode | None = None,
    payer: EOA | Paymaster | None = None,
    sender: EOA | None = None,
    expiry: bool = False,
    after: Sequence[Frame] = (),
    **tx_kwargs: Any,
) -> Transaction:
    """
    Return a frame transaction opening with the validation prefix of
    `shape` budgeted to the given totals, followed by the frames in
    `after`.
    """
    built = prefix(
        pre,
        fork,
        shape,
        sender_code=sender_code,
        paymaster_code=paymaster_code,
        payer=payer,
        sender=sender,
        expiry=expiry,
    )
    built.signatures += list(extra_signatures)
    return budgeted_transaction(
        fork,
        built,
        total_verify_gas=total_verify_gas,
        total_verify_state_gas=total_verify_state_gas,
        after=after,
        **tx_kwargs,
    )
