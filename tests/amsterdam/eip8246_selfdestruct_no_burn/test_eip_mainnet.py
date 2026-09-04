"""
Mainnet marked execute checklist tests for
[EIP-8246: Remove SELFDESTRUCT Burn](https://eips.ethereum.org/EIPS/eip-8246).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing import (
    Macros as Om,
)

from .spec import ref_spec_8246

REFERENCE_SPEC_GIT_PATH = ref_spec_8246.git_path
REFERENCE_SPEC_VERSION = ref_spec_8246.version

pytestmark = [pytest.mark.valid_at("EIP8246"), pytest.mark.mainnet]

ENDOWMENT = 1


def test_create_tx_selfdestruct_to_self_keeps_balance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """A creation transaction whose initcode self-destructs to itself."""
    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=sender.nonce)

    tx = Transaction(
        sender=sender,
        to=None,
        value=ENDOWMENT,
        data=Op.SELFDESTRUCT(Op.ADDRESS),
    )

    state_test(
        pre=pre,
        post={
            created: Account(balance=ENDOWMENT, nonce=0, code=b"", storage={})
        },
        tx=tx,
    )


def test_factory_create_selfdestruct_to_self_keeps_balance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    A factory CREATEs a contract whose initcode self-destructs to itself.
    The factory then reads the new account's balance and finds the
    endowment still there.
    """
    sender = pre.fund_eoa()
    initcode = Op.SELFDESTRUCT(Op.ADDRESS)
    factory = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + Op.SSTORE(
            0, Op.CREATE(value=Op.CALLVALUE, offset=0, size=len(initcode))
        )
        + Op.SSTORE(1, Op.BALANCE(Op.SLOAD(0)))
        + Op.STOP
    )
    created = compute_create_address(address=factory, nonce=1)

    tx = Transaction(sender=sender, to=factory, value=ENDOWMENT)

    state_test(
        pre=pre,
        post={
            factory: Account(nonce=2, storage={0: created, 1: ENDOWMENT}),
            created: Account(balance=ENDOWMENT, nonce=0, code=b"", storage={}),
        },
        tx=tx,
    )
