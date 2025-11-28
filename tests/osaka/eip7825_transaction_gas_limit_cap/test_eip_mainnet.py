"""
Mainnet tests for transaction gas limit cap [EIP-7825: Transaction Gas Limit
Cap](https://eips.ethereum.org/EIPS/eip-7825).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
)

from .spec import ref_spec_7825

# Update reference spec constants
REFERENCE_SPEC_GIT_PATH = ref_spec_7825.git_path
REFERENCE_SPEC_VERSION = ref_spec_7825.version

pytestmark = [pytest.mark.valid_at("Osaka"), pytest.mark.mainnet]


@pytest.mark.exception_test
def test_tx_gas_limit_cap_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
) -> None:
    """Negative test going beyond transaction gas limit cap."""
    target_gas_wasted_min = 2 ^ 24 + 1

    # repeatedly call BALANCE on different addresses until we detect
    # that we used up target_gas_wasted_min
    code = (
        Op.PUSH4[target_gas_wasted_min]
        + Op.GAS
        + Op.PUSH1[0x0]
        + Op.JUMPDEST
        + Op.DUP1
        + Op.BALANCE
        + Op.POP
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.GAS
        + Op.DUP4
        + Op.SWAP1
        + Op.SUB
        + Op.DUP4
        + Op.GT
        + Op.PUSH1[0x8]
        + Op.JUMPI
        + Op.STOP
    )

    caller_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=caller_address,
        sender=pre.fund_eoa(),
        gas_limit=17_000_000,  # more than target_gas_wasted_min
        error=TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
    )

    state_test(env=env, pre=pre, post={}, tx=tx)
