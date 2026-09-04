"""Pytest plugin: CLI options and fixtures for spamoor scenarios."""

import warnings
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest
import requests
import yaml


class SpamoorYAMLWarning(UserWarning):
    """Surface-level warning for YAML scenario overlay issues."""


# YAML key → spamoor_config key.  Infrastructure keys (endpoint, count,
# private_key, from_addr) are intentionally absent so that a CLI invocation
# keeps full control of them regardless of the config file.
_YAML_TO_CONFIG_KEY: Dict[str, str] = {
    "amount": "amount",
    "contract_address": "contract_address",
    "contract_code": "contract_code",
    "call_data": "call_data",
    "call_fn_sig": "call_fn_sig",
    "call_args": "call_args",
    "contract_args": "contract_args",
    "gas_limit": "gas_limit",
    "deploy_gas_limit": "deploy_gas_limit",
    "throughput": "throughput",
    "random_target": "random_target",
    "random_amount": "random_amount",
    "seed": "wallet_seed",
    "total_count": "total_count",
    "max_wallets": "max_wallets",
    "max_pending": "max_pending",
    "rebroadcast": "rebroadcast",
}

# Config-level keys understood by the overlay (either via _YAML_TO_CONFIG_KEY
# or the custom fee handling below).
_MAPPED_YAML_KEYS = set(_YAML_TO_CONFIG_KEY) | {
    "base_fee",
    "base_fee_wei",
    "tip_fee",
    "tip_fee_wei",
    "refill_amount",
    "refill_balance",
}

# Config-level keys that EST intentionally ignores (infrastructure concerns
# with no EST-side analogue). No warning, no strict failure — they're common
# in spammer exports and carry no actionable signal.
_IGNORED_YAML_KEYS = {
    "client_group",
    "deploy_client_group",
    "refill_interval",
    "log_txs",
    "timeout",
}

# Top-level (sibling of `config`) keys allowed on each scenario entry.
_ALLOWED_TOP_LEVEL_KEYS = {"scenario", "name", "description", "config"}


def _is_empty(value: Any) -> bool:
    """Return True when a YAML value carries no user intent."""
    if value is None or value is False:
        return True
    if isinstance(value, (str, list, dict, tuple, set)) and len(value) == 0:
        return True
    if isinstance(value, (int, float)) and value == 0:
        return True
    return False


def _validate_yaml_keys(
    scenario_entry: Dict[str, Any], *, strict: bool
) -> None:
    """
    Check a scenario entry for unknown keys.

    Empty/zero/null/false values for unknown keys always emit a warning.
    Non-empty values for unknown keys warn in non-strict mode and raise
    ``pytest.UsageError`` when ``strict=True``.
    """
    name = scenario_entry.get("name") or "<unnamed>"
    yaml_cfg = scenario_entry.get("config") or {}

    unknown_nonempty: List[str] = []

    for key in scenario_entry:
        if key in _ALLOWED_TOP_LEVEL_KEYS:
            continue
        value = scenario_entry[key]
        if _is_empty(value):
            warnings.warn(
                f"scenario {name!r}: unknown top-level key {key!r} "
                f"(empty value ignored)",
                SpamoorYAMLWarning,
                stacklevel=2,
            )
        else:
            unknown_nonempty.append(f"{key}={value!r} (top-level)")

    if isinstance(yaml_cfg, dict):
        for key, value in yaml_cfg.items():
            if key in _MAPPED_YAML_KEYS or key in _IGNORED_YAML_KEYS:
                continue
            if _is_empty(value):
                warnings.warn(
                    f"scenario {name!r}: unknown config key {key!r} "
                    f"(empty value ignored)",
                    SpamoorYAMLWarning,
                    stacklevel=2,
                )
            else:
                unknown_nonempty.append(f"config.{key}={value!r}")

    if not unknown_nonempty:
        return

    msg = (
        f"scenario {name!r}: the following YAML keys are not supported by "
        f"the EST overlay: " + ", ".join(unknown_nonempty)
    )
    if strict:
        raise pytest.UsageError(msg)
    warnings.warn(msg, SpamoorYAMLWarning, stacklevel=2)


