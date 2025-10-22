"""Pytest plugin to test the `eth_config` RPC endpoint in a node."""

import re
from os.path import realpath
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

import pytest
import requests

from ethereum_test_rpc import EthRPC
from pytest_plugins.custom_logging import get_logger

from .execute_types import Genesis, NetworkConfigFile

CURRENT_FILE = Path(realpath(__file__))
CURRENT_FOLDER = CURRENT_FILE.parent

DEFAULT_NETWORK_CONFIGS_FILE = CURRENT_FOLDER / "networks.yml"
DEFAULT_NETWORKS = NetworkConfigFile.from_yaml(DEFAULT_NETWORK_CONFIGS_FILE)

EXECUTION_CLIENTS = [
    "besu",
    "erigon",
    "geth",
    "nethermind",
    "nimbusel",
    "reth",
]
CONSENSUS_CLIENTS = [
    "grandine",
    "lighthouse",
    "lodestar",
    "nimbus",
    "prysm",
    "teku",
]

logger = get_logger(__name__)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    eth_config_group = parser.getgroup(
        "execute", "Arguments defining eth_config test behavior."
    )
    eth_config_group.addoption(
        "--network",
        action="store",
        dest="network",
        required=False,
        type=str,
        default=None,
        help=(
            "Name of the network to verify for the RPC client. Supported networks by default: "
            f"{', '.join(DEFAULT_NETWORKS.root.keys())}."
        ),
    )
    eth_config_group.addoption(
        "--network-config-file",
        action="store",
        dest="network_config_file",
        required=False,
        type=Path,
        default=None,
        help="Path to the yml file that contains custom network configuration "
        "(e.g. ./src/pytest_plugins/execute/eth_config/networks.yml).\nIf no config is provided "
        "then majority mode will be used for devnet testing (clients that have a different "
        "response than the majority of clients will fail the test)",
    )
    eth_config_group.addoption(
        "--clients",
        required=False,
        action="store",
        dest="clients",
        type=str,
        default=None,
        help="Comma-separated list of clients to be tested in majority mode. Example: "
        '"besu,erigon,geth,nethermind,nimbusel,reth"\nIf you do not pass a value, majority mode '
        "testing will be disabled.",
    )
    eth_config_group.addoption(
        "--genesis-config-file",
        action="store",
        dest="genesis_config_file",
        required=False,
        type=Path,
        default=None,
        help="Path to a genesis JSON file from which a custom network configuration "
        "must be derived.",
    )
    eth_config_group.addoption(
        "--genesis-config-url",
        action="store",
        dest="genesis_config_url",
        required=False,
        type=str,
        default=None,
        help="URL to a genesis JSON file from which a custom network configuration "
        "must be derived.",
    )
    eth_config_group.addoption(
        "--rpc-endpoint",
        required=True,
        action="store",
        dest="rpc_endpoint",
        help="RPC endpoint to the execution client that will be tested.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """
    Load the network configuration file and load the specific network to be
    used for the test.
    """
    genesis_config_file = config.getoption("genesis_config_file")
    genesis_config_url = config.getoption("genesis_config_url")
    network_configs_path = config.getoption("network_config_file")
    network_name = config.getoption("network")
    rpc_endpoint = config.getoption("rpc_endpoint")
    # majority mode
    clients = config.getoption("clients")
    config.option.majority_clients = []  # List[str]

    if genesis_config_file and genesis_config_url:
        pytest.exit(
            "Cannot specify both the --genesis-config-file and --genesis-config-url flags."
        )

    if (genesis_config_file or genesis_config_url) and network_name:
        pytest.exit(
            "Cannot specify a network name when using the --genesis-config-file or "
            "--genesis-config-url flag."
        )
    # handle the one of the three flags that was passed
    #   case 1: genesis_config_file
    if genesis_config_file:
        genesis_config_contents = genesis_config_file.read_text()
        genesis_config = Genesis.model_validate_json(genesis_config_contents)
        config.network = genesis_config.network_config()  # type: ignore
    #   case 2: genesis_config_url
    elif genesis_config_url:
        genesis_config_contents = requests.get(genesis_config_url).text
        genesis_config = Genesis.model_validate_json(genesis_config_contents)
        config.network = genesis_config.network_config()  # type: ignore
    #   case 3: network_name
    elif network_name:
        # load provided networks file
        if network_configs_path is None:
            network_configs_path = DEFAULT_NETWORK_CONFIGS_FILE
        if not network_configs_path.exists():
            pytest.exit(
                f'Specified networks file "{network_configs_path}" does not exist.'
            )
        try:
            network_configs = NetworkConfigFile.from_yaml(network_configs_path)
        except Exception as e:
            pytest.exit(f"Could not load file {network_configs_path}: {e}")

        if network_name not in network_configs.root:
            pytest.exit(
                f'Network "{network_name}" could not be found in file "{network_configs_path}".'
            )
        config.network = network_configs.root[network_name]  # type: ignore

    # determine whether to activate majority mode or not
    if clients:
        clients.replace(" ", "")
        clients = clients.split(",")
        for c in clients:
            if c not in EXECUTION_CLIENTS:
                pytest.exit(f"Unsupported client was passed: {c}")
        logger.info(f"Provided client list: {clients}")
        # activate majority mode if also URL condition is met
        if ".ethpandaops.io" in rpc_endpoint:
            logger.info("Ethpandaops RPC detected")
            logger.info("Toggling majority test on")
            config.option.majority_clients = clients  # List[str]
    else:
        logger.info(
            "Majority test mode is disabled because no --clients value was passed."
        )

    if config.getoption("collectonly", default=False):
        return

    # Test out the RPC endpoint to be able to fail fast if it's not working
    eth_rpc = EthRPC(rpc_endpoint)
    try:
        logger.debug(
            "Will now perform a connection check (request chain_id).."
        )
        chain_id = eth_rpc.chain_id()
        logger.debug(
            f"Connection check ok (successfully got chain id {chain_id})"
        )
    except Exception as e:
        pytest.exit(f"Could not connect to RPC endpoint {rpc_endpoint}: {e}")
    try:
        logger.debug(
            "Will now briefly check whether eth_config is supported by target rpc.."
        )
        eth_rpc.config()
        logger.debug(
            "Connection check ok (successfully got eth_config response)"
        )
    except Exception as e:
        pytest.exit(
            f"RPC endpoint {rpc_endpoint} does not support `eth_config`: {e}"
        )


@pytest.fixture(autouse=True, scope="session")
def rpc_endpoint(request: pytest.FixtureRequest) -> str:
    """
    Return remote RPC endpoint to be used to make requests to the execution
    client.
    """
    return request.config.getoption("rpc_endpoint")


def all_rpc_endpoints(config: pytest.Config) -> Dict[str, List[EthRPC]]:
    """
    Derive a mapping of exec clients to the RPC URLs they are reachable at.
    """
    rpc_endpoint = config.getoption("rpc_endpoint")
    # besu, erigon, ..
    el_clients: List[str] = config.getoption("majority_clients")
    if len(el_clients) == 0:
        endpoint_name = rpc_endpoint
        try:
            parsed = urlparse(rpc_endpoint)
            endpoint_name = parsed.hostname
        except Exception:
            pass
        return {endpoint_name: [EthRPC(rpc_endpoint)]}

    pattern = r"(.*?@rpc\.)([^-]+)-([^-]+)(-.*)"
    url_dict: Dict[str, List[EthRPC]] = {
        exec_client: [
            EthRPC(
                re.sub(
                    pattern,
                    f"\\g<1>{consensus}-{exec_client}\\g<4>",
                    rpc_endpoint,
                )
            )
            for consensus in CONSENSUS_CLIENTS
        ]
        for exec_client in el_clients
    }
    # url_dict looks like this:
    # { 'besu': [<EthRPC that holds url for grandine+besu>,
    #            <EthRPC that holds url for lighthouse+besu>, ..],
    #   'erigon':  ... ... }
    return url_dict


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate tests for all clients under test."""
    # all_rpc_endpoints is a dictionary with the name of the exec client as key
    # and the possible URLs to contact it (different cl combinations) as value
    # list
    all_rpc_endpoints_dict = all_rpc_endpoints(metafunc.config)

    if metafunc.definition.name == "test_eth_config_majority":
        if len(all_rpc_endpoints_dict) < 2:
            # The test function is not run because we only have a single
            # client, so no majority comparison
            logger.info(
                "Skipping eth_config majority because less than 2 exec clients were passed"
            )
            metafunc.parametrize(
                ["all_rpc_endpoints"],
                [
                    pytest.param(
                        all_rpc_endpoints_dict,
                        id=metafunc.definition.name,
                        marks=pytest.mark.skip("Only one client"),
                    )
                ],
            )
        else:
            metafunc.parametrize(
                ["all_rpc_endpoints"],
                [
                    pytest.param(
                        all_rpc_endpoints_dict,
                        id=metafunc.definition.name,
                    )
                ],
                scope="function",
            )
    else:
        metafunc.parametrize(
            ["eth_rpc"],
            [
                pytest.param(
                    rpc_endpoint,
                    id=f"{metafunc.definition.name}[{endpoint_name}]",
                )
                for endpoint_name, rpc_endpoint in all_rpc_endpoints_dict.items()
            ],
            scope="function",
        )
