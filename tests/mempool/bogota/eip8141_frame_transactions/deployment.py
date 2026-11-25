"""
Counterfactual account deployment helpers for the EIP-8141 mempool tests.

An account's address is the `CREATE2` address of a factory, a salt and
initcode that embeds the owner's credential, so the address commits to the
owner. Its first frame transaction deploys the wallet with a `deploy` frame
calling the factory, then the wallet approves in a `VERIFY` frame.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from execution_testing import (
    EOA,
    Address,
    Bytecode,
    Bytes,
    Fork,
    Frame,
    FrameFlag,
    FrameSignature,
    FrameSignatureScheme,
    Hash,
    Initcode,
    Op,
    P256Signer,
    Transaction,
    TransactionException,
    compute_create2_address,
)

from tests.bogota.eip8141_frame_transactions.spec import Spec

SALT = Hash(0)
"""Salt the factory deploys every wallet with."""

ECRECOVER = Address(0x01)
"""Address of the `ecrecover` precompile."""

SENDER_BALANCE = 10**18
"""Balance of a funded sender, far above any transaction's cost."""

FACTORY_CODE = (
    Op.CALLDATACOPY(0, 32, Op.SUB(Op.CALLDATASIZE, 32))
    + Op.POP(Op.CREATE2(0, 0, Op.SUB(Op.CALLDATASIZE, 32), Op.CALLDATALOAD(0)))
    + Op.STOP
)
"""
Factory that deploys the initcode following a 32-byte salt in its calldata
with `CREATE2`, whoever calls it.
"""

DEPLOY_GAS = 50_000
DEPLOY_STATE_GAS = 400_000
VERIFY_GAS = 30_000
"""
Frame budgets within the public mempool caps, with room for every wallet
and constructor the tests deploy.
"""


@dataclass(frozen=True)
class Owner:
    """An owner's credential under one signature scheme."""

    signer: EOA | P256Signer
    """Key the owner signs the canonical signature hash with."""

    scheme: FrameSignatureScheme
    """Scheme of the owner's signature entry."""

    authorizes: Callable[[Bytecode | int], Bytecode]
    """Code leaving whether entry 0 authorizes a credential."""

    setup: Bytecode = field(default_factory=Bytecode)
    """Code the check reads the results of."""

    @property
    def credential(self) -> int:
        """Return the word the wallet compares the authorized signer with."""
        return int.from_bytes(self.signer, "big")

    def entry(self) -> FrameSignature:
        """Return the owner's entry over the canonical signature hash."""
        return FrameSignature(signer=self.signer, scheme=self.scheme)

    def check(self, credential: Optional[Bytecode | int] = None) -> Bytecode:
        """Return code leaving whether entry 0 authorizes the owner."""
        if credential is None:
            credential = self.credential
        return self.setup + self.authorizes(credential)


def protocol_check(
    scheme: FrameSignatureScheme,
) -> Callable[[Bytecode | int], Bytecode]:
    """
    Return the check that entry 0 is a protocol-validated `scheme` entry
    over the canonical signature hash, resolving to the credential.
    """

    def authorizes(credential: Bytecode | int) -> Bytecode:
        return Op.AND(
            Op.EQ(Op.SIGPARAM(0, Spec.SIGPARAM_SCHEME), scheme),
            Op.AND(
                Op.EQ(
                    Op.SIGPARAM(0, Spec.SIGPARAM_RESOLVED_SIGNER), credential
                ),
                Op.ISZERO(Op.SIGPARAM(0, Spec.SIGPARAM_MSG)),
            ),
        )

    return authorizes


def protocol_owner(signer: EOA | P256Signer) -> Owner:
    """Return the owner of `signer`, validated by the protocol."""
    return Owner(
        signer=signer,
        scheme=signer.signature_scheme,
        authorizes=protocol_check(signer.signature_scheme),
    )


