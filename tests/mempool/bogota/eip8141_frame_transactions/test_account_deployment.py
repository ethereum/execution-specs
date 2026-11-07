"""
Counterfactual account deployment tests for the public mempool rules of
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A funded address with no code sends its first frame transaction as
`[deploy, self_verify, user_op]`: the `deploy` frame has a factory
`CREATE2` the wallet at `tx.sender`, then the wallet approves the owner's
signature. Inside the first `deploy` frame the mempool allows installing
code at `tx.sender` and writing its storage, but no other state write.
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Bytecode,
    Fork,
    Frame,
    MempoolException,
    MempoolTestFiller,
    Op,
    Transaction,
    TransactionException,
)

from tests.bogota.eip8141_frame_transactions.spec import Spec

from .deployment import (
    FACTORY_CODE,
    OWNERS,
    SENDER_BALANCE,
    VERIFY_GAS,
    Owner,
    account_address,
    approving_code,
    deploy_frame,
    deployment_data,
    owner_transaction,
    self_verify_frame,
    signature_gas,
    wallet,
    wallet_initcode,
)
from .spec import RULE_SET, MempoolRule, MempoolSpec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

with_all_schemes = pytest.mark.parametrize("scheme", OWNERS.keys())

OWNER_SLOT = 0x00
"""Slot of the wallet's storage that a constructor writes the owner to."""

DEPLOY_RULES = [MempoolRule.PREFIX_SHAPE, MempoolRule.DEPLOY_INSTALLS_CODE]


def user_op(pre: Alloc) -> Frame:
    """Return a `SENDER` frame calling a fresh contract."""
    return Frame.sender(target=pre.deploy_contract(code=Op.STOP))


def deploying_transaction(
    pre: Alloc,
    owner: Owner,
    *,
    wallet_code: Bytecode | None = None,
    constructor: Bytecode | None = None,
    factory_code: Bytecode = FACTORY_CODE,
    deploy_overrides: dict | None = None,
) -> tuple:
    """
    Return the funded counterfactual sender and its first transaction,
    `[deploy, self_verify, user_op]`, deploying the owner's wallet.
    """
    if wallet_code is None:
        wallet_code = wallet(owner)
    initcode = wallet_initcode(wallet_code, constructor)
    factory = pre.deploy_contract(code=factory_code)
    sender = account_address(factory, initcode)
    pre.fund_address(sender, SENDER_BALANCE)
    tx = owner_transaction(
        sender=sender,
        owner=owner,
        frames=[
            deploy_frame(
                factory,
                deployment_data(initcode),
                **(deploy_overrides or {}),
            ),
            self_verify_frame(),
            user_op(pre),
        ],
    )
    return sender, tx


@with_all_schemes
def test_deploy_and_self_verify(
    mempool_test: MempoolTestFiller, pre: Alloc, scheme: str
) -> None:
    """
    Admit an account's first transaction, which deploys its wallet with
    a factory and has the wallet approve the owner's signature.
    """
    _, tx = deploying_transaction(pre, OWNERS[scheme]())

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=True,
        rules=DEPLOY_RULES + [MempoolRule.STATE_WRITE],
        mempool_rules=RULE_SET,
    )


@with_all_schemes
def test_deploy_with_paymaster(
    mempool_test: MempoolTestFiller, pre: Alloc, scheme: str
) -> None:
    """
    Admit `[deploy, only_verify, pay]` from a sender that does not exist,
    with a default-code payer approving the payment.
    """
    owner = OWNERS[scheme]()
    initcode = wallet_initcode(wallet(owner, Spec.APPROVE_EXECUTION))
    factory = pre.deploy_contract(code=FACTORY_CODE)
    sender = account_address(factory, initcode)
    payer = pre.fund_eoa()

    tx = owner_transaction(
        sender=sender,
        owner=owner,
        frames=[
            deploy_frame(factory, deployment_data(initcode)),
            self_verify_frame(flags=Spec.APPROVE_EXECUTION),
            self_verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer),
            user_op(pre),
        ],
        other_signatures=[payer],
    )

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=True,
        rules=DEPLOY_RULES,
        mempool_rules=RULE_SET,
    )


@with_all_schemes
def test_constructor_writes_sender_storage(
    mempool_test: MempoolTestFiller, pre: Alloc, scheme: str
) -> None:
    """
    Admit a deployment whose constructor stores the owner in the wallet's
    storage, which the wallet then reads to verify the signature.
    """
    owner = OWNERS[scheme]()
    _, tx = deploying_transaction(
        pre,
        owner,
        wallet_code=approving_code(owner.check(Op.SLOAD(OWNER_SLOT))),
        constructor=Op.SSTORE(OWNER_SLOT, owner.credential),
    )

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=True,
        rules=DEPLOY_RULES
        + [MempoolRule.STATE_WRITE, MempoolRule.STORAGE_OUTSIDE_SENDER],
        mempool_rules=RULE_SET,
    )


