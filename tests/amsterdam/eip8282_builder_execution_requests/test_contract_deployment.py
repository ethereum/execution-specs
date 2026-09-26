"""
Tests [EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).
"""  # noqa: E501

from os.path import realpath
from pathlib import Path
from typing import Any, Generator

import pytest
from execution_testing import (
    Alloc,
    Block,
    BuilderDepositRequest,
    BuilderExitRequest,
    Header,
    Requests,
    Transaction,
    TransitionFork,
    generate_system_contract_deploy_test,
)
from execution_testing.checklists import EIPChecklist
from execution_testing.forks import Amsterdam

from .spec import ref_spec_8282

REFERENCE_SPEC_GIT_PATH = ref_spec_8282.git_path
REFERENCE_SPEC_VERSION = ref_spec_8282.version

MIN_DEPOSIT_GWEI = BuilderDepositRequest.min_deposit_wei // 10**9


@pytest.mark.eels_base_coverage
@EIPChecklist.SystemContract.Test.Deployment.Address()
@EIPChecklist.SystemContract.Test.Deployment.Missing()
@generate_system_contract_deploy_test(
    fork=Amsterdam,
    factory_json_path=Path(realpath(__file__)).parent
    / "builder_deposit_factory_deploy.json",
    expected_deploy_address=BuilderDepositRequest.system_contract_address,
    fail_on_empty_code=True,
)
def test_builder_deposit_contract_deployment(
    *,
    fork: TransitionFork,
    pre: Alloc,
    **kwargs: Any,
) -> Generator[Block, None, None]:
    """Verify calling the builder deposit contract after deployment."""
    sender = pre.fund_eoa()
    deposit_request = BuilderDepositRequest(
        pubkey=0x01,
        withdrawal_credentials=0x02,
        amount=MIN_DEPOSIT_GWEI,
        signature=0x03,
        fee=BuilderDepositRequest.get_fee(0),
    )

    test_transaction = Transaction(
        data=deposit_request.calldata,
        to=BuilderDepositRequest.system_contract_address,
        sender=sender,
        value=deposit_request.value,
    )

    yield Block(
        txs=[test_transaction],
        header_verify=Header(requests_hash=Requests(deposit_request)),
    )


@pytest.mark.eels_base_coverage
@EIPChecklist.SystemContract.Test.Deployment.Address()
@EIPChecklist.SystemContract.Test.Deployment.Missing()
@generate_system_contract_deploy_test(
    fork=Amsterdam,
    factory_json_path=Path(realpath(__file__)).parent
    / "builder_exit_factory_deploy.json",
    expected_deploy_address=BuilderExitRequest.system_contract_address,
    fail_on_empty_code=True,
)
def test_builder_exit_contract_deployment(
    *,
    fork: TransitionFork,
    pre: Alloc,
    **kwargs: Any,
) -> Generator[Block, None, None]:
    """Verify calling the builder exit contract after deployment."""
    sender = pre.fund_eoa()
    exit_request = BuilderExitRequest(
        pubkey=0x01,
        source_address=sender,
        fee=BuilderExitRequest.get_fee(0),
    )

    test_transaction = Transaction(
        data=exit_request.calldata,
        to=BuilderExitRequest.system_contract_address,
        sender=sender,
        value=exit_request.value,
    )

    yield Block(
        txs=[test_transaction],
        header_verify=Header(requests_hash=Requests(exit_request)),
    )