def arbitrary_owner(signer: EOA) -> Owner:
    """
    Return the owner of the secp256k1 `signer` whose wallet verifies an
    `ARBITRARY` entry itself: it recovers the signer of the signature hash
    from the entry's `v || r || s` bytes with `ecrecover`.
    """

    def authorizes(credential: Bytecode | int) -> Bytecode:
        return Op.AND(
            Op.EQ(
                Op.SIGPARAM(0, Spec.SIGPARAM_SIGNATURE_LENGTH),
                signer.signature_length,
            ),
            Op.EQ(Op.MLOAD(0), credential),
        )

    return Owner(
        signer=signer,
        scheme=Spec.SCHEME_ARBITRARY,
        authorizes=authorizes,
        setup=(
            Op.MSTORE(0, Op.TXPARAM(Spec.TXPARAM_SIG_HASH))
            + Op.SIGDATACOPY(63, 0, 1, 0)
            + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 27))
            + Op.SIGDATACOPY(64, 1, 64, 0)
            + Op.POP(Op.STATICCALL(Op.GAS, ECRECOVER, 0, 128, 0, 32))
        ),
    )


OWNERS: Dict[str, Callable[[], Owner]] = {
    "arbitrary": lambda: arbitrary_owner(EOA(key=0x1001)),
    "secp256k1": lambda: protocol_owner(EOA(key=0x2001)),
    "p256": lambda: protocol_owner(P256Signer(0x3001)),
}
"""Owner of each signature scheme."""


def signature_gas(fork: Fork, scheme: FrameSignatureScheme) -> int:
    """
    Return the intrinsic cost of validating one `scheme` entry, which
    counts against `MAX_VERIFY_GAS`.
    """
    gas_costs = fork.gas_costs()
    return {
        Spec.SCHEME_ARBITRARY: gas_costs.FRAME_SIGNATURE_SCHEME_ARBITRARY,
        Spec.SCHEME_SECP256K1: gas_costs.FRAME_SIGNATURE_SCHEME_SECP256K1,
        Spec.SCHEME_P256: gas_costs.FRAME_SIGNATURE_SCHEME_P256,
    }[scheme]


def approving_code(
    check: Bytecode,
    scope: FrameFlag = Spec.APPROVE_EXECUTION_AND_PAYMENT,
) -> Bytecode:
    """
    Return code that approves `scope` when `check` leaves a non-zero word,
    and reverts otherwise.
    """
    approve = Op.APPROVE(0, 0, scope)
    rejected = check + Op.ISZERO
    destination = len(rejected) + len(Op.PUSH2[0]) + 1 + len(approve)
    code = rejected + Op.PUSH2[destination] + Op.JUMPI + approve
    assert len(code) == destination
    return code + Op.JUMPDEST + Op.REVERT(0, 0)


def wallet(
    owner: Owner,
    scope: FrameFlag = Spec.APPROVE_EXECUTION_AND_PAYMENT,
) -> Bytecode:
    """Return wallet code approving `scope` on the owner's signature."""
    return approving_code(owner.check(), scope)


def deployment_data(initcode: Bytecode, salt: Hash = SALT) -> Bytes:
    """Return the factory calldata deploying `initcode`."""
    return Bytes(bytes(salt) + bytes(initcode))


def account_address(factory: Address, initcode: Bytecode) -> Address:
    """Return the address the factory deploys `initcode` at."""
    return compute_create2_address(factory, SALT, initcode)


def wallet_initcode(
    wallet_code: Bytecode, constructor: Optional[Bytecode] = None
) -> Initcode:
    """Return initcode running `constructor` and deploying the wallet."""
    return Initcode(deploy_code=wallet_code, initcode_prefix=constructor)


def deploy_frame(factory: Address, data: Bytes, **overrides: object) -> Frame:
    """Return a `deploy` frame calling `factory` with `data`."""
    overrides.setdefault("gas_limit", DEPLOY_GAS)
    overrides.setdefault("state_gas_limit", DEPLOY_STATE_GAS)
    return Frame.default(target=factory, data=data, **overrides)


def self_verify_frame(**overrides: object) -> Frame:
    """Return a `VERIFY` frame running the sender's code."""
    overrides.setdefault("gas_limit", VERIFY_GAS)
    overrides.setdefault("state_gas_limit", 0)
    return Frame.verify(**overrides)


def owner_transaction(
    *,
    sender: Address,
    owner: Owner,
    frames: List[Frame],
    other_signatures: Optional[List[FrameSignature | EOA]] = None,
    nonce: int = 0,
    error: TransactionException | None = None,
) -> Transaction:
    """Return the transaction from `sender`, the owner's entry first."""
    return Transaction(
        sender=sender,
        nonce=nonce,
        error=error,
        frames=frames,
        signatures=[owner.entry(), *(other_signatures or [])],
    )
