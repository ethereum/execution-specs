"""
Mainnet marked execute checklist tests for
[EIP-8024: Stack Access Instructions](https://eips.ethereum.org/EIPS/eip-8024).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import ref_spec_8024

REFERENCE_SPEC_GIT_PATH = ref_spec_8024.git_path
REFERENCE_SPEC_VERSION = ref_spec_8024.version

pytestmark = [pytest.mark.valid_at("EIP8024"), pytest.mark.mainnet]


def test_stack_access_opcodes_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that DUPN, SWAPN and EXCHANGE execute with correct results.

    Each opcode moves a distinct planted marker to the top of the stack,
    which is then stored. The opcodes do not depend on any environment
    value, so the full post-state assertion holds when `execute`-ed on a
    live network. Storage keys start at nonzero canaries so a failed
    transaction is distinguishable from a successful one.
    """
    canary = 0xBA5E
    overwrite_canary = Op.SSTORE.with_metadata(original_value=canary)
    dupn_marker = 0xA1
    swapn_marker = 0xB2
    exchange_marker = 0xC3

    code = (
        # DUPN: duplicate the marker planted at depth 17.
        Op.PUSH1(dupn_marker)
        + Op.PUSH0 * 16
        + Op.DUPN[17]
        + Op.PUSH1(0)
        + overwrite_canary
        # SWAPN: swap the top with the marker planted at depth 18.
        + Op.PUSH1(swapn_marker)
        + Op.PUSH0 * 17
        + Op.SWAPN[17]
        + Op.PUSH1(1)
        + overwrite_canary
        # EXCHANGE: move the marker from depth 3 to depth 2, then POP.
        + Op.PUSH1(exchange_marker)
        + Op.PUSH0 * 2
        + Op.EXCHANGE[1, 2]
        + Op.POP
        + Op.PUSH1(2)
        + overwrite_canary
        + Op.STOP
    )
    contract = pre.deploy_contract(
        code=code,
        storage=dict.fromkeys(range(3), canary),
    )
    gas_limit = fork.transaction_intrinsic_cost_calculator()() + code.gas_cost(
        fork
    )
    tx = Transaction(
        ty=0x02,
        to=contract,
        sender=pre.fund_eoa(),
        gas_limit=gas_limit,
    )
    post = {
        contract: Account(
            storage={
                0: dupn_marker,
                1: swapn_marker,
                2: exchange_marker,
            },
        ),
    }

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
