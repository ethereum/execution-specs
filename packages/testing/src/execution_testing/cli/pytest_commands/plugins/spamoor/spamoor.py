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
    group.addoption(
        "--spamoor-sidecars",
        dest="spamoor_sidecars",
        type=int,
        default=3,
        help="Max blob sidecars per blob transaction",
    )
    group.addoption(
        "--spamoor-blob-fee",
        dest="spamoor_blob_fee",
        type=int,
        default=20_000_000_000,
        help="Max blob fee in wei",
    )
    group.addoption(
        "--spamoor-gas-units-to-burn",
        dest="spamoor_gas_units_to_burn",
        type=int,
        default=2_000_000,
        help="Per-tx gas limit for gasburnertx execution transactions",
    )
    group.addoption(
        "--spamoor-pair-count",
        dest="spamoor_pair_count",
        type=int,
        default=1,
        help="Number of uniswap pairs (informational for the port)",
    )
    group.addoption(
        "--spamoor-min-swap-amount",
        dest="spamoor_min_swap_amount",
        type=int,
        default=100_000_000_000_000_000,
        help="Minimum swap amount in wei (0.1 token by default)",
    )
    group.addoption(
        "--spamoor-max-swap-amount",
        dest="spamoor_max_swap_amount",
        type=int,
        default=1_000_000_000_000_000_000_000,
        help="Maximum swap amount in wei (1000 tokens by default)",
    )
    group.addoption(
        "--spamoor-buy-ratio",
        dest="spamoor_buy_ratio",
        type=int,
        default=40,
        help="Percent of swaps that are buys (0..100)",
    )
    group.addoption(
        "--spamoor-slippage",
        dest="spamoor_slippage",
        type=int,
        default=50,
        help="Slippage in basis points (out of 10000)",
    )
    group.addoption(
        "--spamoor-min-code-size",
        dest="spamoor_min_code_size",
        type=int,
        default=100,
        help="Minimum fuzz bytecode size in bytes",
    )
    group.addoption(
        "--spamoor-max-code-size",
        dest="spamoor_max_code_size",
        type=int,
        default=512,
        help="Maximum fuzz bytecode size in bytes",
    )
    group.addoption(
        "--spamoor-payload-seed",
        dest="spamoor_payload_seed",
        type=str,
        default="",
        help="Hex seed for evm-fuzz bytecode generator (empty = deterministic default)",
    )
    group.addoption(
        "--spamoor-tx-id-offset",
        dest="spamoor_tx_id_offset",
        type=int,
        default=0,
        help="Shift evm-fuzz per-tx IDs by this offset",
    )
    group.addoption(
        "--spamoor-fuzz-mode",
        dest="spamoor_fuzz_mode",
        type=str,
        default="all",
        help="evm-fuzz mode: 'all' | 'opcodes' | 'precompiles'",
    )
    group.addoption(
        "--spamoor-random-target",
        dest="spamoor_random_target",
        action="store_true",
        default=False,
        help="Use pseudo-random recipients for erc20tx transfers",
    )
    group.addoption(
        "--spamoor-random-amount",
        dest="spamoor_random_amount",
        action="store_true",
        default=False,
        help="Use pseudo-random amounts for erc20tx transfers",
    )
    group.addoption(
        "--spamoor-reuse-contract",
        dest="spamoor_reuse_contract",
        action="store_true",
        default=False,
        help="storagespam: reuse existing deployed contract (skip deploy tx)",
    )
    group.addoption(
        "--spamoor-addresses-per-tx",
        dest="spamoor_addresses_per_tx",
        type=int,
        default=370,
        help="erc20_bloater: addresses bloated per transaction",
    )
    group.addoption(
        "--spamoor-start-address-index",
        dest="spamoor_start_address_index",
        type=int,
        default=1,
        help="erc20_bloater: starting contract slot index",
    )
    group.addoption(
        "--spamoor-slots-per-call",
        dest="spamoor_slots_per_call",
        type=int,
        default=500,
        help="storagerefundtx: number of slots written+cleared per execute() call",
    )
    group.addoption(
        "--spamoor-bytecodes",
        dest="spamoor_bytecodes",
        type=str,
        default="",
        help="deploytx: comma-separated list of hex bytecodes to cycle through",
    )
    group.addoption(
        "--spamoor-bytecodes-file",
        dest="spamoor_bytecodes_file",
        type=str,
        default="",
        help="deploytx: path to file with one hex bytecode per line",
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
        "sidecars": request.config.getoption("spamoor_sidecars"),
        "blob_fee": request.config.getoption("spamoor_blob_fee"),
        "gas_units_to_burn": request.config.getoption(
            "spamoor_gas_units_to_burn"
        ),
        "pair_count": request.config.getoption("spamoor_pair_count"),
        "min_swap_amount": request.config.getoption(
            "spamoor_min_swap_amount"
        ),
        "max_swap_amount": request.config.getoption(
            "spamoor_max_swap_amount"
        ),
        "buy_ratio": request.config.getoption("spamoor_buy_ratio"),
        "slippage": request.config.getoption("spamoor_slippage"),
        "min_code_size": request.config.getoption("spamoor_min_code_size"),
        "max_code_size": request.config.getoption("spamoor_max_code_size"),
        "payload_seed": request.config.getoption("spamoor_payload_seed"),
        "tx_id_offset": request.config.getoption("spamoor_tx_id_offset"),
        "fuzz_mode": request.config.getoption("spamoor_fuzz_mode"),
        "random_target": request.config.getoption("spamoor_random_target"),
        "random_amount": request.config.getoption("spamoor_random_amount"),
        "reuse_contract": request.config.getoption("spamoor_reuse_contract"),
        "addresses_per_tx": request.config.getoption(
            "spamoor_addresses_per_tx"
        ),
        "start_address_index": request.config.getoption(
            "spamoor_start_address_index"
        ),
        "slots_per_call": request.config.getoption("spamoor_slots_per_call"),
        "bytecodes": request.config.getoption("spamoor_bytecodes"),
        "bytecodes_file": request.config.getoption("spamoor_bytecodes_file"),
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
