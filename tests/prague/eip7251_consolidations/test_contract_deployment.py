"""
Tests [EIP-7251: Increase the MAX_EFFECTIVE_BALANCE](https://eips.ethereum.org/EIPS/eip-7251).
"""

from os.path import realpath
from pathlib import Path
from typing import Any, Generator

from execution_testing import (
    Alloc,
    Block,
    ConsolidationRequest,
    Requests,
    Transaction,
    TransitionFork,
    generate_system_contract_deploy_test,
)
from execution_testing.forks import Prague

from .spec import ref_spec_7251

REFERENCE_SPEC_GIT_PATH = ref_spec_7251.git_path
REFERENCE_SPEC_VERSION = ref_spec_7251.version


@generate_system_contract_deploy_test(
    fork=Prague,
    tx_json_path=Path(realpath(__file__)).parent / "contract_deploy_tx.json",
    expected_deploy_address=ConsolidationRequest.system_contract_address,
    fail_on_empty_code=True,
)
def test_system_contract_deployment(
    *,
    fork: TransitionFork,
    pre: Alloc,
    **kwargs: Any,
) -> Generator[Block, None, None]:
    """Verify calling the consolidation system contract after deployment."""
    sender = pre.fund_eoa()
    consolidation_request = ConsolidationRequest(
        source_pubkey=0x01,
        target_pubkey=0x02,
        source_address=sender,
    )
    intrinsic_gas_calculator = (
        fork.transitions_to().transaction_intrinsic_cost_calculator()
    )
    test_transaction_gas = intrinsic_gas_calculator(
        calldata=consolidation_request.calldata
    )

    test_transaction = Transaction(
        data=consolidation_request.calldata,
        gas_limit=test_transaction_gas * 10,
        to=ConsolidationRequest.system_contract_address,
        sender=sender,
        value=consolidation_request.value,
    )

    yield Block(
        txs=[test_transaction],
        requests_hash=Requests(consolidation_request),
    )
