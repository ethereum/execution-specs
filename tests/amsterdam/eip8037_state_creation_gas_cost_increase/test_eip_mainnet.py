"""
Mainnet marked execute checklist tests for
[EIP-8037: State Creation Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create_address,
)

from .spec import init_code_at_high_bytes, ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version

pytestmark = [pytest.mark.valid_at("EIP8037"), pytest.mark.mainnet]


def test_sstore_zero_to_nonzero(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test SSTORE zero-to-nonzero charges state gas and succeeds."""
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


def test_create_charges_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test CREATE charges state gas for new account creation."""
    init_code = Op.STOP
    mstore_value, size = init_code_at_high_bytes(init_code)

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(0, mstore_value)
            + Op.SSTORE(
                storage.store_next(True),
                Op.GT(Op.CREATE(0, 0, size), 0),
            )
        ),
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


def test_create_tx_deploys_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test contract creation transaction succeeds with state gas."""
    sender = pre.fund_eoa()
    tx = Transaction(
        to=None,
        data=Op.STOP,
        state_gas_reservoir=0,
        sender=sender,
    )

    created = compute_create_address(address=sender, nonce=0)
    post = {created: Account(nonce=1, code=b"")}
    state_test(pre=pre, post=post, tx=tx)
