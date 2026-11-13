"""
Test smart accounts that deploy themselves in their first
[EIP-8141](https://eips.ethereum.org/EIPS/eip-8141) frame transaction.

An account's address is the `CREATE2` address of a factory, a salt and
initcode that embeds the owner's credential, so the address commits to
the owner. The address is funded before it has code. Its first frame
transaction deploys the wallet at the sender with a `DEFAULT` frame,
then a `VERIFY` frame runs the wallet just deployed, which approves on a
signature by the owner.

The owner signs with any signature scheme: the protocol validates
`SECP256K1`, `P256` and `LEANSPHINCS` entries, and the wallet checks
the resolved signer, while it verifies an `ARBITRARY` entry itself, with
the `ecrecover` precompile over the signature hash.
"""

from dataclasses import dataclass
from typing import Callable, Dict

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Bytes,
    FrameSignature,
    Hash,
    Initcode,
    LeanSphincsKey,
    Op,
    P256Key,
    StateTestFiller,
    Transaction,
    TransactionException,
    compute_create2_address,
)

from .helpers import default_frame, sender_frame, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_EXECUTED = 0x01
"""Storage slot used by target contracts to record execution."""

SALT = Hash(0)
"""Salt the factory deploys every wallet with."""

ECRECOVER = Address(0x01)
"""Address of the `ecrecover` precompile."""

SECP256K1_SIGNATURE_LENGTH = 65

FACTORY_CODE = (
    Op.CALLDATACOPY(0, 32, Op.SUB(Op.CALLDATASIZE, 32))
    + Op.POP(Op.CREATE2(0, 0, Op.SUB(Op.CALLDATASIZE, 32), Op.CALLDATALOAD(0)))
    + Op.STOP
)
"""
Factory that deploys the initcode following a 32-byte salt in its
calldata with `CREATE2`, whoever calls it.
"""

DEPLOY_EXECUTION_GAS = 500_000
DEPLOY_STATE_GAS = 2_000_000


@dataclass(frozen=True)
class Owner:
    """An owner's credential under one signature scheme."""

    scheme: int
    """Scheme of the owner's signature entry."""

    entry: Callable[[], FrameSignature]
    """Return the owner's entry, over the canonical signature hash."""

    check: Bytecode
    """Code leaving whether entry 0 authorizes the owner on the stack."""

    setup: Bytecode = Bytecode()
    """Code the check reads the results of."""


def protocol_check(scheme: int, resolved_signer: int) -> Bytecode:
    """
    Return code leaving whether entry 0 is a protocol-validated `scheme`
    entry over the canonical signature hash resolving to
    `resolved_signer`.
    """
    return Op.AND(
        Op.EQ(Op.SIGPARAM(0, Spec.SIGPARAM_SCHEME), scheme),
        Op.AND(
            Op.EQ(
                Op.SIGPARAM(0, Spec.SIGPARAM_RESOLVED_SIGNER), resolved_signer
            ),
            Op.ISZERO(Op.SIGPARAM(0, Spec.SIGPARAM_MSG)),
        ),
    )


def secp256k1_owner(key: Hash) -> Owner:
    """Return the owner of the secp256k1 `key`."""
    address = EOA(key=key)
    return Owner(
        scheme=Spec.SCHEME_SECP256K1,
        entry=lambda: FrameSignature(
            scheme=Spec.SCHEME_SECP256K1,
            signer=Bytes(address),
            secret_key=key,
        ),
        check=protocol_check(
            Spec.SCHEME_SECP256K1, int.from_bytes(address, "big")
        ),
    )


def p256_owner(key: P256Key) -> Owner:
    """Return the owner of the P256 `key`."""
    return Owner(
        scheme=Spec.SCHEME_P256,
        entry=lambda: FrameSignature(
            scheme=Spec.SCHEME_P256,
            signer=Bytes(key.address),
            p256_key=key,
        ),
        check=protocol_check(
            Spec.SCHEME_P256, int.from_bytes(key.address, "big")
        ),
    )


def leansphincs_owner(key: LeanSphincsKey) -> Owner:
    """Return the owner of the leanSPHINCS `key`."""
    return Owner(
        scheme=Spec.SCHEME_LEANSPHINCS,
        entry=lambda: FrameSignature(
            scheme=Spec.SCHEME_LEANSPHINCS,
            signer=Bytes(key.public_key),
            leansphincs_key=key,
        ),
        check=protocol_check(
            Spec.SCHEME_LEANSPHINCS, int.from_bytes(key.public_key, "big")
        ),
    )