@with_all_schemes
def test_proxy_wallet(
    mempool_test: MempoolTestFiller, pre: Alloc, scheme: str
) -> None:
    """
    Admit a deployment of a proxy whose implementation, reached with
    `DELEGATECALL`, checks the owner the constructor stored in the
    sender's storage.
    """
    owner = OWNERS[scheme]()
    implementation = pre.deploy_contract(
        code=Op.MSTORE(0, owner.check(Op.SLOAD(OWNER_SLOT))) + Op.RETURN(0, 32)
    )
    proxy = approving_code(
        Op.POP(Op.DELEGATECALL(Op.GAS, implementation, 0, 0, 0, 32))
        + Op.MLOAD(0)
    )
    _, tx = deploying_transaction(
        pre,
        owner,
        wallet_code=proxy,
        constructor=Op.SSTORE(OWNER_SLOT, owner.credential),
    )

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=True,
        rules=DEPLOY_RULES + [MempoolRule.STORAGE_OUTSIDE_SENDER],
        mempool_rules=RULE_SET,
    )


@with_all_schemes
@pytest.mark.parametrize("over", [False, True], ids=["at_cap", "over_cap"])
@pytest.mark.parametrize("dimension", ["execution", "state"])
def test_validation_gas_caps(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    scheme: str,
    dimension: str,
    over: bool,
) -> None:
    """
    Admit a deployment whose prefix budgets reach a public mempool gas
    cap exactly, and refuse it one gas over.

    The execution cap counts the prefix's execution limits plus the cost
    of validating the signatures, so it depends on the scheme.
    """
    owner = OWNERS[scheme]()
    excess = 1 if over else 0
    if dimension == "execution":
        budget = {
            "gas_limit": MempoolSpec.MAX_VERIFY_GAS
            - signature_gas(fork, owner.scheme)
            - VERIFY_GAS
            + excess
        }
        exception = MempoolException.FRAME_VALIDATION_GAS_EXCEEDED
        rule = MempoolRule.VERIFY_GAS
    elif dimension == "state":
        # The `self_verify` frame has no state budget.
        budget = {"state_gas_limit": MempoolSpec.MAX_VERIFY_STATE_GAS + excess}
        exception = MempoolException.FRAME_VALIDATION_STATE_GAS_EXCEEDED
        rule = MempoolRule.VERIFY_STATE_GAS
    else:
        raise ValueError(f"unknown dimension: {dimension}")
    _, tx = deploying_transaction(pre, owner, deploy_overrides=budget)

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=not over,
        exception=exception if over else None,
        rules=[rule],
        mempool_rules=RULE_SET,
    )


@with_all_schemes
def test_wallet_already_deployed(
    mempool_test: MempoolTestFiller, pre: Alloc, scheme: str
) -> None:
    """
    Admit `[self_verify, user_op]` from a wallet that already exists,
    without a `deploy` frame.
    """
    owner = OWNERS[scheme]()
    sender = pre.deploy_contract(code=wallet(owner), balance=SENDER_BALANCE)

    tx = owner_transaction(
        sender=sender,
        owner=owner,
        nonce=1,
        frames=[self_verify_frame(), user_op(pre)],
    )

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=True,
        rules=[MempoolRule.PREFIX_SHAPE],
        mempool_rules=RULE_SET,
    )


@pytest.mark.parametrize(
    "nonce,exception",
    [
        pytest.param(
            1,
            # The colliding `CREATE2` installs no code, and the factory's
            # nonce bump is then a write outside the sender.
            [
                MempoolException.FRAME_DEPLOY_CODE_NOT_INSTALLED,
                MempoolException.FRAME_VALIDATION_STATE_WRITE,
            ],
            id="resigned",
        ),
        pytest.param(
            0, TransactionException.NONCE_MISMATCH_TOO_LOW, id="stale"
        ),
    ],
)
@with_all_schemes
# The wallet sits at the address the factory deploys it at.
@pytest.mark.pre_alloc_mutable
def test_deploy_front_run(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    scheme: str,
    nonce: int,
    exception: List[MempoolException] | TransactionException,
) -> None:
    """
    Refuse a deploying transaction after a third party deployed the
    wallet first.

    Signed again for the nonce the deployment left, the transaction is
    valid, since the wallet still approves, but its `deploy` frame no
    longer installs code. Signed for the old nonce, it is invalid.
    """
    owner = OWNERS[scheme]()
    wallet_code = wallet(owner)
    initcode = wallet_initcode(wallet_code)
    factory = pre.deploy_contract(code=FACTORY_CODE)
    sender = pre.deploy_contract(
        code=wallet_code,
        balance=SENDER_BALANCE,
        address=account_address(factory, initcode),
    )

    tx = owner_transaction(
        sender=sender,
        owner=owner,
        nonce=nonce,
        frames=[
            deploy_frame(factory, deployment_data(initcode)),
            self_verify_frame(),
            user_op(pre),
        ],
    )

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=False,
        exception=exception,
        rules=[MempoolRule.DEPLOY_INSTALLS_CODE],
        mempool_rules=RULE_SET,
    )