def _load_scenario_from_yaml(path: str, index: int) -> Dict[str, Any]:
    """Return the YAML list entry at *index*, validating structure."""
    p = Path(path)
    if not p.is_file():
        raise pytest.UsageError(
            f"--spamoor-config-file {path!r}: file not found"
        )
    try:
        data = yaml.safe_load(p.read_text())
    except yaml.YAMLError as exc:
        raise pytest.UsageError(
            f"--spamoor-config-file {path!r}: invalid YAML ({exc})"
        ) from exc
    if not isinstance(data, list):
        raise pytest.UsageError(
            f"--spamoor-config-file {path!r}: expected a YAML list at the "
            f"top level, got {type(data).__name__}"
        )
    if index < 0 or index >= len(data):
        raise pytest.UsageError(
            f"--spamoor-scenario-index {index} out of range (file has "
            f"{len(data)} scenario(s))"
        )
    entry = data[index]
    if not isinstance(entry, dict) or "config" not in entry:
        raise pytest.UsageError(
            f"--spamoor-config-file {path!r}: entry #{index} is not a "
            f"scenario object with a 'config' field"
        )
    return entry


def _overlay_yaml_on_config(
    cfg: Dict[str, Any], scenario_entry: Dict[str, Any]
) -> None:
    """
    Overwrite ``cfg`` in place with mapped values from a YAML scenario.

    ``base_fee`` / ``tip_fee`` in the YAML are gwei floats; the ``*_wei``
    variants, when non-empty, take precedence and are interpreted as
    decimal integers. When ``total_count`` is set, it also overrides
    ``cfg["count"]`` — YAML is authoritative when a scenario file is in use.
    """
    yaml_cfg = scenario_entry.get("config") or {}
    if not isinstance(yaml_cfg, dict):
        raise pytest.UsageError(
            f"scenario entry {scenario_entry.get('name')!r} has a non-dict "
            f"'config'"
        )

    for y_key, c_key in _YAML_TO_CONFIG_KEY.items():
        if y_key not in yaml_cfg:
            continue
        value = yaml_cfg[y_key]
        if value is None or value == "":
            continue
        # YAML's safe_load parses ``0xfd1a...`` as a Python int. Address /
        # code / call-data fields must round-trip as hex strings.
        if c_key in (
            "contract_address",
            "contract_code",
            "call_data",
        ) and isinstance(value, int):
            value = "0x" + format(value, "040x" if c_key == "contract_address" else "x")
        cfg[c_key] = value

    # ``*_wei`` may arrive as a Python int (YAML ``safe_load`` default) or
    # as a string (e.g. ``"1000000000"``). Accept both — silently falling
    # back to the gwei field when the int form is present would change the
    # effective fee profile without telling the user.
    base_fee_wei = yaml_cfg.get("base_fee_wei")
    if isinstance(base_fee_wei, int) and not isinstance(base_fee_wei, bool):
        cfg["basefee"] = base_fee_wei
    elif isinstance(base_fee_wei, str) and base_fee_wei.strip():
        cfg["basefee"] = int(base_fee_wei)
    elif isinstance(yaml_cfg.get("base_fee"), (int, float)):
        cfg["basefee"] = int(float(yaml_cfg["base_fee"]) * 1e9)

    tip_fee_wei = yaml_cfg.get("tip_fee_wei")
    if isinstance(tip_fee_wei, int) and not isinstance(tip_fee_wei, bool):
        cfg["tip_fee"] = tip_fee_wei
    elif isinstance(tip_fee_wei, str) and tip_fee_wei.strip():
        cfg["tip_fee"] = int(tip_fee_wei)
    elif isinstance(yaml_cfg.get("tip_fee"), (int, float)):
        cfg["tip_fee"] = int(float(yaml_cfg["tip_fee"]) * 1e9)

    # Spamoor throughput is an int (txs/sec) but the helpers treat it as
    # a float multiplier for max_fee_per_gas. Coerce for consistency.
    if "throughput" in yaml_cfg and yaml_cfg["throughput"] is not None:
        cfg["throughput"] = float(yaml_cfg["throughput"])

    total_count = yaml_cfg.get("total_count")
    if isinstance(total_count, int) and total_count > 0:
        cfg["count"] = total_count

    # Wallet-pool refill amounts: YAML stores them in wei as Python ints
    # (the export tool deliberately keeps the precise wei value). Surface
    # under the *_wei keys consumed by spamoor_wallet_pool.
    refill_amount = yaml_cfg.get("refill_amount")
    if isinstance(refill_amount, int) and refill_amount > 0:
        cfg["refill_amount_wei"] = refill_amount
    refill_balance = yaml_cfg.get("refill_balance")
    if isinstance(refill_balance, int) and refill_balance > 0:
        cfg["refill_balance_wei"] = refill_balance

    cfg["yaml_scenario"] = scenario_entry


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register ``--spamoor-*`` CLI options under the spamoor group."""
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
        help="Hex seed for evm-fuzz bytecode generator "
        "(empty = deterministic default)",
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
        help="storagerefundtx: slots written+cleared per execute() call",
    )
    group.addoption(
        "--spamoor-bytecodes",
        dest="spamoor_bytecodes",
        type=str,
        default="",
        help="deploytx: comma-separated hex bytecodes to cycle through",
    )
    group.addoption(
        "--spamoor-bytecodes-file",
        dest="spamoor_bytecodes_file",
        type=str,
        default="",
        help="deploytx: path to file with one hex bytecode per line",
    )
    group.addoption(
        "--spamoor-config-file",
        dest="spamoor_config_file",
        type=str,
        default="",
        help=(
            "Path to a spammer-export YAML. When set, the scenario at "
            "--spamoor-scenario-index overlays tx-shape options "
            "(contract_address, fees, gas_limit, ...) onto the fixture."
        ),
    )
    group.addoption(
        "--spamoor-max-count",
        dest="spamoor_max_count",
        type=int,
        default=None,
        help=(
            "Cap for the effective tx count. When set, overrides YAML "
            "``total_count`` and any lower-priority source. Intended for "
            "local runs against spammer exports whose ``total_count`` "
            "values are production-scale."
        ),
    )
    group.addoption(
        "--spamoor-skip-assert",
        dest="spamoor_skip_assert",
        action="store_true",
        default=False,
        help=(
            "Submit-only mode: build and broadcast every tx, but do not "
            "fail the test if some txs never mine or if a block commit "
            "call errors. Intended for bloat-style load runs where the "
            "goal is to hammer the client, not to assert receipts."
        ),
    )
    group.addoption(
        "--spamoor-strict",
        dest="spamoor_strict",
        action="store_true",
        default=False,
        help=(
            "Fail the run when the selected YAML scenario uses keys the "
            "EST overlay does not support. Empty/zero values always "
            "produce a warning only."
        ),
    )
    group.addoption(
        "--spamoor-scenario-index",
        dest="spamoor_scenario_index",
        type=int,
        default=0,
        help="0-indexed scenario entry to load from --spamoor-config-file.",
    )
    group.addoption(
        "--spamoor-max-wallets",
        dest="spamoor_max_wallets",
        type=int,
        default=0,
        help=(
            "Number of HD-derived child wallets to spread tx load across. "
            "0 (default) auto-derives clamp(total_count / 50, 10, 1000) "
            "to match upstream spamoor."
        ),
    )
    group.addoption(
        "--spamoor-max-pending",
        dest="spamoor_max_pending",
        type=int,
        default=0,
        help=(
            "Maximum in-flight (submitted-but-not-confirmed) transactions. "
            "0 (default) auto-derives clamp(throughput * 10, 100, 4000)."
        ),
    )
    group.addoption(
        "--spamoor-rebroadcast",
        dest="spamoor_rebroadcast",
        type=int,
        default=1,
        help=(
            "Slots without a receipt before re-broadcasting a stuck tx "
            "(0 disables rebroadcast)."
        ),
    )
    group.addoption(
        "--spamoor-refill-amount",
        dest="spamoor_refill_amount",
        type=int,
        default=0,
        help=(
            "Wei sent from the root wallet to each child during pool "
            "preparation (0 falls back to the spamoor default 5e18)."
        ),
    )
    group.addoption(
        "--spamoor-refill-balance",
        dest="spamoor_refill_balance",
        type=int,
        default=0,
        help=(
            "Minimum wei balance each child must reach during pool "
            "preparation (0 falls back to the spamoor default 1e18)."
        ),
    )
    group.addoption(
        "--spamoor-wallet-seed",
        dest="spamoor_wallet_seed",
        type=str,
        default="",
        help=(
            "Seed string mixed into HD wallet derivation. Blank picks the "
            "value from the YAML scenario or empty string."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register the ``spamoor`` pytest marker."""
    config.addinivalue_line(
        "markers", "spamoor: Run spamoor load generation tests"
    )


