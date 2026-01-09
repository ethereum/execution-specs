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

    reset_tx = Transaction(
        sender=sender,
        to=contract_address,
        data=Hash(0),
        gas_limit=100_000,
    )
    set_tx = Transaction(
        sender=sender,
        to=contract_address,
        data=Hash(1),
        gas_limit=100_000,
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