@pytest.mark.parametrize(
    "deploy_target,exception,rules",
    [
        pytest.param(
            Op.STOP,
            MempoolException.FRAME_DEPLOY_CODE_NOT_INSTALLED,
            [MempoolRule.DEPLOY_INSTALLS_CODE],
            id="installs_nothing",
        ),
        pytest.param(
            FACTORY_CODE,
            [
                MempoolException.FRAME_DEPLOY_CODE_NOT_INSTALLED,
                MempoolException.FRAME_VALIDATION_STATE_WRITE,
            ],
            [MempoolRule.DEPLOY_INSTALLS_CODE, MempoolRule.STATE_WRITE],
            id="installs_elsewhere",
        ),
        pytest.param(
            Op.REVERT(0, 0),
            [
                MempoolException.FRAME_DEPLOY_CODE_NOT_INSTALLED,
                MempoolException.FRAME_VALIDATION_REVERTED,
            ],
            [MempoolRule.DEPLOY_INSTALLS_CODE, MempoolRule.PREFIX_REVERT],
            id="reverts",
        ),
    ],
)
def test_deploy_frame_without_code_at_sender(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    deploy_target: Bytecode,
    exception: List[MempoolException] | MempoolException,
    rules: List[str],
) -> None:
    """
    Refuse a transaction whose `deploy` frame leaves `tx.sender` without
    code.

    The sender is a secp256k1 address whose default code approves its
    signature, so the transaction stays valid whatever the `deploy` frame
    does.
    """
    sender = pre.fund_eoa(amount=SENDER_BALANCE)
    target = pre.deploy_contract(code=deploy_target)

    tx = Transaction(
        sender=sender,
        frames=[
            deploy_frame(target, deployment_data(wallet_initcode(Op.STOP))),
            self_verify_frame(),
            user_op(pre),
        ],
        signatures=[sender],
    )

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=False,
        exception=exception,
        rules=rules,
        mempool_rules=RULE_SET,
    )


@pytest.mark.parametrize(
    "factory_code,exception,rule",
    [
        pytest.param(
            Op.SSTORE(0, 1) + FACTORY_CODE,
            MempoolException.FRAME_VALIDATION_STATE_WRITE,
            MempoolRule.STATE_WRITE,
            id="writes_own_storage",
        ),
        pytest.param(
            Op.POP(Op.SLOAD(0)) + FACTORY_CODE,
            MempoolException.FRAME_VALIDATION_STORAGE_ACCESS,
            MempoolRule.STORAGE_OUTSIDE_SENDER,
            id="reads_own_storage",
        ),
    ],
)
@with_all_schemes
def test_factory_storage_access(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    scheme: str,
    factory_code: Bytecode,
    exception: MempoolException,
    rule: str,
) -> None:
    """
    Refuse a deployment whose factory writes or reads its own storage,
    such as a registry of deployments or a configurable implementation.
    """
    _, tx = deploying_transaction(
        pre, OWNERS[scheme](), factory_code=factory_code
    )

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=False,
        exception=exception,
        rules=[rule],
        mempool_rules=RULE_SET,
    )


