"""
Test deterministic deployment of contracts through
`pre.deterministic_deploy_contract`.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Fork,
    Hash,
    Op,
    Transaction,
)

from .spec import ref_spec_1014

REFERENCE_SPEC_GIT_PATH = ref_spec_1014.git_path
REFERENCE_SPEC_VERSION = ref_spec_1014.version


@pytest.mark.valid_from("Constantinople")
def test_deterministic_deployment(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test deterministic deployments for contracts using
    `pre.deterministic_deploy_contract`.
    """
    deploy_code = Op.SSTORE(1, Op.CALLDATALOAD(0))

    contract_address = pre.deterministic_deploy_contract(
        deploy_code=deploy_code
    )

    sender = pre.fund_eoa()

    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    # Sized for the set-tx (Hash(1) calldata, with a nonzero byte) since
    # its intrinsic is the larger of the two; `deploy_code.gas_cost(fork)`
    # defaults SSTORE to cold zero->non-zero which slightly over-estimates
    # the reset-tx (already-zero) — harmless.
    tx_gas = (
        intrinsic_calc(calldata=Hash(1))
        + deploy_code.gas_cost(fork)
        + fork.sstore_state_gas()
    )
    reset_tx = Transaction(
        sender=sender,
        to=contract_address,
        data=Hash(0),
        gas_limit=tx_gas,
    )
    set_tx = Transaction(
        sender=sender,
        to=contract_address,
        data=Hash(1),
        gas_limit=tx_gas,
    )

    post = {
        contract_address: Account(
            code=deploy_code,
            storage={
                1: 1,
            },
        ),
    }

    blockchain_test(pre=pre, post=post, blocks=[Block(txs=[reset_tx, set_tx])])
