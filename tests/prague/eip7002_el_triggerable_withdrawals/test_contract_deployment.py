"""
Tests [EIP-7002: Execution layer triggerable withdrawals](https://eips.ethereum.org/EIPS/eip-7002).
"""

from os.path import realpath
from pathlib import Path
from typing import Any, Generator

import pytest
from execution_testing import (
    Alloc,
    Block,
    Requests,
    Transaction,
    TransitionFork,
    WithdrawalRequest,
    generate_system_contract_deploy_test,
)
from execution_testing.forks import Prague

from .spec import ref_spec_7002

REFERENCE_SPEC_GIT_PATH = ref_spec_7002.git_path
REFERENCE_SPEC_VERSION = ref_spec_7002.version


@pytest.mark.eels_base_coverage
@generate_system_contract_deploy_test(
    fork=Prague,
    tx_json_path=Path(realpath(__file__)).parent / "contract_deploy_tx.json",
    expected_deploy_address=WithdrawalRequest.system_contract_address,
    fail_on_empty_code=True,
)
def test_system_contract_deployment(
    *,
    fork: TransitionFork,
    pre: Alloc,
    **kwargs: Any,
) -> Generator[Block, None, None]:
    """Verify calling the withdrawals system contract after deployment."""
    sender = pre.fund_eoa()
    withdrawal_request = WithdrawalRequest(
        validator_pubkey=0x01,
        amount=1,
        source_address=sender,
    )
    intrinsic_gas_calculator = (
        fork.transitions_to().transaction_intrinsic_cost_calculator()
    )
    test_transaction_gas = intrinsic_gas_calculator(
        calldata=withdrawal_request.calldata
    )

    test_transaction = Transaction(
        data=withdrawal_request.calldata,
        gas_limit=test_transaction_gas * 10,
        to=WithdrawalRequest.system_contract_address,
        sender=sender,
        value=withdrawal_request.value,
    )

    yield Block(
        txs=[test_transaction],
        requests_hash=Requests(withdrawal_request),
    )
