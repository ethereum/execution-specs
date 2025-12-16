"""
Test deterministic deployment of contracts through
`pre.deterministic_deploy_contract`.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import ref_spec_1014

REFERENCE_SPEC_GIT_PATH = ref_spec_1014.git_path
REFERENCE_SPEC_VERSION = ref_spec_1014.version


@pytest.mark.valid_from("Constantinople")
def test_deterministic_deployment(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test deterministic deployments for contracts using
    `pre.deterministic_deploy_contract`.
    """
    deploy_code = Op.SSTORE(1, Op.CALLDATALOAD(0))

    contract_address = pre.deterministic_deploy_contract(
        deploy_code=deploy_code,
        # A setup transaction is sent after deployment with `Hash(0)` as
        # calldata to restore the contract's storage.
        setup_calldata=Hash(0),
    )

    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=contract_address,
        data=Hash(1),
        gas_limit=100_000,
    )

    post = {
        contract_address: Account(
            deploy_code=deploy_code,
            storage={
                1: 1,
            },
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