def arbitrary_owner(key: Hash) -> Owner:
    """
    Return the owner of the secp256k1 `key` whose wallet verifies an
    `ARBITRARY` entry itself: it recovers the signer of the signature
    hash from the entry's `v || r || s` bytes with `ecrecover`.
    """
    address = EOA(key=key)
    return Owner(
        scheme=Spec.SCHEME_ARBITRARY,
        entry=lambda: FrameSignature(
            scheme=Spec.SCHEME_ARBITRARY,
            secret_key=key,
        ),
        setup=(
            Op.MSTORE(0, Op.TXPARAM(Spec.TXPARAM_SIG_HASH))
            + Op.SIGDATACOPY(63, 0, 1, 0)
            + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 27))
            + Op.SIGDATACOPY(64, 1, 64, 0)
            + Op.POP(Op.STATICCALL(Op.GAS, ECRECOVER, 0, 128, 0, 32))
        ),
        check=Op.AND(
            Op.EQ(
                Op.SIGPARAM(0, Spec.SIGPARAM_SIGNATURE_LENGTH),
                SECP256K1_SIGNATURE_LENGTH,
            ),
            Op.EQ(Op.MLOAD(0), int.from_bytes(address, "big")),
        ),
    )


OWNERS: Dict[str, Callable[[int], Owner]] = {
    "arbitrary": lambda seed: arbitrary_owner(Hash(0x1000 + seed)),
    "secp256k1": lambda seed: secp256k1_owner(Hash(0x2000 + seed)),
    "p256": lambda seed: p256_owner(P256Key(0x3000 + seed)),
    "leansphincs": lambda seed: leansphincs_owner(
        LeanSphincsKey(bytes([seed]) * 32)
    ),
}
"""Owner of each scheme, from a seed picking one of its keys."""


def wallet(
    owner: Owner, scope: int = Spec.APPROVE_EXECUTION_AND_PAYMENT
) -> Bytecode:
    """
    Return wallet code that approves `scope` when entry 0 authorizes
    `owner`, and reverts otherwise.
    """
    approve = Op.APPROVE(0, 0, scope)
    rejected = Op.ISZERO(owner.check)
    # The setup, `rejected`, then PUSH1 of the destination and JUMPI.
    destination = len(owner.setup) + len(rejected) + 3 + len(approve)
    assert destination < 0x100
    code = owner.setup + Op.JUMPI(destination, rejected) + approve
    assert len(code) == destination
    return code + Op.JUMPDEST + Op.REVERT(0, 0)


def deployment_data(wallet_code: Bytecode) -> Bytes:
    """Return the factory calldata deploying `wallet_code`."""
    return Bytes(bytes(SALT) + bytes(Initcode(deploy_code=wallet_code)))


def account_address(factory: Address, wallet_code: Bytecode) -> Address:
    """Return the address the factory deploys `wallet_code` at."""
    return compute_create2_address(
        factory, SALT, Initcode(deploy_code=wallet_code)
    )


def deploying_transaction(
    sender: Address,
    factory: Address,
    wallet_code: Bytecode,
    entry: FrameSignature,
    target: Address,
    **kwargs: object,
) -> Transaction:
    """
    Return the frame transaction from `sender` that deploys
    `wallet_code` at it, has the wallet verify `entry` and calls
    `target`.
    """
    return Transaction(
        sender=sender,
        frames=[
            default_frame(
                target=factory,
                data=deployment_data(wallet_code),
                gas_limit=DEPLOY_EXECUTION_GAS,
                state_gas_limit=DEPLOY_STATE_GAS,
            ),
            verify_frame(),
            sender_frame(target=target),
        ],
        signatures=[entry],
        **kwargs,
    )


@pytest.mark.parametrize("scheme", OWNERS.keys())
def test_account_deploys_itself(
    state_test: StateTestFiller,
    pre: Alloc,
    scheme: str,
) -> None:
    """
    Deploy a wallet at a funded address with no code in the address's
    first frame transaction, and have the wallet approve the transaction
    on its owner's signature.
    """
    owner = OWNERS[scheme](1)
    wallet_code = wallet(owner)
    factory = pre.deploy_contract(code=FACTORY_CODE)
    sender = account_address(factory, wallet_code)
    pre.fund_address(sender, 10**18)
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)

    tx = deploying_transaction(
        sender, factory, wallet_code, owner.entry(), target
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(code=wallet_code, nonce=2),
            target: Account(storage={SLOT_EXECUTED: 1}),
        },
    )


