"""Pytest plugin to run the execute in remote-rpc-mode."""

from pathlib import Path

import pytest

from ethereum_test_forks import Fork
from ethereum_test_rpc import EngineRPC, EthRPC
from ethereum_test_types.chain_config_types import ChainConfigDefaults

from ..pre_alloc import AddressStubs
from .chain_builder_eth_rpc import ChainBuilderEthRPC


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    remote_rpc_group = parser.getgroup(
        "remote_rpc", "Arguments defining remote RPC configuration"
    )
    remote_rpc_group.addoption(
        "--rpc-endpoint",
        required=True,
        action="store",
        dest="rpc_endpoint",
        help="RPC endpoint to an execution client",
    )
    remote_rpc_group.addoption(
        "--rpc-chain-id",
        action="store",
        dest="rpc_chain_id",
        required=False,
        type=int,
        default=None,
        help="DEPRECATED: ID of the chain where the tests will be executed. "
        "This flag is deprecated and will be removed in a future release."
        "Use --chain-id instead.",
    )
    remote_rpc_group.addoption(
        "--tx-wait-timeout",
        action="store",
        dest="tx_wait_timeout",
        type=int,
        default=60,
        help="Maximum time in seconds to wait for a transaction to be included in a block",
    )
    remote_rpc_group.addoption(
        "--address-stubs",
        action="store",
        dest="address_stubs",
        default=AddressStubs(root={}),
        type=AddressStubs.model_validate_json_or_file,
        help="The address stubs for contracts that have already been placed in the chain and to "
        "use for the test. Can be a JSON formatted string or a path to a YAML or JSON file.",
    )

    engine_rpc_group = parser.getgroup(
        "engine_rpc", "Arguments defining engine RPC configuration"
    )
    engine_rpc_group.addoption(
        "--engine-endpoint",
        required=False,
        action="store",
        default=None,
        dest="engine_endpoint",
        help="Engine endpoint to an execution client, which implies that the execute command "
        "will be used to drive the chain. If not provided, it's assumed that the execution client"
        "is connected to a beacon node and the chain progresses automatically. If provided, the"
        "JWT secret must be provided as well.",
    )
    engine_rpc_group.addoption(
        "--engine-jwt-secret",
        required=False,
        action="store",
        default=None,
        dest="engine_jwt_secret",
        help="JWT secret to be used to authenticate with the engine endpoint. Provided string "
        "will be converted to bytes using the UTF-8 encoding.",
    )
    engine_rpc_group.addoption(
        "--engine-jwt-secret-file",
        required=False,
        action="store",
        default=None,
        dest="engine_jwt_secret_file",
        help="Path to a file containing the JWT secret to be used to authenticate with the engine"
        "endpoint. The file must contain only the JWT secret as a hex string.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Check if a chain ID configuration is provided."""
    if (
        config.getoption("rpc_chain_id") is None
        and config.getoption("chain_id") is None
    ):
        pytest.exit("No chain ID configuration found. Please use --chain-id.")
    # Verify the chain ID configuration is consistent with the remote RPC
    # endpoint
    rpc_endpoint = config.getoption("rpc_endpoint")
    eth_rpc = EthRPC(rpc_endpoint)
    remote_chain_id = eth_rpc.chain_id()
    if remote_chain_id != ChainConfigDefaults.chain_id:
        pytest.exit(
            f"Chain ID obtained from the remote RPC endpoint ({remote_chain_id}) does not match "
            f"the configured chain ID ({ChainConfigDefaults.chain_id})."
            "Please check if the chain ID is correctly configured with the --chain-id flag."
        )
    engine_endpoint = config.getoption("engine_endpoint")
    engine_rpc = None
    if engine_endpoint is not None:
        jwt_secret = config.getoption("engine_jwt_secret")
        jwt_secret_file = config.getoption("engine_jwt_secret_file")
        if jwt_secret is None and jwt_secret_file is None:
            pytest.exit(
                "JWT secret must be provided if engine endpoint is provided. "
                "Please check if the JWT secret is correctly configured with the "
                "--engine-jwt-secret or --engine-jwt-secret-file flag."
            )
        elif jwt_secret_file is not None:
            with open(jwt_secret_file, "r") as f:
                jwt_secret = f.read().strip()
            if jwt_secret.startswith("0x"):
                jwt_secret = jwt_secret[2:]
            try:
                jwt_secret = bytes.fromhex(jwt_secret)
            except ValueError:
                pytest.exit(
                    "JWT secret must be a hex string if provided as a file. "
                    "Please check if the JWT secret is correctly configured with the "
                    "--engine-jwt-secret-file flag."
                )
        if isinstance(jwt_secret, str):
            jwt_secret = jwt_secret.encode("utf-8")
        assert isinstance(jwt_secret, bytes), (
            f"JWT secret must be a bytes object, got {type(jwt_secret)}"
        )
        engine_rpc = EngineRPC(engine_endpoint, jwt_secret=jwt_secret)
        # TODO: Perform a request to the engine endpoint to verify that the JWT
        # secret is valid. Potentially could be `engine_getClientVersionV1` but
        # need to implement this in rpc.py.
    config.engine_rpc = engine_rpc  # type: ignore


@pytest.fixture(scope="session")
def engine_rpc(request: pytest.FixtureRequest) -> EngineRPC | None:
    """Execute remote command does not have access to the engine RPC."""
    return request.config.engine_rpc  # type: ignore


@pytest.fixture(autouse=True, scope="session")
def rpc_endpoint(request: pytest.FixtureRequest) -> str:
    """
    Return remote RPC endpoint to be used to make requests to the execution
    client.
    """
    return request.config.getoption("rpc_endpoint")


@pytest.fixture(autouse=True, scope="session")
def eth_rpc(
    request: pytest.FixtureRequest,
    rpc_endpoint: str,
    engine_rpc: EngineRPC | None,
    session_fork: Fork,
    transactions_per_block: int,
    session_temp_folder: Path,
) -> EthRPC:
    """Initialize ethereum RPC client for the execution client under test."""
    tx_wait_timeout = request.config.getoption("tx_wait_timeout")
    if engine_rpc is None:
        return EthRPC(rpc_endpoint, transaction_wait_timeout=tx_wait_timeout)
    get_payload_wait_time = request.config.getoption("get_payload_wait_time")
    return ChainBuilderEthRPC(
        rpc_endpoint=rpc_endpoint,
        fork=session_fork,
        engine_rpc=engine_rpc,
        transactions_per_block=transactions_per_block,
        session_temp_folder=session_temp_folder,
        get_payload_wait_time=get_payload_wait_time,
        transaction_wait_timeout=tx_wait_timeout,
    )
