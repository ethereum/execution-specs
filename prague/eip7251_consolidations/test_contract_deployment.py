"""
abstract: Tests [EIP-7251: Increase the MAX_EFFECTIVE_BALANCE](https://eips.ethereum.org/EIPS/eip-7251).
    Test system contract deployment for [EIP-7251: Increase the MAX_EFFECTIVE_BALANCE](https://eips.ethereum.org/EIPS/eip-7251).
"""  # noqa: E501

from os.path import realpath
from pathlib import Path
from typing import Generator

from ethereum_test_forks import Fork, Prague
from ethereum_test_tools import (
    Address,
    Alloc,
    Block,
    Header,
    Requests,
    Transaction,
    generate_system_contract_deploy_test,
)

from .helpers import ConsolidationRequest
from .spec import Spec, ref_spec_7251

REFERENCE_SPEC_GIT_PATH = ref_spec_7251.git_path
REFERENCE_SPEC_VERSION = ref_spec_7251.version


@generate_system_contract_deploy_test(
    fork=Prague,
    tx_json_path=Path(realpath(__file__)).parent / "contract_deploy_tx.json",
    expected_deploy_address=Address(Spec.CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS),
)
def test_system_contract_deployment(
    *,
    fork: Fork,
    pre: Alloc,
    **kwargs,
) -> Generator[Block, None, None]:
    """Verify calling the consolidation system contract after deployment."""
    sender = pre.fund_eoa()
    consolidation_request = ConsolidationRequest(
        source_pubkey=0x01,
        target_pubkey=0x02,
        fee=Spec.get_fee(0),
        source_address=sender,
    )
    pre.fund_address(sender, consolidation_request.value)
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    test_transaction_gas = intrinsic_gas_calculator(calldata=consolidation_request.calldata)

    test_transaction = Transaction(
        data=consolidation_request.calldata,
        gas_limit=test_transaction_gas * 10,
        to=Spec.CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS,
        sender=sender,
        value=consolidation_request.value,
    )

    yield Block(
        txs=[test_transaction],
        header=Header(
            requests_hash=Requests(consolidation_request),
        ),
    )
