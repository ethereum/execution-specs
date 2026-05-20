"""
Mainnet marked execute checklist tests for
[EIP-8037: State Creation Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version

pytestmark = [pytest.mark.valid_at("EIP8037"), pytest.mark.mainnet]


def test_sstore_zero_to_nonzero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test SSTORE zero-to-nonzero charges state gas and succeeds."""
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


def test_create_charges_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test CREATE charges state gas for new account creation."""
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    init_code = Op.STOP

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(init_code), "big")
                << (256 - 8 * len(init_code)),
            )
            + Op.SSTORE(
                storage.store_next(True),
                Op.GT(Op.CREATE(0, 0, len(init_code)), 0),
            )
        ),
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


def test_create_tx_deploys_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test contract creation transaction succeeds with state gas."""
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    tx = Transaction(
        to=None,
        data=Op.STOP,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={}, tx=tx)
