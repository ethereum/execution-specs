"""Methods to deploy required contracts for execute command."""

from typing import List, Tuple

from execution_testing.base_types import Address
from execution_testing.client_clis.cli_types import EnginePayloadMetadata
from execution_testing.forks import Fork, TransitionFork
from execution_testing.logging import get_logger
from execution_testing.rpc import EthRPC
from execution_testing.test_types import (
    DETERMINISTIC_FACTORY_ADDRESS,
    DETERMINISTIC_FACTORY_BYTECODE,
    EOA,
    Transaction,
    TransactionTestMetadata,
)

from .rpc.chain_builder_eth_rpc import ChainBuilderEthRPC

logger = get_logger(__name__)


def check_deterministic_factory_deployment(
    *,
    eth_rpc: EthRPC,
    fork: Fork | TransitionFork,
) -> Address | None:
    """Check if the deterministic deployment contract is deployed."""
    fork_deterministic_factory_predeploy_address = (
        fork.transitions_from().deterministic_factory_predeploy_address()
    )
    if fork_deterministic_factory_predeploy_address is not None:
        return fork_deterministic_factory_predeploy_address
    # Check the manually deployed contract.
    deployment_contract_code = eth_rpc.get_code(DETERMINISTIC_FACTORY_ADDRESS)
    if deployment_contract_code == DETERMINISTIC_FACTORY_BYTECODE:
        return DETERMINISTIC_FACTORY_ADDRESS

    return None


def _send_tx_capturing(
    eth_rpc: EthRPC,
    tx: Transaction,
) -> EnginePayloadMetadata | None:
    """
    Send a single tx, returning the built engine payload metadata when
    routed through ``testing_buildBlockV1`` (fill-stateful path) or
    ``None`` for the mempool path (execute).
    """
    if (
        isinstance(eth_rpc, ChainBuilderEthRPC)
        and eth_rpc.testing_rpc is not None
    ):
        return eth_rpc.build_block_with_transactions([tx])
    eth_rpc.send_wait_transactions([tx])
    return None


def deploy_deterministic_factory_contract(
    *,
    eth_rpc: EthRPC,
    seed_key: EOA,
    gas_price: int,
    tx_index: int = 0,
) -> Tuple[int, List[EnginePayloadMetadata]]:
    """
    Deploy the deterministic deployment contract.

    Returns ``(next_tx_index, captured_payloads)``; the captured list is
    only populated on the fill-stateful path (``ChainBuilderEthRPC`` with
    ``testing_rpc``) so callers can write payloads into
    ``pre_run/<start_block_hash>.json``.
    """
    captured: List[EnginePayloadMetadata] = []
    deploy_tx_gas_price = 0x174876E800
    deploy_tx_gas_limit = 0x0186A0
    deploy_tx = Transaction(
        # See https://github.com/Arachnid/deterministic-deployment-proxy for
        # more details on these values.
        ty=0,
        protected=False,
        nonce=0,
        gas_price=deploy_tx_gas_price,
        gas_limit=deploy_tx_gas_limit,
        to=None,
        value=0,
        data=(
            "0x604580600e600039806000f350fe7fffffffffffffffffffffffffffffffffff"
            "ffffffffffffffffffffffffffffe03601600081602082378035828234f5801515"
            "6039578182fd5b8082525050506014600cf3"
        ),
        v=0x1B,
        r=0x2222222222222222222222222222222222222222222222222222222222222222,
        s=0x2222222222222222222222222222222222222222222222222222222222222222,
    ).with_signature_and_sender()
    deploy_tx_sender = deploy_tx.sender
    assert deploy_tx_sender is not None
    required_deployer_balance = deploy_tx_gas_price * deploy_tx_gas_limit
    current_balance = eth_rpc.get_balance(deploy_tx_sender)
    if current_balance < required_deployer_balance:
        # Add transaction to fund the deployer.
        fund_amount = required_deployer_balance - current_balance
        logger.info(
            "Funding deterministic factory deployer address "
            f"{deploy_tx_sender} with "
            f"{fund_amount / 10**18:.18f} ETH"
        )
        fund_tx = Transaction(
            to=deploy_tx_sender,
            value=fund_amount,
            gas_limit=200_000,
            gas_price=gas_price,
            sender=seed_key,
        )
        fund_tx.metadata = TransactionTestMetadata(
            test_id="global",
            phase="setup",
            action="fund_eoa",
            target="Deterministic Factory Deployer",
            tx_index=tx_index,
        )
        tx_index += 1
        fund_payload = _send_tx_capturing(eth_rpc, fund_tx)
        if fund_payload is not None:
            captured.append(fund_payload)
        logger.info(f"Funding transaction mined: {fund_tx.hash}")

    # Add deployment transaction.
    logger.info("Sending deployment transaction...")
    deploy_tx.metadata = TransactionTestMetadata(
        test_id="global",
        phase="setup",
        action="deploy_contract",
        target="Deterministic Factory",
        tx_index=tx_index,
    )
    tx_index += 1
    deploy_payload = _send_tx_capturing(eth_rpc, deploy_tx)
    if deploy_payload is not None:
        captured.append(deploy_payload)
    logger.info(f"Deployment transaction mined: {deploy_tx.hash}")
    deployment_contract_code = eth_rpc.get_code(DETERMINISTIC_FACTORY_ADDRESS)
    logger.info(f"Deployment contract code: {deployment_contract_code}")
    assert deployment_contract_code == DETERMINISTIC_FACTORY_BYTECODE, (
        f"Deployment contract code is not the expected code: "
        f"{deployment_contract_code} != {DETERMINISTIC_FACTORY_BYTECODE}"
    )
    return tx_index, captured