@pytest.mark.parametrize(
    "constructor,exception,rule",
    [
        pytest.param(
            Op.POP(Op.CREATE(0, 0, 0)),
            MempoolException.FRAME_VALIDATION_STATE_WRITE,
            MempoolRule.STATE_WRITE,
            id="creates_contract",
        ),
        pytest.param(
            Op.POP(Op.TIMESTAMP),
            MempoolException.FRAME_VALIDATION_BANNED_OPCODE,
            MempoolRule.BANNED_OPCODE,
            id="TIMESTAMP",
        ),
        pytest.param(
            Op.POP(Op.NUMBER),
            MempoolException.FRAME_VALIDATION_BANNED_OPCODE,
            MempoolRule.BANNED_OPCODE,
            id="NUMBER",
        ),
        pytest.param(
            Op.POP(Op.BALANCE(Op.CALLER)),
            MempoolException.FRAME_VALIDATION_BANNED_OPCODE,
            MempoolRule.BANNED_OPCODE,
            id="BALANCE",
        ),
    ],
)
@with_all_schemes
def test_constructor_violation(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    scheme: str,
    constructor: Bytecode,
    exception: MempoolException,
    rule: str,
) -> None:
    """
    Refuse a deployment whose constructor creates a second contract or
    runs a banned opcode, since the `deploy` frame is part of the
    validation prefix.
    """
    _, tx = deploying_transaction(
        pre, OWNERS[scheme](), constructor=constructor
    )

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=False,
        exception=exception,
        rules=[rule],
        mempool_rules=RULE_SET,
    )


@with_all_schemes
def test_initcode_reverts(
    mempool_test: MempoolTestFiller, pre: Alloc, scheme: str
) -> None:
    """
    Refuse a deployment whose initcode reverts: the `VERIFY` frame then
    runs the default code of a sender with no code, which rejects the
    owner's entry, so the transaction is invalid.
    """
    _, tx = deploying_transaction(
        pre, OWNERS[scheme](), constructor=Op.REVERT(0, 0)
    )

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=False,
        exception=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
        rules=[MempoolRule.DEPLOY_INSTALLS_CODE],
        mempool_rules=RULE_SET,
    )


@pytest.mark.parametrize(
    "shape",
    [
        "two_deploy_frames",
        "deploy_flags",
        "deploy_in_verify_mode",
        "deploy_after_verify",
    ],
)
@with_all_schemes
def test_deploy_frame_shape(
    mempool_test: MempoolTestFiller, pre: Alloc, scheme: str, shape: str
) -> None:
    """
    Refuse a deployment whose `deploy` frame is not a single first
    `DEFAULT` frame with no flags.
    """
    owner = OWNERS[scheme]()
    initcode = wallet_initcode(wallet(owner))
    factory = pre.deploy_contract(code=FACTORY_CODE)
    sender = account_address(factory, initcode)
    pre.fund_address(sender, SENDER_BALANCE)
    deploy = deploy_frame(factory, deployment_data(initcode))
    exception: MempoolException | TransactionException
    if shape == "two_deploy_frames":
        frames = [deploy, deploy.model_copy(), self_verify_frame()]
        exception = MempoolException.FRAME_PREFIX_NOT_RECOGNIZED
    elif shape == "deploy_flags":
        frames = [
            deploy_frame(
                factory,
                deployment_data(initcode),
                flags=Spec.APPROVE_PAYMENT,
            ),
            self_verify_frame(),
        ]
        exception = MempoolException.FRAME_PREFIX_NOT_RECOGNIZED
    elif shape == "deploy_in_verify_mode":
        # A `VERIFY` frame cannot create, and the factory never approves.
        frames = [
            Frame.verify(
                target=factory,
                data=deployment_data(initcode),
                flags=Spec.APPROVE_NONE,
            ),
            self_verify_frame(),
        ]
        exception = TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
    elif shape == "deploy_after_verify":
        # The sender has no code yet, so its default code rejects the
        # owner's entry.
        frames = [self_verify_frame(), deploy]
        exception = TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
    else:
        raise ValueError(f"unknown shape: {shape}")
    tx = owner_transaction(
        sender=sender, owner=owner, frames=frames + [user_op(pre)]
    )

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=False,
        exception=exception,
        rules=[MempoolRule.PREFIX_SHAPE],
        mempool_rules=RULE_SET,
    )


@pytest.mark.parametrize(
    "gas_read", [False, True], ids=["gas_before_call", "gas_popped"]
)
def test_arbitrary_wallet_gas_read(
    mempool_test: MempoolTestFiller, pre: Alloc, gas_read: bool
) -> None:
    """
    Refuse a deployment whose `ARBITRARY` wallet reads `GAS` other than
    to pass it to its `ecrecover` call, and admit the same wallet without
    the read.
    """
    owner = OWNERS["arbitrary"]()
    wallet_code = wallet(owner)
    if gas_read:
        wallet_code = Op.POP(Op.GAS) + wallet_code
    _, tx = deploying_transaction(pre, owner, wallet_code=wallet_code)

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=not gas_read,
        exception=(
            MempoolException.FRAME_VALIDATION_BANNED_OPCODE
            if gas_read
            else None
        ),
        rules=[MempoolRule.BANNED_OPCODE],
        mempool_rules=RULE_SET,
    )
