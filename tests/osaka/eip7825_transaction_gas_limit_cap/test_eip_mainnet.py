"""
Mainnet marked execute checklist tests for
[EIP-7825: Transaction Gas Limit Cap](https://eips.ethereum.org/EIPS/eip-7825).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
)

from .spec import Spec, ref_spec_7825

REFERENCE_SPEC_GIT_PATH = ref_spec_7825.git_path
REFERENCE_SPEC_VERSION = ref_spec_7825.version

pytestmark = [pytest.mark.valid_at("Osaka"), pytest.mark.mainnet]


def test_tx_gas_limit_cap_at_maximum(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test transaction at exactly the gas limit cap (2^24)."""
    storage = Storage()
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1) + Op.STOP,
    )

    tx = Transaction(
        ty=0x02,
        to=contract_address,
        sender=pre.fund_eoa(),
        gas_limit=Spec.tx_gas_limit_cap,
    )

    post = {
        contract_address: Account(storage=storage),
    }

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.exception_test
def test_tx_gas_limit_cap_exceeded(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test transaction exceeding the gas limit cap (2^24 + 1)."""
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(0, 1) + Op.STOP,
    )

    tx = Transaction(
        ty=0x02,
        to=contract_address,
        sender=pre.fund_eoa(),
        gas_limit=Spec.tx_gas_limit_cap + 1,
        error=TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
    )

    state_test(pre=pre, post={}, tx=tx)
