"""Transaction builders for the spamoor scenario unit tests."""

import hashlib
import json
import time
from typing import Any, Callable, Dict, List, Optional, cast

try:
    from eth_abi import encode as eth_abi_encode
    from eth_utils import keccak
except ImportError:
    eth_abi_encode = cast(Any, None)
    keccak = cast(Any, None)


# --- Broadcast helpers shared by the spamoor tests ---------------------------


def _normalize_fees(tx_dict: Dict[str, Any]) -> None:
    """
    Clamp ``maxFeePerGas`` to satisfy EIP-1559 validity.

    Builders scale basefee by throughput to pick ``maxFeePerGas``, which
    can fall below ``maxPriorityFeePerGas`` on low-basefee devnets. Raise
    ``maxFeePerGas`` so the tx is accepted by the node.
    """
    if tx_dict.get("type") not in (2, 3):
        return
    max_fee = int(tx_dict.get("maxFeePerGas", 0))
    priority = int(tx_dict.get("maxPriorityFeePerGas", 0))
    if max_fee < priority * 2:
        tx_dict["maxFeePerGas"] = priority * 2


def spamoor_signer_context(
    spamoor_config: Dict[str, Any],
    rpc_client: Optional[Callable[[str, List[Any]], Any]],
) -> Dict[str, Any]:
    """
    Skip-or-return signing context for a spamoor broadcast test.

    Calls ``pytest.skip`` when the private key / sender / endpoint are
    unavailable. Otherwise returns ``{signer, chain_id, start_nonce}``.
    """
    import pytest
    from execution_testing.test_types import EOA

    private_key = spamoor_config.get("private_key")
    from_addr = spamoor_config.get("from_addr")
    if not private_key or not from_addr:
        pytest.skip("spamoor private_key/from_addr not configured")
    if rpc_client is None:
        pytest.skip("spamoor rpc_client not configured")

    chain_id_hex = rpc_client("eth_chainId", [])
    if not isinstance(chain_id_hex, str):
        pytest.skip("spamoor endpoint unreachable (eth_chainId failed)")
    nonce_hex = rpc_client("eth_getTransactionCount", [from_addr, "pending"])
    assert isinstance(nonce_hex, str), "eth_getTransactionCount failed"

    start_nonce = int(nonce_hex, 16)
    return {
        "signer": EOA(key=private_key, nonce=start_nonce),
        "chain_id": int(chain_id_hex, 16),
        "start_nonce": start_nonce,
    }