@pytest.fixture(scope="session")
def spamoor_config(request: pytest.FixtureRequest) -> Dict[str, Any]:
    """Collect all ``--spamoor-*`` options into a config dict."""
    cfg: Dict[str, Any] = {
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
        "min_swap_amount": request.config.getoption("spamoor_min_swap_amount"),
        "max_swap_amount": request.config.getoption("spamoor_max_swap_amount"),
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
        "skip_assert": bool(
            request.config.getoption("spamoor_skip_assert")
        ),
        # Wallet-pool / submitter knobs. Defaults of 0 mean "auto-derive
        # from total_count / throughput at fixture-build time", matching
        # upstream spamoor (txscenario.go:140-313).
        "max_wallets": int(
            request.config.getoption("spamoor_max_wallets")
        ),
        "max_pending": int(
            request.config.getoption("spamoor_max_pending")
        ),
        "rebroadcast": int(
            request.config.getoption("spamoor_rebroadcast")
        ),
        "refill_amount_wei": int(
            request.config.getoption("spamoor_refill_amount")
        ),
        "refill_balance_wei": int(
            request.config.getoption("spamoor_refill_balance")
        ),
        "wallet_seed": str(
            request.config.getoption("spamoor_wallet_seed")
        ),
    }

    config_file = request.config.getoption("spamoor_config_file")
    if config_file:
        index = int(request.config.getoption("spamoor_scenario_index"))
        entry = _load_scenario_from_yaml(config_file, index)
        strict = bool(request.config.getoption("spamoor_strict"))
        # Also honour --bloat-strict when the bloat plugin is loaded.
        if not strict:
            try:
                strict = bool(request.config.getoption("bloat_strict"))
            except (ValueError, KeyError):
                pass
        _validate_yaml_keys(entry, strict=strict)
        _overlay_yaml_on_config(cfg, entry)

    max_count = request.config.getoption("spamoor_max_count")
    if max_count is not None and int(max_count) > 0:
        cap = int(max_count)
        if int(cfg.get("count", 0)) > cap:
            cfg["count"] = cap

    return cfg


