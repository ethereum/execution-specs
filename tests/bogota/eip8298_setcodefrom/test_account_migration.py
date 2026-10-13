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
    Op,
    Transaction,
    TransactionException,
)

from .helpers import (
    MARKER_SLOT,
    RESULT_SLOT,
    SENTINEL,
    SHELL_CODE,
    TEMPLATE_CODE,
    TEMPLATE_MARKER,
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
    template = pre.deploy_contract(TEMPLATE_CODE)
    shell = pre.deploy_contract(SHELL_CODE, storage={RESULT_SLOT: SENTINEL})
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
                code=TEMPLATE_CODE, nonce=nonce, storage={RESULT_SLOT: 1}
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
    template = pre.deploy_contract(TEMPLATE_CODE)
    shell = pre.deploy_contract(SHELL_CODE, storage={RESULT_SLOT: SENTINEL})
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
                code=TEMPLATE_CODE, nonce=nonce, storage={RESULT_SLOT: 1}
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
    template = pre.deploy_contract(TEMPLATE_CODE)
    shell = pre.deploy_contract(SHELL_CODE, storage={RESULT_SLOT: SENTINEL})
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
                code=TEMPLATE_CODE, nonce=nonce, storage={RESULT_SLOT: 1}
            ),
            recipient: Account(balance=10),
        },
    )


def test_migrated_eoa_runs_adopted_code(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """Verify a call to a migrated EOA runs its adopted code."""
    template = pre.deploy_contract(TEMPLATE_CODE)
    shell = pre.deploy_contract(SHELL_CODE, storage={RESULT_SLOT: SENTINEL})
    eoa = pre.fund_eoa(amount=1)
    relayer = pre.fund_eoa()
    migration, nonce = migrate(eoa, 0, relayer, shell, template, False)
    call = Transaction(sender=relayer, to=eoa, value=1)
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[migration]), Block(txs=[call])],
        post={
            eoa: Account(
                code=TEMPLATE_CODE,
                nonce=nonce,
                balance=2,
                storage={RESULT_SLOT: 1, MARKER_SLOT: TEMPLATE_MARKER},
            )
        },
    )
