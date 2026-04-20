import pytest
import requests


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("spamoor", "Spamoor load generation tool options")
    group.addoption(
        "--spamoor-endpoint",
        "--rpc-url",
        dest="spamoor_endpoint",
        default="http://localhost:8545",
        help="RPC endpoint",
    )
    group.addoption(
        "--spamoor-count",
        "--transactions-count",
        dest="spamoor_count",
        type=int,
        default=10,
        help="Number of txs",
    )
    group.addoption(
        "--spamoor-throughput",
        type=float,
        default=1.0,
        help="Txs per slot/second multiplier",
    )
    group.addoption(
        "--spamoor-basefee",
        type=int,
        default=None,
        help="Basefee override in wei",
    )
    group.addoption(
        "--spamoor-amount",
        type=int,
        default=1000000000000000000,
        help="Amount in wei",
    )
    group.addoption(
        "--spamoor-from", type=str, default=None, help="Sender address"
    )
    group.addoption(
        "--spamoor-private-key",
        type=str,
        default=None,
        help="Private key for signing",
    )
    group.addoption(
        "--spamoor-contract-code",
        type=str,
        default=None,
        help="Contract bytecode to deploy",
    )
    group.addoption(
        "--spamoor-contract-address",
        type=str,
        default=None,
        help="Contract address for execution txs",
    )
    group.addoption(
        "--spamoor-call-data",
        type=str,
        default="",
        help="Call data for execution txs",
    )
    group.addoption(
        "--spamoor-deploy-gas-limit",
        type=int,
        default=2000000,
        help="Gas limit for deployment",
    )
    group.addoption(
        "--spamoor-call-fn-sig",
        type=str,
        default="",
        help="Function signature for call",
    )
    group.addoption(
        "--spamoor-call-args",
        type=str,
        default="[]",
        help="JSON list of call arguments",
    )
    group.addoption(
        "--spamoor-contract-args",
        type=str,
        default="[]",
        help="JSON list of constructor arguments",
    )
    group.addoption(
        "--spamoor-gas-limit",
        type=int,
        default=0,
        help="Gas limit for execution txs (0=dynamic/fallback)",
    )
    group.addoption(
        "--spamoor-tip-fee",
        type=int,
        default=1_000_000_000,
        help="Priority fee in wei",
    )
    group.addoption(
        "--spamoor-start-salt",
        dest="spamoor_start_salt",
        type=int,
        default=0,
        help="Salt to start the Spamoor sequence",
    )
    group.addoption(
        "--spamoor-init-code",
        dest="spamoor_init_code",
        type=str,
        default="",
        help="Initialization code for Spamoor",
    )
    group.addoption(
        "--spamoor-factory-address",
        dest="spamoor_factory_address",
        type=str,
        default="",
        help="Factory contract address for Spamoor initialization",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "spamoor: Run spamoor load generation tests"
    )


@pytest.fixture(scope="session")
def spamoor_config(request):
    return {
        "endpoint": request.config.getoption("spamoor_endpoint"),
        "count": request.config.getoption("spamoor_count"),
        "throughput": request.config.getoption("--spamoor-throughput"),
        "basefee": request.config.getoption("--spamoor-basefee"),
        "amount": request.config.getoption("--spamoor-amount"),
        "from_addr": request.config.getoption("--spamoor-from"),
        "private_key": request.config.getoption("--spamoor-private-key"),
        "contract_code": request.config.getoption("--spamoor-contract-code"),
        "contract_address": request.config.getoption(
            "--spamoor-contract-address"
        ),
        "call_data": request.config.getoption("--spamoor-call-data"),
        "deploy_gas_limit": request.config.getoption(
            "--spamoor-deploy-gas-limit"
        ),
        "call_fn_sig": request.config.getoption("--spamoor-call-fn-sig"),
        "call_args": request.config.getoption("--spamoor-call-args"),
        "contract_args": request.config.getoption("--spamoor-contract-args"),
        "gas_limit": request.config.getoption("--spamoor-gas-limit"),
        "tip_fee": request.config.getoption("--spamoor-tip-fee"),
        # New Spamoor options
        "start_salt": request.config.getoption("spamoor_start_salt"),
        "init_code": request.config.getoption("spamoor_init_code"),
        "factory_address": request.config.getoption("spamoor_factory_address"),
    }


@pytest.fixture(scope="session")
def spamoor_rpc_client(spamoor_config):
    endpoint = spamoor_config["endpoint"]

    def rpc_call(method, params):
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": 1,
            }
            resp = requests.post(endpoint, json=payload, timeout=5)
            resp.raise_for_status()
            return resp.json().get("result")
        except Exception:
            return None

    return rpc_call
