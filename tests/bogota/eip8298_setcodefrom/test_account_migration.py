"""Test EOA migration to adopted code via `SETCODEFROM`."""

from typing import Any

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    BalAccountExpectation,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    Bytes,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from spec256k1 import PrivateKey

from ...frontier.precompiles.spec import EcrecoverInput
from ...frontier.precompiles.spec import Spec as PrecompileSpec
from .helpers import (
    ADOPT_FROM_CALLDATA,
    MARKER_A,
    MARKER_SLOT,
    RESULT_SLOT,
    SENTINEL,
    SSTORE_MARKER_A,
    call_with,
    word,
)
from .spec import ref_spec_8298

REFERENCE_SPEC_GIT_PATH = ref_spec_8298.git_path
REFERENCE_SPEC_VERSION = ref_spec_8298.version

pytestmark = pytest.mark.valid_from("EIP8298")

with_self_sponsored = pytest.mark.parametrize(
    "self_sponsored",
    [
        pytest.param(True, id="self_sponsored"),
        pytest.param(False, id="relayed"),
    ],
)


def migrate(
    eoa: EOA,
    eoa_nonce: int,
    relayer: EOA,
    shell: Address,
    source: Address,
    self_sponsored: bool,
) -> tuple[Transaction, int]:
    """
    Build the type-4 tx that delegates `eoa` to `shell` and adopts `source`;
    return it with the EOA nonce after it.
    """
    sender_kwargs: dict[str, Any]
    if self_sponsored:
        sender_kwargs = {"sender": eoa, "nonce": eoa_nonce}
        auth_nonce = eoa_nonce + 1
    else:
        sender_kwargs = {"sender": relayer}
        auth_nonce = eoa_nonce
    tx = Transaction(
        to=eoa,
        data=word(source),
        authorization_list=[
            AuthorizationTuple(address=shell, nonce=auth_nonce, signer=eoa)
        ],
        **sender_kwargs,
    )
    return tx, auth_nonce + 1


@with_self_sponsored
def test_eoa_sends_before_migration(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    self_sponsored: bool,
) -> None:
    """Verify an EOA can send a tx placed before its migration in a block."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    eoa = pre.fund_eoa()
    relayer = pre.fund_eoa()
    send = Transaction(sender=eoa, to=relayer, value=1)
    migration, nonce = migrate(
        eoa, 1, relayer, shell, template, self_sponsored
    )
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[send, migration])],
        post={
            eoa: Account(
                code=SSTORE_MARKER_A, nonce=nonce, storage={RESULT_SLOT: 1}
            )
        },
    )


@pytest.mark.inclusion_test
@pytest.mark.exception_test
@with_self_sponsored
@pytest.mark.parametrize("send", ["same_block", "next_block"])
def test_migrated_eoa_cannot_send(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    self_sponsored: bool,
    send: str,
) -> None:
    """Verify an EOA that adopted code is rejected as a tx sender."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    eoa = pre.fund_eoa()
    relayer = pre.fund_eoa()
    migration, nonce = migrate(
        eoa, 0, relayer, shell, template, self_sponsored
    )
    tx = Transaction(
        sender=eoa,
        nonce=nonce,
        to=relayer,
        value=1,
        error=TransactionException.SENDER_NOT_EOA,
    )
    if send == "same_block":
        blocks = [
            Block(
                txs=[migration, tx],
                exception=TransactionException.SENDER_NOT_EOA,
            )
        ]
        # The rejected block also drops the migration.
        post = {eoa: Account(code=b"", nonce=0)}
    elif send == "next_block":
        blocks = [
            Block(txs=[migration]),
            Block(txs=[tx], exception=TransactionException.SENDER_NOT_EOA),
        ]
        post = {
            eoa: Account(
                code=SSTORE_MARKER_A, nonce=nonce, storage={RESULT_SLOT: 1}
            )
        }
    else:
        raise ValueError(f"unknown send: {send}")
    blockchain_test(pre=pre, blocks=blocks, post=post)


def test_migrated_eoa_redelegation_skipped(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """Verify a later authorization from a migrated EOA is skipped."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    eoa = pre.fund_eoa()
    relayer = pre.fund_eoa()
    other_impl = pre.deploy_contract(Op.STOP)
    recipient = pre.fund_eoa(amount=0)
    migration, nonce = migrate(eoa, 0, relayer, shell, template, False)
    redelegation = Transaction(
        sender=relayer,
        to=recipient,
        value=10,
        authorization_list=[
            AuthorizationTuple(address=other_impl, nonce=nonce, signer=eoa)
        ],
    )
    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[migration]),
            Block(
                txs=[redelegation],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        # Loaded for the authority check, then rejected
                        # because it has non-designator code.
                        eoa: BalAccountExpectation.empty(),
                        other_impl: None,
                    }
                ),
            ),
        ],
        post={
            eoa: Account(
                code=SSTORE_MARKER_A, nonce=nonce, storage={RESULT_SLOT: 1}
            ),
            recipient: Account(balance=10),
        },
    )


def test_migrated_eoa_runs_adopted_code(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """Verify a call to a migrated EOA runs its adopted code."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    eoa = pre.fund_eoa(amount=1)
    relayer = pre.fund_eoa()
    migration, nonce = migrate(eoa, 0, relayer, shell, template, False)
    call = Transaction(sender=relayer, to=eoa, value=1)
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[migration]), Block(txs=[call])],
        post={
            eoa: Account(
                code=SSTORE_MARKER_A,
                nonce=nonce,
                balance=2,
                storage={RESULT_SLOT: 1, MARKER_SLOT: MARKER_A},
            )
        },
    )


def test_migrated_eoa_withheld_from_ecrecover(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify `ecrecover` recovers an EOA's signature before and after it
    adopts code, unless EIP-8151 is enabled: a signer holding code other
    than a delegation designation is then withheld, so adopting code
    retires the EOA's key.
    """
    template = pre.deploy_contract(SSTORE_MARKER_A)
    shell = pre.deploy_contract(
        ADOPT_FROM_CALLDATA, storage={RESULT_SLOT: SENTINEL}
    )
    eoa = pre.fund_eoa(delegation=shell)
    assert eoa.key is not None
    digest = Bytes(b"migrated eoa ecrecover").keccak256()
    signature = PrivateKey(eoa.key).sign_recoverable(digest)
    recover_input = EcrecoverInput(
        msg_hash=int.from_bytes(digest),
        v=signature[64] + 27,
        r=int.from_bytes(signature[0:32]),
        s=int.from_bytes(signature[32:64]),
    )

    def recover_into(slot: int) -> Bytecode:
        """
        Recover the signature in the calldata, leaving `SENTINEL` in
        `slot` when the output is empty.
        """
        return (
            Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            + Op.MSTORE(128, SENTINEL)
            + Op.POP(
                Op.STATICCALL(
                    address=PrecompileSpec.ECRECOVER,
                    args_size=128,
                    ret_offset=128,
                    ret_size=32,
                )
            )
            + Op.SSTORE(slot, Op.MLOAD(128))
        )

    driver = pre.deploy_contract(
        recover_into(0)
        + Op.POP(call_with(eoa, template))
        + recover_into(1)
        + Op.STOP
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=driver, data=bytes(recover_input)
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            driver: Account(
                storage={
                    0: eoa,
                    1: SENTINEL if fork.is_eip_enabled(8151) else eoa,
                }
            ),
            eoa: Account(code=SSTORE_MARKER_A, storage={RESULT_SLOT: 1}),
        },
    )
