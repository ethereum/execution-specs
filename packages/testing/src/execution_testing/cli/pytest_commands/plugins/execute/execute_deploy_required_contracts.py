"""Pytest test to deploy required contracts for execute command."""

import pytest

from execution_testing.base_types import Bytes
from execution_testing.forks import Fork
from execution_testing.logging import get_logger
from execution_testing.rpc import EthRPC
from execution_testing.test_types import (
    DETERMINISTIC_FACTORY_ADDRESS,
    DETERMINISTIC_FACTORY_BYTECODE,
    EOA,
)

from .contracts import (
    check_deterministic_factory_deployment,
    deploy_deterministic_factory_contract,
)

logger = get_logger(__name__)


def test_deploy_deterministic_deployment_contract(
    seed_key: EOA,
    gas_price: int,
    eth_rpc: EthRPC,
    check_only: bool,
    session_fork: Fork,
) -> None:
    """Deploy the deterministic deployment contract to the network."""
    # Check if contract already deployed
    current_deterministic_deployment_contract_address = (
        check_deterministic_factory_deployment(
            eth_rpc=eth_rpc, fork=session_fork
        )
    )
    if current_deterministic_deployment_contract_address is not None:
        logger.info(
            f"✓ Deterministic deployment contract already deployed at "
            f"{current_deterministic_deployment_contract_address}"
        )
        if check_only:
            print(
                f"✓ Contract is already deployed at {current_deterministic_deployment_contract_address}"
            )
        else:
            print(
                f"Contract already exists at {current_deterministic_deployment_contract_address}, skipping deployment"
            )
        return

    if check_only:
        logger.info(
            f"✗ Deterministic deployment contract NOT deployed at {DETERMINISTIC_FACTORY_ADDRESS}"
        )
        print(f"✗ Contract is NOT deployed at {DETERMINISTIC_FACTORY_ADDRESS}")
        pytest.fail("Contract not deployed (check-only mode)")

    try:
        deploy_deterministic_factory_contract(
            eth_rpc=eth_rpc, seed_key=seed_key, gas_price=gas_price
        )
    except Exception as e:
        pytest.fail(f"Failed to deploy contract: {e}")

    # Verify deployment
    deployed_code = eth_rpc.get_code(DETERMINISTIC_FACTORY_ADDRESS)
    if deployed_code != Bytes(DETERMINISTIC_FACTORY_BYTECODE):
        pytest.fail(
            f"Verification failed: Contract code mismatch at {DETERMINISTIC_FACTORY_ADDRESS}. "
            f"Expected: {DETERMINISTIC_FACTORY_BYTECODE}, "
            f"Deployed: {deployed_code}"
        )

    logger.info("✓ Successfully deployed deterministic deployment contract!")
    print(
        f"✓ Successfully deployed contract at {DETERMINISTIC_FACTORY_ADDRESS}"
    )
    print(f"  Contract size: {len(deployed_code)} bytes")