@pytest.mark.parametrize("scheme", OWNERS.keys())
def test_sponsored_account_deploys_itself(
    state_test: StateTestFiller,
    pre: Alloc,
    scheme: str,
) -> None:
    """
    Deploy a wallet at an address with no account, in a transaction a
    payer sponsors.

    The deployment creates the sender account, so it exists when the
    payer approves payment, and incrementing its nonce creates no
    account: the payer's `VERIFY` frame needs no state gas.
    """
    owner = OWNERS[scheme](1)
    wallet_code = wallet(owner, Spec.APPROVE_EXECUTION)
    factory = pre.deploy_contract(code=FACTORY_CODE)
    sender = account_address(factory, wallet_code)
    payer = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)

    tx = Transaction(
        sender=sender,
        frames=[
            default_frame(
                target=factory,
                data=deployment_data(wallet_code),
                gas_limit=DEPLOY_EXECUTION_GAS,
                state_gas_limit=DEPLOY_STATE_GAS,
            ),
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            verify_frame(
                flags=Spec.APPROVE_PAYMENT,
                target=payer,
                state_gas_limit=0,
            ),
            sender_frame(target=target),
        ],
        signatures=[
            owner.entry(),
            FrameSignature(
                scheme=Spec.SCHEME_SECP256K1,
                signer=Bytes(payer),
                secret_key=payer.key,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(code=wallet_code, nonce=2, balance=0),
            target: Account(storage={SLOT_EXECUTED: 1}),
        },
    )


@pytest.mark.exception_test
@pytest.mark.parametrize("scheme", OWNERS.keys())
def test_account_deployment_rejects_other_key(
    state_test: StateTestFiller,
    pre: Alloc,
    scheme: str,
) -> None:
    """
    Reject the first frame transaction of an address whose deployed
    wallet's owner did not sign it: a valid signature by another key of
    the same scheme does not authorize the wallet.
    """
    owner = OWNERS[scheme](1)
    other = OWNERS[scheme](2)
    wallet_code = wallet(owner)
    factory = pre.deploy_contract(code=FACTORY_CODE)
    sender = account_address(factory, wallet_code)
    pre.fund_address(sender, 10**18)
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)

    tx = deploying_transaction(
        sender,
        factory,
        wallet_code,
        other.entry(),
        target,
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(code=b"", nonce=0, balance=10**18),
            target: Account(storage={SLOT_EXECUTED: 0}),
        },
    )


@pytest.mark.parametrize(
    "resigned",
    [
        pytest.param(True, id="resigned"),
        pytest.param(False, id="stale", marks=pytest.mark.exception_test),
    ],
)
@pytest.mark.parametrize("scheme", OWNERS.keys())
def test_account_deployment_front_run(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    scheme: str,
    resigned: bool,
) -> None:
    """
    Front-run an address's first frame transaction by deploying its
    wallet from another account in an earlier block.

    The attacker can only deploy the code the address commits to, which
    authorizes the owner alone. Deploying it sets the account's nonce to
    1, which invalidates the owner's transaction signed for nonce 0.
    Signed again for nonce 1, it is valid: its deployment fails because
    the wallet exists, and the wallet then approves the owner's
    signature.
    """
    owner = OWNERS[scheme](1)
    wallet_code = wallet(owner)
    factory = pre.deploy_contract(code=FACTORY_CODE)
    sender = account_address(factory, wallet_code)
    pre.fund_address(sender, 10**18)
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    attacker = pre.fund_eoa()

    front_run = Transaction(
        sender=attacker,
        to=factory,
        data=deployment_data(wallet_code),
        gas_limit=DEPLOY_EXECUTION_GAS + DEPLOY_STATE_GAS,
    )
    error = None if resigned else TransactionException.NONCE_MISMATCH_TOO_LOW
    tx = deploying_transaction(
        sender,
        factory,
        wallet_code,
        owner.entry(),
        target,
        nonce=1 if resigned else 0,
        error=error,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[front_run]),
            Block(txs=[tx], exception=error),
        ],
        post={
            sender: Account(code=wallet_code, nonce=2 if resigned else 1),
            target: Account(storage={SLOT_EXECUTED: 1 if resigned else 0}),
        },
    )