def broadcast_and_assert_receipts(
    raw_txs: List[Dict[str, Any]],
    ctx: Dict[str, Any],
    rpc_client: Callable[[str, List[Any]], Any],
    *,
    fork: Optional[Any] = None,
    blob_seed: int = 0,
    timeout: float = 60.0,
    poll_interval: float = 1.0,
    allow_reverts: bool = False,
    batch_size: int = 256,
    skip_assert: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """
    Sign every raw tx, broadcast, poll receipts, assert ``status == 0x1``.

    When ``batch_size`` is positive and smaller than the full set, txs are
    submitted in chunks and each chunk is drained (all receipts received)
    before the next chunk is submitted. This keeps the per-account txpool
    from overflowing on large runs.

    Submit-only mode (``skip_assert=True``): every tx is still built and
    submitted, but the "all receipts observed" and "status == 0x1" checks
    are relaxed. Intended for bloat-style load generation where dropped
    or pending receipts are expected.

    Returns the receipts keyed by tx hash. Skips the test if the builder
    produced no txs. Type-3 (blob) transactions cannot be broadcast via
    ``eth_sendRawTransaction`` with EST's block-form RLP (no sidecars),
    so the helper skips when it encounters one.
    """
    import pytest
    from execution_testing.cli.pytest_commands.plugins.testing_build_block.tx_convert import (  # noqa: E501
        spamoor_dict_to_transaction,
    )

    if not raw_txs:
        pytest.skip("builder produced no transactions")
    if any(int(tx.get("type", 0)) == 3 for tx in raw_txs):
        pytest.skip(
            "type-3 blob broadcast requires network-form RLP with sidecars; "
            "not implemented for spamoor smoke tests"
        )

    signer = ctx["signer"]
    chain_id = ctx["chain_id"]
    start_nonce = int(ctx["start_nonce"])

    total = len(raw_txs)
    chunk = batch_size if batch_size and batch_size > 0 else total
    receipts: Dict[str, Dict[str, Any]] = {}

    for batch_start in range(0, total, chunk):
        batch = raw_txs[batch_start : batch_start + chunk]
        tx_hashes: List[str] = []
        for offset, tx_dict in enumerate(batch):
            i = batch_start + offset
            _normalize_fees(tx_dict)
            tx = spamoor_dict_to_transaction(
                tx_dict,
                signer,
                chain_id,
                nonce_override=start_nonce + i,
                fork=fork,
                blob_seed=blob_seed,
            )
            raw = tx.rlp().hex()
            result = rpc_client("eth_sendRawTransaction", [raw])
            assert isinstance(result, str) and result.startswith("0x"), (
                f"eth_sendRawTransaction failed for tx {i} "
                f"(type={tx_dict.get('type')} to={tx_dict.get('to')!r} "
                f"gas={tx_dict.get('gas')} "
                f"maxFee={tx_dict.get('maxFeePerGas')} "
                f"tip={tx_dict.get('maxPriorityFeePerGas')} "
                f"nonce={start_nonce + i} "
                f"data_len={len(tx_dict.get('data', '') or '') // 2}): "
                f"{result!r}"
            )
            tx_hashes.append(result)

        deadline = time.time() + timeout
        pending = list(tx_hashes)
        while pending and time.time() < deadline:
            still_pending: List[str] = []
            for h in pending:
                receipt = rpc_client("eth_getTransactionReceipt", [h])
                if receipt is None:
                    still_pending.append(h)
                else:
                    receipts[h] = receipt
            pending = still_pending
            if pending:
                time.sleep(poll_interval)

        if pending and not skip_assert:
            assert not pending, (
                f"batch {batch_start}..{batch_start + len(batch)} never "
                f"mined within {timeout}s: {pending}"
            )

    if not allow_reverts and not skip_assert:
        for h, r in receipts.items():
            status = r.get("status")
            assert status == "0x1", (
                f"tx {h} reverted: status={status} receipt={r}"
            )
    return receipts


def build_eoatx_transactions(
    count: int,
    throughput: float,
    amount: int = 0,
    basefee: Optional[int] = None,
    from_addr: Optional[str] = None,
    private_key: Optional[str] = None,
    rpc_client: Optional[Callable[[str, List[Any]], Any]] = None,
) -> List[Dict[str, Any]]:
    """Build ``count`` EOA-to-EOA type-2 transfer transactions."""
    if count <= 0:
        return []

    nonce = None
    if from_addr and rpc_client:
        resp = rpc_client("eth_getTransactionCount", [from_addr, "pending"])
        if isinstance(resp, str) and resp.startswith("0x"):
            nonce = int(resp, 16)

    base_fee_per_gas = basefee
    if base_fee_per_gas is None and rpc_client:
        bf_resp = rpc_client("eth_feeHistory", ["0x1", "latest", []])
        if bf_resp and "baseFeePerGas" in bf_resp and bf_resp["baseFeePerGas"]:
            try:
                base_fee_per_gas = int(bf_resp["baseFeePerGas"][-1], 16)
            except ValueError:
                pass

    if base_fee_per_gas is None:
        base_fee_per_gas = 1_000_000_000

    max_fee_per_gas = int(base_fee_per_gas * (1.0 + throughput))
    max_priority_fee_per_gas = 1_000_000_000

    to_addr = "0x0000000000000000000000000000000000000000"
    txs = []
    for i in range(count):
        tx = {
            "type": 2,
            "to": to_addr,
            "value": amount,
            "data": "",
            "gas": 21000,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "chainId": 1,
            "accessList": [],
        }
        if nonce is not None:
            tx["nonce"] = nonce + i
        txs.append(tx)
    return txs


def build_calltx_transactions(
    count: int,
    throughput: float,
    amount: int = 0,
    basefee: Optional[int] = None,
    from_addr: Optional[str] = None,
    private_key: Optional[str] = None,
    contract_code: Optional[str] = None,
    contract_address: Optional[str] = None,
    call_data: str = "",
    call_fn_sig: str = "",
    call_args: str = "[]",
    contract_args: str = "[]",
    gas_limit: int = 0,
    tip_fee: int = 1_000_000_000,
    deploy_gas_limit: int = 2000000,
    rpc_client: Optional[Callable] = None,
) -> List[Dict[str, Any]]:
    """
    Build a list of calltx-like transactions.

    If contract_code is provided, first include a deployment transaction
    (type=2, to="", value=0, data=contract_code, gas=deploy_gas_limit).
    Then append ``count`` execution transactions targeting
    ``contract_address`` (or a placeholder) with the supplied call_data.
    Nonce handling mirrors build_eoatx_transactions: fetch once if
    ``from_addr`` and ``rpc_client`` are provided, then increment per tx.
    """
    if count <= 0:
        return []

    nonce = None
    if from_addr and rpc_client:
        resp = rpc_client("eth_getTransactionCount", [from_addr, "pending"])
        if isinstance(resp, str) and resp.startswith("0x"):
            nonce = int(resp, 16)

    base_fee_per_gas = basefee
    if base_fee_per_gas is None and rpc_client:
        bf_resp = rpc_client("eth_feeHistory", ["0x1", "latest", []])
        if bf_resp and "baseFeePerGas" in bf_resp and bf_resp["baseFeePerGas"]:
            try:
                base_fee_per_gas = int(bf_resp["baseFeePerGas"][-1], 16)
            except ValueError:
                pass

    if base_fee_per_gas is None:
        base_fee_per_gas = 1_000_000_000

    max_fee_per_gas = int(base_fee_per_gas * (1.0 + throughput))

    # Treat empty strings from YAML config as "unset".
    if isinstance(contract_code, str) and contract_code == "":
        contract_code = None
    if isinstance(contract_address, str) and contract_address == "":
        contract_address = None

    txs: List[Dict[str, Any]] = []

    # ABI-encode call_data when not provided but a function signature is given
    parsed_call_data = call_data
    if (
        not parsed_call_data
        and call_fn_sig
        and eth_abi_encode is not None
        and keccak is not None
    ):
        import re

        sig_match = re.match(r"^[^\(]+\((.*)\)$", call_fn_sig)
        if sig_match:
            types_str = sig_match.group(1)
            types = types_str.split(",") if types_str else []
            try:
                args = json.loads(call_args)
                encoded_args = eth_abi_encode(types, args)
                selector = keccak(text=call_fn_sig)[:4]
                parsed_call_data = "0x" + selector.hex() + encoded_args.hex()
            except Exception:
                pass

    # Deployment transaction if contract code provided
    if contract_code is not None:
        dep_tx: Dict[str, Any] = {
            "type": 2,
            "to": "",
            "value": 0,
            "data": contract_code,
            "gas": deploy_gas_limit,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": tip_fee,
            "chainId": 1,
            "accessList": [],
        }
        if nonce is not None:
            dep_tx["nonce"] = nonce
            nonce += 1  # increment after using nonce for deployment
        txs.append(dep_tx)
        # Constructor ABI encoding for contract_args is a potential
        # follow-up; for now we only support raw ``contract_code`` and
        # leave the field untouched when ``contract_args`` is set.
        _ = (contract_args, eth_abi_encode)

    # Execution transactions
    target_to = (
        contract_address
        if contract_address is not None
        else "0x1111111111111111111111111111111111111111"
    )
    # Determine gas to use for execution transactions (default 500000)
    execution_gas = gas_limit if gas_limit and gas_limit > 0 else 500000

    for _i in range(count):
        tx: Dict[str, Any] = {
            "type": 2,
            "to": target_to,
            "value": amount,
            "data": parsed_call_data,
            "gas": execution_gas,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": tip_fee,
            "chainId": 1,
            "accessList": [],
        }
        if nonce is not None:
            tx["nonce"] = nonce
            nonce += 1
        txs.append(tx)

    return txs


def build_blob_combined_transactions(
    count: int,
    sidecars: int = 3,
    basefee: Optional[int] = None,
    tip_fee: int = 1_000_000_000,
    blob_fee: int = 20_000_000_000,
    from_addr: Optional[str] = None,
    private_key: Optional[str] = None,
    rpc_client: Optional[Callable[[str, List[Any]], Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Build EIP-4844 blob transactions mirroring spamoor blob-combined.

    Produces `count` type-3 transactions, each carrying `sidecars`
    placeholder versioned hashes. Blob sidecar data is left to the
    caller for the committed-path conversion.
    """
    if count <= 0:
        return []

    nonce = None
    if from_addr and rpc_client:
        resp = rpc_client("eth_getTransactionCount", [from_addr, "pending"])
        if isinstance(resp, str) and resp.startswith("0x"):
            nonce = int(resp, 16)

    base_fee_per_gas = basefee
    if base_fee_per_gas is None and rpc_client:
        bf_resp = rpc_client("eth_feeHistory", ["0x1", "latest", []])
        if bf_resp and "baseFeePerGas" in bf_resp and bf_resp["baseFeePerGas"]:
            try:
                base_fee_per_gas = int(bf_resp["baseFeePerGas"][-1], 16)
            except ValueError:
                pass
    if base_fee_per_gas is None:
        base_fee_per_gas = 20_000_000_000

    max_fee_per_gas = base_fee_per_gas + tip_fee

    blob_count = max(1, min(int(sidecars), 6))
    to_addr = "0x1000000000000000000000000000000000000000"
    txs: List[Dict[str, Any]] = []
    for i in range(count):
        versioned_hashes = [
            "0x01" + f"{(i * 100 + j):062x}" for j in range(blob_count)
        ]
        tx: Dict[str, Any] = {
            "type": 3,
            "to": to_addr,
            "value": 0,
            "data": "",
            "gas": 21000,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": tip_fee,
            "maxFeePerBlobGas": blob_fee,
            "blobVersionedHashes": versioned_hashes,
            "blobCount": blob_count,
            "chainId": 1,
            "accessList": [],
        }
        if nonce is not None:
            tx["nonce"] = nonce + i
        txs.append(tx)
    return txs


_FACTORY_BYTECODE = "0x608060405234801561001057600080fd5b50610365806100206000396000f3fe6080604052600436106100295760003560e01c806310a935281461002e578063cdcb760a14610064575b600080fd5b34801561003a57600080fd5b5061004e6100493660046101db565b610077565b60405161005b91906102d7565b60405180910390f35b61004e6100723660046101fc565b6100ee565b6040516000906100b1907fff0000000000000000000000000000000000000000000000000000000000000090309086908690602001610273565b604080517fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe081840301815291905280516020909101209392505050565b600080600084848080601f01602080910402602001604051908101604052809392919081815260200183838082843760009201919091525050825192935088929150506020830134f5915073ffffffffffffffffffffffffffffffffffffffff821661018f576040517f08c379a0000000000000000000000000000000000000000000000000000000008152600401610186906102f8565b60405180910390fd5b604051869073ffffffffffffffffffffffffffffffffffffffff8416907fb085ff794f342ed78acc7791d067e28a931e614b52476c0305795e1ff0a154bc90600090a350949350505050565b600080604083850312156101ed578182fd5b50508035926020909101359150565b600080600060408486031215610210578081fd5b83359250602084013567ffffffffffffffff8082111561022e578283fd5b818601915086601f830112610241578283fd5b81358181111561024f578384fd5b876020828501011115610260578384fd5b6020830194508093505050509250925092565b7fff0000000000000000000000000000000000000000000000000000000000000094909416845260609290921b7fffffffffffffffffffffffffffffffffffffffff0000000000000000000000001660018401526015830152603582015260550190565b73ffffffffffffffffffffffffffffffffffffffff91909116815260200190565b60208082526011908201527f4465706c6f796d656e74206661696c656400000000000000000000000000000060408201526060019056fea26469706673582212202d3e87dd998c22df28ccb2c934734610461c1e6888114d8003aa51583d65054c64736f6c63430008000033"  # noqa: E501


def build_factorydeploytx_transactions(
    count: int,
    init_code: str,
    start_salt: int = 0,
    factory_address: str = "",
    deploy_gas_limit: int = 2000000,
    gas_limit: int = 500000,
    max_fee_per_gas: int = 20_000_000_000,
    tip_fee: int = 1_000_000_000,
    rpc_client: Optional[Callable] = None,
) -> List[Dict[str, Any]]:
    """
    Build factory deployment + deploy(bytes32,bytes) transactions.

    If factory_address is empty, emit a deployment tx with ``to=""`` and
    ``data`` as the factory bytecode (placeholder if not provided), then
    target the deployed factory (mock address used if the real receipt
    is unavailable). Then emit ``count`` deploy calls to the factory
    with salt and init_code.
    """
    # Use a mock factory address if none provided
    target_address = (
        factory_address
        if factory_address
        else "0x2222222222222222222222222222222222222222"
    )

    txs: List[Dict[str, Any]] = []
    if factory_address == "":
        txs.append(
            {
                "type": 2,
                "to": "",
                "value": 0,
                "data": _FACTORY_BYTECODE,
                "gas": deploy_gas_limit,
                "maxFeePerGas": max_fee_per_gas,
                "maxPriorityFeePerGas": tip_fee,
                "chainId": 1,
                "accessList": [],
            }
        )

    def _to_bytes32(n: int) -> bytes:
        return int(n).to_bytes(32, "big")

    init_code_bytes = bytes.fromhex(
        init_code[2:] if init_code.startswith("0x") else init_code
    )
    for i in range(count):
        salt = start_salt + i
        salt_bytes32 = _to_bytes32(salt)
        call_data = None
        # Try ABI encoding if available
        try:
            if eth_abi_encode is not None:
                encoded = eth_abi_encode(
                    ["bytes32", "bytes"], [salt_bytes32, init_code_bytes]
                )
                call_data = "0x4c8c9ea1" + encoded.hex()
        except Exception:
            call_data = None
        if call_data is None:
            # Manual ABI-like encoding for (bytes32,bytes)
            offset = 64
            length = len(init_code_bytes)
            length32 = length.to_bytes(32, "big")
            offset32 = offset.to_bytes(32, "big")
            pad_len = (32 - (length % 32)) % 32
            padded = init_code_bytes + (b"\x00" * pad_len)
            call_data = (
                "0x"
                + "4c8c9ea1"
                + salt_bytes32.hex()
                + offset32.hex()
                + length32.hex()
                + padded.hex()
            )

        txs.append(
            {
                "type": 2,
                "to": target_address,
                "value": 0,
                "data": call_data,
                "gas": gas_limit,
                "maxFeePerGas": max_fee_per_gas,
                "maxPriorityFeePerGas": tip_fee,
                "chainId": 1,
                "accessList": [],
            }
        )

    return txs


# Minimal gas-burner runtime: loops on JUMPDEST/JUMP until gas runs out.
# Layout: JUMPDEST (0x5b), PUSH1 0x00, JUMP (0x56). Loops back to offset 0.
_GAS_BURNER_RUNTIME = bytes.fromhex("5b600056")
# Init code: copy the runtime into memory and RETURN it.
#   PUSH1 len, PUSH1 runtime_offset, PUSH1 0 (mem), CODECOPY,
#   PUSH1 len, PUSH1 0, RETURN
# With a 4-byte runtime, runtime offset = 12.
_GAS_BURNER_INIT = (
    bytes.fromhex("6004600c60003960046000f3") + _GAS_BURNER_RUNTIME
)
_GAS_BURNER_CONTRACT_HEX = "0x" + _GAS_BURNER_INIT.hex()
_GAS_BURNER_PLACEHOLDER_ADDR = "0x3333333333333333333333333333333333333333"


def build_gasburnertx_transactions(
    count: int,
    gas_units_to_burn: int = 2_000_000,
    basefee: Optional[int] = None,
    tip_fee: int = 1_000_000_000,
    throughput: float = 1.0,
    deploy_gas_limit: int = 2_000_000,
    contract_address: Optional[str] = None,
    from_addr: Optional[str] = None,
    private_key: Optional[str] = None,
    rpc_client: Optional[Callable[[str, List[Any]], Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Build gasburnertx deployment + execution transactions.

    Mirrors the Go scenario: one dynamic-fee deploy tx for the gas-burner
    contract, followed by *count* dynamic-fee execution txs each carrying
    a 4-byte big-endian txIdx payload and a gas limit of
    *gas_units_to_burn*.
    """
    if count <= 0:
        return []

    nonce = None
    if from_addr and rpc_client:
        resp = rpc_client("eth_getTransactionCount", [from_addr, "pending"])
        if isinstance(resp, str) and resp.startswith("0x"):
            nonce = int(resp, 16)

    base_fee_per_gas = basefee
    if base_fee_per_gas is None and rpc_client:
        bf_resp = rpc_client("eth_feeHistory", ["0x1", "latest", []])
        if bf_resp and "baseFeePerGas" in bf_resp and bf_resp["baseFeePerGas"]:
            try:
                base_fee_per_gas = int(bf_resp["baseFeePerGas"][-1], 16)
            except ValueError:
                pass
    if base_fee_per_gas is None:
        base_fee_per_gas = 1_000_000_000

    max_fee_per_gas = int(base_fee_per_gas * (1.0 + throughput))

    txs: List[Dict[str, Any]] = []

    deploy_tx: Dict[str, Any] = {
        "type": 2,
        "to": "",
        "value": 0,
        "data": _GAS_BURNER_CONTRACT_HEX,
        "gas": deploy_gas_limit,
        "maxFeePerGas": max_fee_per_gas,
        "maxPriorityFeePerGas": tip_fee,
        "chainId": 1,
        "accessList": [],
    }
    if nonce is not None:
        deploy_tx["nonce"] = nonce
        nonce += 1
    txs.append(deploy_tx)

    target_addr = contract_address or _GAS_BURNER_PLACEHOLDER_ADDR
    for i in range(count):
        tx_id_bytes = int(i).to_bytes(4, "big")
        exec_tx: Dict[str, Any] = {
            "type": 2,
            "to": target_addr,
            "value": 0,
            "data": "0x" + tx_id_bytes.hex(),
            "gas": gas_units_to_burn,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": tip_fee,
            "chainId": 1,
            "accessList": [],
        }
        if nonce is not None:
            exec_tx["nonce"] = nonce
            nonce += 1
        txs.append(exec_tx)

    return txs


# Uniswap V2 Router02 selectors (first 4 bytes of keccak(signature)).
_SWAP_EXACT_TOKENS_FOR_TOKENS = (
    "38ed1739"  # (uint256,uint256,address[],address,uint256)
)
_SWAP_EXACT_ETH_FOR_TOKENS = (
    "7ff36ab5"  # payable; (uint256,address[],address,uint256)
)
_SWAP_EXACT_TOKENS_FOR_ETH = (
    "18cbafe5"  # (uint256,uint256,address[],address,uint256)
)

_UNISWAP_ROUTER_ADDR = "0x4444444444444444444444444444444444444444"
_UNISWAP_WETH_ADDR = "0x5555555555555555555555555555555555555555"
_UNISWAP_DAI_ADDR = "0x6666666666666666666666666666666666666666"
_UNISWAP_RECIPIENT = "0x7777777777777777777777777777777777777777"


def _encode_uniswap_swap_call(
    variant: int,
    amount_in: int,
    min_out: int,
    path: List[str],
    recipient: str,
    deadline: int,
) -> tuple[str, int]:
    """
    Return (hex call_data, tx_value_wei) for a router swap call.

    variant 0 → swapExactTokensForTokens (value=0)
    variant 1 → swapExactETHForTokens  (value=amount_in, payable)
    variant 2 → swapExactTokensForETH  (value=0)
    """
    assert eth_abi_encode is not None, "eth_abi required for uniswap port"
    path_addrs = [bytes.fromhex(a[2:]).rjust(20, b"\x00") for a in path]
    if variant == 1:
        # swapExactETHForTokens(uint256 amountOutMin, address[] path,
        #   address to, uint256 deadline). amountIn == msg.value.
        encoded = eth_abi_encode(
            ["uint256", "address[]", "address", "uint256"],
            [min_out, path_addrs, bytes.fromhex(recipient[2:]), deadline],
        )
        return "0x" + _SWAP_EXACT_ETH_FOR_TOKENS + encoded.hex(), amount_in

    selector = (
        _SWAP_EXACT_TOKENS_FOR_ETH
        if variant == 2
        else _SWAP_EXACT_TOKENS_FOR_TOKENS
    )
    encoded = eth_abi_encode(
        ["uint256", "uint256", "address[]", "address", "uint256"],
        [
            amount_in,
            min_out,
            path_addrs,
            bytes.fromhex(recipient[2:]),
            deadline,
        ],
    )
    return "0x" + selector + encoded.hex(), 0


def build_uniswap_swaps_transactions(
    count: int,
    pair_count: int = 1,
    min_swap_amount: int = 100_000_000_000_000_000,
    max_swap_amount: int = 1_000_000_000_000_000_000_000,
    buy_ratio: int = 40,
    slippage: int = 50,
    basefee: Optional[int] = None,
    tip_fee: int = 1_000_000_000,
    throughput: float = 1.0,
    gas_limit: int = 200_000,
    recipient: str = _UNISWAP_RECIPIENT,
    router_address: str = _UNISWAP_ROUTER_ADDR,
    weth_address: str = _UNISWAP_WETH_ADDR,
    token_address: str = _UNISWAP_DAI_ADDR,
    from_addr: Optional[str] = None,
    private_key: Optional[str] = None,
    rpc_client: Optional[Callable[[str, List[Any]], Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Build uniswap-swaps execution transactions.

    Deterministic port of the Go scenario's action mix: per tx index we
    alternate between *buy-with-ETH*, *buy-with-WETH*, and *sell-tokens*,
    weighted by ``buy_ratio``. Every tx is a type-2 (EIP-1559) call to
    ``router_address`` with ABI-encoded swap calldata. Swap amounts are
    the midpoint of the ``[min_swap_amount, max_swap_amount]`` range so
    the builder stays deterministic for shape assertions.
    """
    if count <= 0:
        return []
    if eth_abi_encode is None:
        raise RuntimeError("eth_abi is required for uniswap-swaps port")

    nonce = None
    if from_addr and rpc_client:
        resp = rpc_client("eth_getTransactionCount", [from_addr, "pending"])
        if isinstance(resp, str) and resp.startswith("0x"):
            nonce = int(resp, 16)

    base_fee_per_gas = basefee
    if base_fee_per_gas is None and rpc_client:
        bf_resp = rpc_client("eth_feeHistory", ["0x1", "latest", []])
        if bf_resp and "baseFeePerGas" in bf_resp and bf_resp["baseFeePerGas"]:
            try:
                base_fee_per_gas = int(bf_resp["baseFeePerGas"][-1], 16)
            except ValueError:
                pass
    if base_fee_per_gas is None:
        base_fee_per_gas = 1_000_000_000
    max_fee_per_gas = int(base_fee_per_gas * (1.0 + throughput))

    swap_amount = (int(min_swap_amount) + int(max_swap_amount)) // 2
    min_out = swap_amount * max(0, 10_000 - int(slippage)) // 10_000
    deadline = 2_000_000_000  # fixed future unix ts; scenario uses now+300.

    # Deterministic buy/sell allocation proportional to buy_ratio so small
    # counts still produce a mix. e.g. count=5, buy_ratio=40 → buys={0,2}
    # (2 buys), sells={1,3,4}. Rounding keeps at least 1 of each when
    # 0 < buy_ratio < 100 and count >= 2.
    buy_count_target = max(0, min(count, (count * int(buy_ratio) + 50) // 100))
    if 0 < int(buy_ratio) < 100 and count >= 2:
        buy_count_target = max(1, min(count - 1, buy_count_target))
    buy_stride = count / buy_count_target if buy_count_target else float("inf")
    buys_issued = 0

    txs: List[Dict[str, Any]] = []
    for i in range(count):
        # Interleave buys by stride so they're spread across the batch.
        want_buy = buys_issued < buy_count_target and i >= int(
            buys_issued * buy_stride
        )
        if want_buy:
            variant = 0 if (buys_issued % 2 == 0) else 1
            path = [weth_address, token_address]
            buys_issued += 1
        else:
            variant = 2
            path = [token_address, weth_address]

        call_data, value = _encode_uniswap_swap_call(
            variant,
            amount_in=swap_amount,
            min_out=min_out,
            path=path,
            recipient=recipient,
            deadline=deadline,
        )

        tx: Dict[str, Any] = {
            "type": 2,
            "to": router_address,
            "value": value,
            "data": call_data,
            "gas": gas_limit,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": tip_fee,
            "chainId": 1,
            "accessList": [],
        }
        if nonce is not None:
            tx["nonce"] = nonce + i
        txs.append(tx)

    _ = pair_count  # reserved for future multi-pair encoding
    return txs


def _evm_fuzz_bytecode(
    tx_id: int, seed_hex: str, min_size: int, max_size: int, mode: str
) -> bytes:
    """
    Deterministically derive fuzz bytecode for *tx_id*.

    Rather than porting the full Go opcode generator, we expand the
    seed + tx_id + mode through SHA-256 counters until we have enough
    bytes. Resulting bytecodes are almost always invalid EVM init code,
    which matches the scenario's purpose: exercise the EVM and the
    deployment path with random-shaped payloads.
    """
    if max_size < min_size:
        max_size = min_size
    # Seed can be a 0x-hex blob or an arbitrary label (e.g. "evm-fuzz-7"
    # from spamoor YAML exports). Parse as hex when it looks hex-shaped;
    # otherwise hash the raw UTF-8 bytes so every label maps to a stable
    # 32-byte seed.
    if not seed_hex:
        seed_bytes = b""
    else:
        hx = seed_hex[2:] if seed_hex.startswith("0x") else seed_hex
        try:
            seed_bytes = bytes.fromhex(hx)
        except ValueError:
            seed_bytes = hashlib.sha256(seed_hex.encode("utf-8")).digest()
    # Size is deterministic per tx within [min_size, max_size].
    size_span = max_size - min_size + 1
    size = min_size + (
        int.from_bytes(
            hashlib.sha256(
                seed_bytes + tx_id.to_bytes(8, "big") + b"size"
            ).digest()[:4],
            "big",
        )
        % size_span
    )
    mode_byte = {"all": 0, "opcodes": 1, "precompiles": 2}.get(mode, 0)
    out = bytearray()
    counter = 0
    while len(out) < size:
        h = hashlib.sha256(
            seed_bytes
            + tx_id.to_bytes(8, "big")
            + bytes([mode_byte])
            + counter.to_bytes(4, "big")
        ).digest()
        out.extend(h)
        counter += 1
    return bytes(out[:size])


def build_evm_fuzz_transactions(
    count: int,
    gas_limit: int = 0,
    min_code_size: int = 100,
    max_code_size: int = 512,
    payload_seed: str = "",
    tx_id_offset: int = 0,
    fuzz_mode: str = "all",
    basefee: Optional[int] = None,
    tip_fee: int = 1_000_000_000,
    throughput: float = 1.0,
    from_addr: Optional[str] = None,
    private_key: Optional[str] = None,
    rpc_client: Optional[Callable[[str, List[Any]], Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Build evm-fuzz contract creation transactions.

    Each tx is a type-2 contract creation (``to == ""``) carrying
    deterministic pseudo-random bytes as init code. 25% of txs carry
    ``value == 0``; the remainder carry a small random value in the
    ``[0xa000, 0x10000)`` wei range, mirroring the Go scenario's 75/25
    value split.
    """
    if count <= 0:
        return []
    effective_gas = gas_limit if gas_limit and gas_limit > 0 else 1_000_000

    nonce = None
    if from_addr and rpc_client:
        resp = rpc_client("eth_getTransactionCount", [from_addr, "pending"])
        if isinstance(resp, str) and resp.startswith("0x"):
            nonce = int(resp, 16)

    base_fee_per_gas = basefee
    if base_fee_per_gas is None and rpc_client:
        bf_resp = rpc_client("eth_feeHistory", ["0x1", "latest", []])
        if bf_resp and "baseFeePerGas" in bf_resp and bf_resp["baseFeePerGas"]:
            try:
                base_fee_per_gas = int(bf_resp["baseFeePerGas"][-1], 16)
            except ValueError:
                pass
    if base_fee_per_gas is None:
        base_fee_per_gas = 1_000_000_000
    max_fee_per_gas = int(base_fee_per_gas * (1.0 + throughput))

    seed = payload_seed or "deadbeef"

    txs: List[Dict[str, Any]] = []
    for i in range(count):
        tx_id = i + int(tx_id_offset)
        code = _evm_fuzz_bytecode(
            tx_id, seed, int(min_code_size), int(max_code_size), fuzz_mode
        )
        # Deterministic 75/25 value split: every 4th tx gets value=0.
        if tx_id % 4 == 0:
            value = 0
        else:
            value_span = 0x6000
            value = 0xA000 + (
                int.from_bytes(
                    hashlib.sha256(
                        seed.encode() + tx_id.to_bytes(8, "big") + b"val"
                    ).digest()[:2],
                    "big",
                )
                % value_span
            )
        tx: Dict[str, Any] = {
            "type": 2,
            "to": "",
            "value": value,
            "data": "0x" + code.hex(),
            "gas": effective_gas,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": tip_fee,
            "chainId": 1,
            "accessList": [],
        }
        if nonce is not None:
            tx["nonce"] = nonce + i
        txs.append(tx)
    return txs


# keccak("transferMint(address,uint256)")[:4]
_TRANSFER_MINT_SELECTOR = "9d0f7cba"
_ERC20_PLACEHOLDER_ADDR = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def _erc20_recipient_for_idx(idx: int) -> str:
    tail = f"{idx:040x}"
    return "0x" + ("cc" * 12) + tail[-16:]


def build_erc20tx_transactions(
    count: int,
    amount: int = 1_000_000_000_000_000_000,
    random_target: bool = False,
    random_amount: bool = False,
    contract_address: Optional[str] = None,
    contract_code: Optional[str] = None,
    deploy_gas_limit: int = 2_000_000,
    gas_limit: int = 100_000,
    basefee: Optional[int] = None,
    tip_fee: int = 1_000_000_000,
    throughput: float = 1.0,
    from_addr: Optional[str] = None,
    private_key: Optional[str] = None,
    rpc_client: Optional[Callable[[str, List[Any]], Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Build erc20tx deployment + transferMint execution transactions.

    If *contract_code* is provided, the first tx deploys it (to="",
    data=code). Then *count* transferMint calls follow, targeting either
    the provided *contract_address* or a fixed placeholder.
    """
    if count <= 0:
        return []

    nonce = None
    if from_addr and rpc_client:
        resp = rpc_client("eth_getTransactionCount", [from_addr, "pending"])
        if isinstance(resp, str) and resp.startswith("0x"):
            nonce = int(resp, 16)

    base_fee_per_gas = basefee
    if base_fee_per_gas is None and rpc_client:
        bf_resp = rpc_client("eth_feeHistory", ["0x1", "latest", []])
        if bf_resp and "baseFeePerGas" in bf_resp and bf_resp["baseFeePerGas"]:
            try:
                base_fee_per_gas = int(bf_resp["baseFeePerGas"][-1], 16)
            except ValueError:
                pass
    if base_fee_per_gas is None:
        base_fee_per_gas = 1_000_000_000
    max_fee_per_gas = int(base_fee_per_gas * (1.0 + throughput))

    txs: List[Dict[str, Any]] = []

    if contract_code is not None:
        deploy_tx: Dict[str, Any] = {
            "type": 2,
            "to": "",
            "value": 0,
            "data": contract_code,
            "gas": deploy_gas_limit,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": tip_fee,
            "chainId": 1,
            "accessList": [],
        }
        if nonce is not None:
            deploy_tx["nonce"] = nonce
            nonce += 1
        txs.append(deploy_tx)

    target_token = contract_address or _ERC20_PLACEHOLDER_ADDR

    for i in range(count):
        if random_target:
            recipient = (
                "0x"
                + hashlib.sha256(b"erc20tx:target:" + i.to_bytes(8, "big"))
                .digest()[:20]
                .hex()
            )
        else:
            recipient = _erc20_recipient_for_idx(i)

        if random_amount:
            transfer_amount = int.from_bytes(
                hashlib.sha256(
                    b"erc20tx:amount:" + i.to_bytes(8, "big")
                ).digest()[:8],
                "big",
            ) % max(int(amount), 1)
        else:
            transfer_amount = int(amount)

        addr_word = bytes.fromhex(recipient[2:]).rjust(32, b"\x00")
        amount_word = transfer_amount.to_bytes(32, "big")
        call_data = (
            "0x"
            + _TRANSFER_MINT_SELECTOR
            + addr_word.hex()
            + amount_word.hex()
        )

        tx: Dict[str, Any] = {
            "type": 2,
            "to": target_token,
            "value": 0,
            "data": call_data,
            "gas": gas_limit,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": tip_fee,
            "chainId": 1,
            "accessList": [],
        }
        if nonce is not None:
            tx["nonce"] = nonce
            nonce += 1
        txs.append(tx)

    return txs


# keccak("setRandomForGas(uint256,uint256)")[:4]
_SET_RANDOM_FOR_GAS_SELECTOR = "fed72935"
_STORAGESPAM_PLACEHOLDER_ADDR = "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def build_storagespam_transactions(
    count: int,
    gas_units_to_burn: int = 2_000_000,
    reuse_contract: bool = False,
    contract_address: Optional[str] = None,
    contract_code: Optional[str] = None,
    deploy_gas_limit: int = 2_000_000,
    basefee: Optional[int] = None,
    tip_fee: int = 1_000_000_000,
    throughput: float = 1.0,
    from_addr: Optional[str] = None,
    private_key: Optional[str] = None,
    rpc_client: Optional[Callable[[str, List[Any]], Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Build storagespam deployment + setRandomForGas execution transactions.

    Unless *reuse_contract* is True, a deployment tx is emitted first with
    *contract_code* (a minimal placeholder when not provided). Each of
    the *count* execution txs calls ``setRandomForGas(gas_units_to_burn,
    txIdx)`` on the deployed (or placeholder) contract. Gas per exec tx
    is ``gas_units_to_burn + 50_000`` to match the Go scenario.
    """
    if count <= 0:
        return []

    nonce = None
    if from_addr and rpc_client:
        resp = rpc_client("eth_getTransactionCount", [from_addr, "pending"])
        if isinstance(resp, str) and resp.startswith("0x"):
            nonce = int(resp, 16)

    base_fee_per_gas = basefee
    if base_fee_per_gas is None and rpc_client:
        bf_resp = rpc_client("eth_feeHistory", ["0x1", "latest", []])
        if bf_resp and "baseFeePerGas" in bf_resp and bf_resp["baseFeePerGas"]:
            try:
                base_fee_per_gas = int(bf_resp["baseFeePerGas"][-1], 16)
            except ValueError:
                pass
    if base_fee_per_gas is None:
        base_fee_per_gas = 1_000_000_000
    max_fee_per_gas = int(base_fee_per_gas * (1.0 + throughput))

    txs: List[Dict[str, Any]] = []

    # Inline minimal init code that returns a tiny runtime (so committed
    # txs targeting the CREATE address still see a contract; the real
    # StorageSpam.sol bytecode isn't bundled here).
    stub_init_hex = "0x6004600c60003960046000f35b600056"

    if not reuse_contract:
        deploy_code = contract_code or stub_init_hex
        deploy_tx: Dict[str, Any] = {
            "type": 2,
            "to": "",
            "value": 0,
            "data": deploy_code,
            "gas": deploy_gas_limit,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": tip_fee,
            "chainId": 1,
            "accessList": [],
        }
        if nonce is not None:
            deploy_tx["nonce"] = nonce
            nonce += 1
        txs.append(deploy_tx)

    target = contract_address or _STORAGESPAM_PLACEHOLDER_ADDR
    exec_gas = int(gas_units_to_burn) + 50_000

    for i in range(count):
        gas_word = int(gas_units_to_burn).to_bytes(32, "big")
        seed_word = int(i).to_bytes(32, "big")
        call_data = (
            "0x"
            + _SET_RANDOM_FOR_GAS_SELECTOR
            + gas_word.hex()
            + seed_word.hex()
        )
        tx: Dict[str, Any] = {
            "type": 2,
            "to": target,
            "value": 0,
            "data": call_data,
            "gas": exec_gas,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": tip_fee,
            "chainId": 1,
            "accessList": [],
        }
        if nonce is not None:
            tx["nonce"] = nonce
            nonce += 1
        txs.append(tx)

    return txs


# keccak("bloatStorage(uint256,uint256)")[:4]
_BLOAT_STORAGE_SELECTOR = "c1926de5"
# Reasonable gas limit for erc20_bloater tx. The Go scenario uses 16.7M
# (EIP-7825 cap). The lab genesis block gas limit is 30M so this fits.
_BLOAT_DEFAULT_GAS = 16_700_000
_BLOAT_PLACEHOLDER_ADDR = "0xdddddddddddddddddddddddddddddddddddddddd"


def build_erc20_bloater_transactions(
    count: int,
    addresses_per_tx: int = 370,
    start_address_index: int = 1,
    gas_limit: int = 0,
    contract_address: Optional[str] = None,
    contract_code: Optional[str] = None,
    deploy_gas_limit: int = 2_000_000,
    basefee: Optional[int] = None,
    tip_fee: int = 1_000_000_000,
    throughput: float = 1.0,
    from_addr: Optional[str] = None,
    private_key: Optional[str] = None,
    rpc_client: Optional[Callable[[str, List[Any]], Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Build erc20_bloater deployment + bloatStorage execution transactions.

    When *contract_code* is provided (or the default placeholder is used)
    the first tx deploys the contract. Each of the *count* execution
    txs calls ``bloatStorage(uint256 startAddressIndex, uint256
    numAddresses)`` with a sliding ``startAddressIndex``, which mirrors
    the Go scenario's sequential sweep of the address space.
    """
    if count <= 0:
        return []

    nonce = None
    if from_addr and rpc_client:
        resp = rpc_client("eth_getTransactionCount", [from_addr, "pending"])
        if isinstance(resp, str) and resp.startswith("0x"):
            nonce = int(resp, 16)

    base_fee_per_gas = basefee
    if base_fee_per_gas is None and rpc_client:
        bf_resp = rpc_client("eth_feeHistory", ["0x1", "latest", []])
        if bf_resp and "baseFeePerGas" in bf_resp and bf_resp["baseFeePerGas"]:
            try:
                base_fee_per_gas = int(bf_resp["baseFeePerGas"][-1], 16)
            except ValueError:
                pass
    if base_fee_per_gas is None:
        base_fee_per_gas = 1_000_000_000
    max_fee_per_gas = int(base_fee_per_gas * (1.0 + throughput))

    exec_gas = gas_limit if gas_limit and gas_limit > 0 else _BLOAT_DEFAULT_GAS

    txs: List[Dict[str, Any]] = []

    # Minimal stub init that returns a tiny runtime. The real ERC20Bloater
    # bytecode lives in the Go contract package; we just need a well-
    # formed deploy tx here.
    stub_init_hex = "0x6004600c60003960046000f35b600056"
    if contract_code is not None or contract_address is None:
        deploy_tx: Dict[str, Any] = {
            "type": 2,
            "to": "",
            "value": 0,
            "data": contract_code or stub_init_hex,
            "gas": deploy_gas_limit,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": tip_fee,
            "chainId": 1,
            "accessList": [],
        }
        if nonce is not None:
            deploy_tx["nonce"] = nonce
            nonce += 1
        txs.append(deploy_tx)

    target = contract_address or _BLOAT_PLACEHOLDER_ADDR
    idx = int(start_address_index)
    step = max(1, int(addresses_per_tx))

    for _ in range(count):
        start_word = idx.to_bytes(32, "big")
        num_word = step.to_bytes(32, "big")
        call_data = (
            "0x" + _BLOAT_STORAGE_SELECTOR + start_word.hex() + num_word.hex()
        )
        tx: Dict[str, Any] = {
            "type": 2,
            "to": target,
            "value": 0,
            "data": call_data,
            "gas": exec_gas,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": tip_fee,
            "chainId": 1,
            "accessList": [],
        }
        if nonce is not None:
            tx["nonce"] = nonce
            nonce += 1
        txs.append(tx)
        idx += step

    return txs


# keccak("execute(uint256)")[:4]
_STORAGE_REFUND_EXECUTE_SELECTOR = "fe0d94c1"
_STORAGE_REFUND_PLACEHOLDER_ADDR = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
# When the caller does not pin a gas limit, the Go scenario picks a
# value that comfortably fits SlotsPerCall SSTORE+clear cycles. 3M is
# large enough for SlotsPerCall<=500 in practice and small enough to
# fit many per block under the 30M lab cap.
_STORAGE_REFUND_DEFAULT_GAS = 3_000_000


def build_storagerefundtx_transactions(
    count: int,
    slots_per_call: int = 500,
    gas_limit: int = 0,
    contract_address: Optional[str] = None,
    contract_code: Optional[str] = None,
    deploy_gas_limit: int = 2_000_000,
    basefee: Optional[int] = None,
    tip_fee: int = 1_000_000_000,
    throughput: float = 1.0,
    from_addr: Optional[str] = None,
    private_key: Optional[str] = None,
    rpc_client: Optional[Callable[[str, List[Any]], Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Build storagerefundtx deployment + execute(uint256) calls.

    Unless *contract_address* is supplied, the first tx deploys a stub
    (or user-provided *contract_code*) so the batch is self-contained.
    Each of the *count* execution txs calls
    ``execute(slots_per_call)`` on the deployed (or supplied) contract.
    """
    if count <= 0:
        return []

    nonce = None
    if from_addr and rpc_client:
        resp = rpc_client("eth_getTransactionCount", [from_addr, "pending"])
        if isinstance(resp, str) and resp.startswith("0x"):
            nonce = int(resp, 16)

    base_fee_per_gas = basefee
    if base_fee_per_gas is None and rpc_client:
        bf_resp = rpc_client("eth_feeHistory", ["0x1", "latest", []])
        if bf_resp and "baseFeePerGas" in bf_resp and bf_resp["baseFeePerGas"]:
            try:
                base_fee_per_gas = int(bf_resp["baseFeePerGas"][-1], 16)
            except ValueError:
                pass
    if base_fee_per_gas is None:
        base_fee_per_gas = 1_000_000_000
    max_fee_per_gas = int(base_fee_per_gas * (1.0 + throughput))

    exec_gas = (
        gas_limit
        if gas_limit and gas_limit > 0
        else _STORAGE_REFUND_DEFAULT_GAS
    )

    txs: List[Dict[str, Any]] = []

    stub_init_hex = "0x6004600c60003960046000f35b600056"
    if contract_address is None:
        deploy_tx: Dict[str, Any] = {
            "type": 2,
            "to": "",
            "value": 0,
            "data": contract_code or stub_init_hex,
            "gas": deploy_gas_limit,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": tip_fee,
            "chainId": 1,
            "accessList": [],
        }
        if nonce is not None:
            deploy_tx["nonce"] = nonce
            nonce += 1
        txs.append(deploy_tx)

    target = contract_address or _STORAGE_REFUND_PLACEHOLDER_ADDR
    slots_word = int(slots_per_call).to_bytes(32, "big")
    call_data = "0x" + _STORAGE_REFUND_EXECUTE_SELECTOR + slots_word.hex()

    for _ in range(count):
        tx: Dict[str, Any] = {
            "type": 2,
            "to": target,
            "value": 0,
            "data": call_data,
            "gas": exec_gas,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": tip_fee,
            "chainId": 1,
            "accessList": [],
        }
        if nonce is not None:
            tx["nonce"] = nonce
            nonce += 1
        txs.append(tx)

    return txs


# Default bytecode: PUSH1 0x01 / PUSH1 0x00 / SSTORE / STOP — writes one
# slot on deploy; leaves empty runtime (so "runtime" is zero bytes).
_DEPLOYTX_DEFAULT_BYTECODE = "0x6001600055"


def _parse_deploytx_bytecodes(
    bytecodes: str, bytecodes_file: str
) -> List[str]:
    """Return the list of hex bytecodes (with ``0x`` prefix) to cycle."""
    out: List[str] = []
    if bytecodes:
        for chunk in bytecodes.split(","):
            chunk = chunk.strip()
            if not chunk:
                continue
            if not chunk.startswith("0x"):
                chunk = "0x" + chunk
            out.append(chunk)
    if bytecodes_file:
        try:
            with open(bytecodes_file, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if not line.startswith("0x"):
                        line = "0x" + line
                    out.append(line)
        except OSError:
            pass
    if not out:
        out.append(_DEPLOYTX_DEFAULT_BYTECODE)
    return out


def build_deploytx_transactions(
    count: int,
    bytecodes: str = "",
    bytecodes_file: str = "",
    gas_limit: int = 0,
    basefee: Optional[int] = None,
    tip_fee: int = 1_000_000_000,
    throughput: float = 1.0,
    from_addr: Optional[str] = None,
    private_key: Optional[str] = None,
    rpc_client: Optional[Callable[[str, List[Any]], Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Build N deployment transactions cycling through *bytecodes*.

    Mirrors the Go deploytx scenario: every tx is type 2 with
    ``to == ""`` (contract creation); the init code cycles through the
    parsed list of bytecodes (or a tiny default if none supplied).
    """
    if count <= 0:
        return []

    nonce = None
    if from_addr and rpc_client:
        resp = rpc_client("eth_getTransactionCount", [from_addr, "pending"])
        if isinstance(resp, str) and resp.startswith("0x"):
            nonce = int(resp, 16)

    base_fee_per_gas = basefee
    if base_fee_per_gas is None and rpc_client:
        bf_resp = rpc_client("eth_feeHistory", ["0x1", "latest", []])
        if bf_resp and "baseFeePerGas" in bf_resp and bf_resp["baseFeePerGas"]:
            try:
                base_fee_per_gas = int(bf_resp["baseFeePerGas"][-1], 16)
            except ValueError:
                pass
    if base_fee_per_gas is None:
        base_fee_per_gas = 1_000_000_000
    max_fee_per_gas = int(base_fee_per_gas * (1.0 + throughput))

    codes = _parse_deploytx_bytecodes(bytecodes, bytecodes_file)
    exec_gas = gas_limit if gas_limit and gas_limit > 0 else 1_000_000

    txs: List[Dict[str, Any]] = []
    for i in range(count):
        data = codes[i % len(codes)]
        tx: Dict[str, Any] = {
            "type": 2,
            "to": "",
            "value": 0,
            "data": data,
            "gas": exec_gas,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": tip_fee,
            "chainId": 1,
            "accessList": [],
        }
        if nonce is not None:
            tx["nonce"] = nonce + i
        txs.append(tx)
    return txs