@pytest.fixture(scope="session")
def spamoor_rpc_client(
    spamoor_config: Dict[str, Any],
) -> Callable[[str, List[Any]], Any]:
    """Return a minimal JSON-RPC call helper bound to the configured RPC.

    The helper still returns ``None`` on failure to keep the hot path
    non-throwing, but it stashes the most recent error message in
    ``rpc_call.last_error`` so callers (e.g. the submitter's
    AssertionError formatter) can surface why a send failed without
    having to retry.
    """
    endpoint = spamoor_config["endpoint"]

    def rpc_call(method: str, params: List[Any]) -> Optional[Any]:
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": 1,
            }
            resp = requests.post(endpoint, json=payload, timeout=5)
            resp.raise_for_status()
            body = resp.json()
            if "error" in body:
                rpc_call.last_error = (  # type: ignore[attr-defined]
                    f"{method}: {body['error']!r}"
                )
                return None
            rpc_call.last_error = None  # type: ignore[attr-defined]
            return body.get("result")
        except Exception as exc:
            rpc_call.last_error = (  # type: ignore[attr-defined]
                f"{method}: {exc!r}"
            )
            return None

    rpc_call.last_error = None  # type: ignore[attr-defined]
    return rpc_call


def _verbose_rpc(
    endpoint: str, method: str, params: List[Any]
) -> Any:
    """Direct RPC call that surfaces JSON-RPC errors via RuntimeError.

    The session-scoped ``spamoor_rpc_client`` deliberately swallows errors
    so the tx-submission hot path stays single-return; this variant is
    used by setup paths where the error message is more useful than a
    silent ``None``.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }
    resp = requests.post(endpoint, json=payload, timeout=10)
    resp.raise_for_status()
    body = resp.json()
    if "error" in body:
        raise RuntimeError(
            f"RPC {method} returned error: {body['error']!r}"
        )
    return body.get("result")


def resolve_pool_sizing(spamoor_config: Dict[str, Any]) -> Dict[str, int]:
    """
    Auto-derive `max_wallets` / `max_pending` from the config when 0.

    Mirrors txscenario.go:140-313: ``max_wallets =
    clamp(total_count // 50, 10, 1000)``; ``max_pending =
    clamp(throughput * 10, 100, 4000)``. Explicit non-zero values pass
    through untouched.
    """
    from .wallet_pool import default_max_wallets

    total = int(spamoor_config.get("count", 0))
    explicit_w = int(spamoor_config.get("max_wallets", 0))
    if explicit_w > 0:
        max_wallets = explicit_w
    else:
        max_wallets = default_max_wallets(total) if total > 0 else 10

    explicit_p = int(spamoor_config.get("max_pending", 0))
    if explicit_p > 0:
        max_pending = explicit_p
    else:
        throughput = float(spamoor_config.get("throughput", 0) or 0)
        proposed = int(throughput * 10) if throughput > 0 else 100
        max_pending = max(100, min(4000, proposed))

    return {"max_wallets": max_wallets, "max_pending": max_pending}


@pytest.fixture
def spamoor_wallet_pool(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, List[Any]], Any],
) -> Any:
    """
    Build, fund, and yield a :class:`WalletPool` matching the YAML scenario.

    Mirrors upstream spamoor's pool prepare-and-fund step
    (``walletpool.go:560-638``). Skips the test when a private key /
    endpoint is not configured.

    The fixture is function-scoped on purpose. Upstream spamoor refills
    children continuously via the ``refill_interval`` watcher on the
    wallet pool; EST does not yet have an in-workload refill loop, so we
    re-fund deterministically before each test instead. Children whose
    balance is already above the threshold are skipped, so a re-fund is
    a no-op when the previous test left them well-stocked.

    The effective refill amount is the maximum of the YAML's
    ``refill_amount``, the YAML's ``refill_balance`` top-up math, AND
    the workload's expected per-wallet gas reservation (``count /
    max_wallets`` txs × ``gas`` × ``maxFeePerGas`` × 1.5 safety
    factor). This guarantees each child has enough balance to cover
    the txpool reservation imposed by Nethermind, which would otherwise
    reject the second tx with ``InsufficientFunds``.

    The funding batch is sent via ``eth_sendRawTransaction`` from the root
    EOA, signed using the existing tx_convert helper. We block until each
    funding tx is observed in a receipt before yielding so the children
    have spendable balance when the workload starts.
    """
    import time

    from execution_testing.cli.pytest_commands.plugins.testing_build_block.tx_convert import (  # noqa: E501
        spamoor_dict_to_transaction,
    )

    from .wallet_pool import (
        DEFAULT_REFILL_AMOUNT_WEI,
        DEFAULT_REFILL_BALANCE_WEI,
        WalletPool,
    )

    private_key = spamoor_config.get("private_key")
    if not private_key:
        pytest.skip("spamoor private_key not configured")

    chain_hex = spamoor_rpc_client("eth_chainId", [])
    if not isinstance(chain_hex, str):
        pytest.skip("spamoor endpoint unreachable (eth_chainId failed)")
    chain_id = int(chain_hex, 16)

    sizing = resolve_pool_sizing(spamoor_config)
    yaml_refill_amount = (
        int(spamoor_config.get("refill_amount_wei") or 0)
        or DEFAULT_REFILL_AMOUNT_WEI
    )
    yaml_refill_balance = (
        int(spamoor_config.get("refill_balance_wei") or 0)
        or DEFAULT_REFILL_BALANCE_WEI
    )

    # Compute the upper bound of gas reservation each wallet needs. The
    # txpool charges `gas * maxFeePerGas + value` per pending tx; a wallet
    # round-robin'd into receives `count // max_wallets` txs, sometimes one
    # more. Apply a 1.5x safety factor so the wallet survives a partial
    # refund / repeat run that doubles up on a single account.
    count = int(spamoor_config.get("count") or 0)
    max_wallets = sizing["max_wallets"]
    txs_per_wallet = max(1, (count + max_wallets - 1) // max_wallets)
    gas = int(spamoor_config.get("gas_limit") or 0) or 500_000
    basefee = int(spamoor_config.get("basefee") or 1_000_000_000)
    tip = int(spamoor_config.get("tip_fee") or 1_000_000_000)
    # Mirror the ``max(basefee*2, tip*2)`` upper bound that the funding
    # path below sets as ``maxFeePerGas`` — the txpool reserves balance
    # against that cap, not against the current basefee, so a tighter
    # estimate here triggers intermittent ``InsufficientFunds``.
    max_fee_per_gas = max(basefee * 2, tip * 2)
    value = int(spamoor_config.get("amount") or 0)
    expected_per_wallet = int(
        (gas * max_fee_per_gas + value) * txs_per_wallet * 1.5
    )

    refill_amount = max(yaml_refill_amount, expected_per_wallet)
    refill_balance = max(yaml_refill_balance, expected_per_wallet)
    seed = str(spamoor_config.get("wallet_seed") or "")

    pool = WalletPool(
        private_key,
        seed=seed,
        count=sizing["max_wallets"],
        refill_amount_wei=refill_amount,
        refill_balance_wei=refill_balance,
    )

    endpoint = spamoor_config["endpoint"]

    # Sync root nonce — surface the error rather than silently skipping.
    root_addr = str(pool.root_eoa)
    nonce_hex = _verbose_rpc(
        endpoint, "eth_getTransactionCount", [root_addr, "pending"]
    )
    if not isinstance(nonce_hex, str):
        pytest.skip("eth_getTransactionCount(root) failed")
    root_nonce = int(nonce_hex, 16)

    funding = pool.prepare(spamoor_rpc_client)
    if funding:
        # basefee + tip large enough to land quickly on a fresh devnet.
        basefee = int(spamoor_config.get("basefee") or 1_000_000_000)
        tip = int(spamoor_config.get("tip_fee") or 1_000_000_000)
        max_fee = max(basefee * 2, tip * 2)
        tx_hashes: List[str] = []
        send_errors: List[str] = []
        for f in funding:
            tx_dict = {
                "type": 2,
                "to": f.to_address,
                "value": f.value_wei,
                "data": "",
                "gas": 21000,
                "maxFeePerGas": max_fee,
                "maxPriorityFeePerGas": tip,
                "chainId": 1,  # overridden by tx_convert
                "accessList": [],
            }
            tx = spamoor_dict_to_transaction(
                tx_dict,
                pool.root_eoa,
                chain_id,
                nonce_override=root_nonce,
            )
            root_nonce += 1
            raw = tx.rlp().hex()
            if not raw.startswith("0x"):
                raw = "0x" + raw
            try:
                h = _verbose_rpc(endpoint, "eth_sendRawTransaction", [raw])
            except Exception as exc:
                send_errors.append(f"{f.to_address}: {exc}")
                continue
            if isinstance(h, str) and h.startswith("0x"):
                tx_hashes.append(h)
            else:
                send_errors.append(
                    f"{f.to_address}: unexpected response {h!r}"
                )

        if send_errors and not tx_hashes:
            raise RuntimeError(
                "spamoor_wallet_pool: every funding send failed.\n"
                + "\n".join(send_errors)
            )
        if send_errors:
            print(
                "spamoor_wallet_pool: partial funding "
                f"({len(tx_hashes)} ok, {len(send_errors)} failed):\n"
                + "\n".join(send_errors)
            )

        # Wait for funding receipts (max 120 s) so children have balance.
        deadline = time.time() + 120.0
        pending = list(tx_hashes)
        while pending and time.time() < deadline:
            still_pending: List[str] = []
            for h in pending:
                r = spamoor_rpc_client("eth_getTransactionReceipt", [h])
                if r is None:
                    still_pending.append(h)
            pending = still_pending
            if pending:
                time.sleep(1.0)
        if pending:
            pytest.skip(
                f"wallet pool funding incomplete: {len(pending)} of "
                f"{len(tx_hashes)} funding txs unmined after 120 s"
            )

    return pool
