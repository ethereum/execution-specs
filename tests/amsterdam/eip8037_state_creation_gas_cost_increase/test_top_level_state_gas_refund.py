"""
Opposite of ethereum/execution-specs#2595: state gas refunded on
top-level failure (ethereum/EIPs#11476).

TX1 pushes block_state above block_regular via large deploy.
TX2 is a failing CREATE whose initcode state gas (GAS_NEW_ACCOUNT)
must NOT count in block_state_gas_used.

Tests for [EIP-8037](https://eips.ethereum.org/EIPS/eip-8037).
See: ethereum/EIPs#11476
"""

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Fork,
    Op,
    Transaction,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@pytest.mark.parametrize(
    "state_op",
    [
        pytest.param(
            Op.POP(Op.CALL(gas=100_000, address=0xDEAD, value=1)),
            id="call_new_account",
        ),
        pytest.param(
            Op.POP(Op.CREATE(value=0, offset=0, size=1)),
            id="inner_create",
        ),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_top_level_failure_refunds_execution_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    state_op: bytes,
) -> None:
    """
    TX1 makes state gas the binding dimension. TX2's initcode state
    gas (GAS_NEW_ACCOUNT) must not count in block_state_gas_used
    after code deposit failure.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    # --- TX1: Deploy a 14 KiB contract (high state gas) ---
    deploy_size = 14_000
    tx1_create_state = fork.create_state_gas(code_size=deploy_size)
    tx1_gas_limit = gas_limit_cap + tx1_create_state

    sender1 = pre.fund_eoa(10**21)
    tx1 = Transaction(
        to=None,
        data=Op.RETURN(0, deploy_size),
        gas_limit=tx1_gas_limit,
        sender=sender1,
    )

    # --- TX2: Failing CREATE with initcode state ops ---
    oversized = fork.max_code_size() + 232
    initcode = state_op + Op.RETURN(0, oversized)

    sender2 = pre.fund_eoa(10**21)
    tx2 = Transaction(
        to=None,
        data=initcode,
        value=10**18,
        gas_limit=gas_limit_cap,
        sender=sender2,
    )

    blockchain_test(
        genesis_environment=Environment(gas_limit=100_000_000),
        pre=pre,
        blocks=[
            Block(
                txs=[tx1, tx2],
                gas_limit=100_000_000,
            ),
        ],
        post={},
    )
