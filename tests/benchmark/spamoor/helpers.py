from typing import List, Optional, Callable, Any, Dict
import json

try:
    from eth_abi import encode as eth_abi_encode
    from eth_utils import keccak
except ImportError:
    eth_abi_encode = None
    keccak = None


def build_eoatx_transactions(
    count: int,
    throughput: float,
    amount: int = 0,
    basefee: Optional[int] = None,
    from_addr: Optional[str] = None,
    private_key: Optional[str] = None,
    rpc_client: Optional[Callable[[str, List[Any]], Any]] = None,
) -> List[Dict[str, Any]]:
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
    """Build a list of calltx-like transactions.

    If contract_code is provided, first include a deployment transaction:
      type=2, to="", value=0, data=contract_code, gas=deploy_gas_limit
    Then append `count` execution transactions:
      type=2, to=contract_address or fallback, value=amount, data=call_data, gas=21000
    Nonce handling mirrors build_eoatx_transactions: fetch once if from_addr and
    rpc_client provided, and increment nonce for each subsequent tx when nonce is known.
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
    max_priority_fee_per_gas = 1_000_000_000

    txs: List[Dict[str, Any]] = []

    # ABI-encode call_data when not provided but a function signature is given
    parsed_call_data = call_data
    if not parsed_call_data and call_fn_sig and eth_abi_encode and keccak:
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
        # MVP: prepare for potential contract constructor ABI encoding (no-op if types unavailable)
        parsed_contract_code = contract_code
        if (
            parsed_contract_code
            and contract_args
            and contract_args != "[]"
            and eth_abi_encode
        ):
            # We need the constructor ABI types to properly encode this.
            # But for MVP, if we don't have the types, we can't easily encode it.
            # Spamoor Go code seems to know the types. Let's assume for MVP we only support raw `contract_code` unless types are known.
            # Actually, let's just leave parsed_contract_code as is for now and document it.
            pass

    # Execution transactions
    target_to = (
        contract_address
        if contract_address is not None
        else "0x1111111111111111111111111111111111111111"
    )
    # Determine gas to use for execution transactions (default 500000)
    execution_gas = gas_limit if gas_limit and gas_limit > 0 else 500000

    for i in range(count):
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
    """Build factory deployment + deploy(bytes32,bytes) transactions.

    If factory_address is empty, emit a deployment tx with to: "" and data as
    the factory bytecode (placeholder if not provided), then target the deployed
    factory (mock address used if real receipt is unavailable).
    Then emit `count` deploy calls to the factory with salt and init_code.
    """

    # Use a mock factory address if none provided
    target_address = (
        factory_address
        if factory_address
        else "0x2222222222222222222222222222222222222222"
    )

    FACTORY_BYTECODE = "0x608060405234801561001057600080fd5b50610365806100206000396000f3fe6080604052600436106100295760003560e01c806310a935281461002e578063cdcb760a14610064575b600080fd5b34801561003a57600080fd5b5061004e6100493660046101db565b610077565b60405161005b91906102d7565b60405180910390f35b61004e6100723660046101fc565b6100ee565b6040516000906100b1907fff0000000000000000000000000000000000000000000000000000000000000090309086908690602001610273565b604080517fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe081840301815291905280516020909101209392505050565b600080600084848080601f01602080910402602001604051908101604052809392919081815260200183838082843760009201919091525050825192935088929150506020830134f5915073ffffffffffffffffffffffffffffffffffffffff821661018f576040517f08c379a0000000000000000000000000000000000000000000000000000000008152600401610186906102f8565b60405180910390fd5b604051869073ffffffffffffffffffffffffffffffffffffffff8416907fb085ff794f342ed78acc7791d067e28a931e614b52476c0305795e1ff0a154bc90600090a350949350505050565b600080604083850312156101ed578182fd5b50508035926020909101359150565b600080600060408486031215610210578081fd5b83359250602084013567ffffffffffffffff8082111561022e578283fd5b818601915086601f830112610241578283fd5b81358181111561024f578384fd5b876020828501011115610260578384fd5b6020830194508093505050509250925092565b7fff0000000000000000000000000000000000000000000000000000000000000094909416845260609290921b7fffffffffffffffffffffffffffffffffffffffff0000000000000000000000001660018401526015830152603582015260550190565b73ffffffffffffffffffffffffffffffffffffffff91909116815260200190565b60208082526011908201527f4465706c6f796d656e74206661696c656400000000000000000000000000000060408201526060019056fea26469706673582212202d3e87dd998c22df28ccb2c934734610461c1e6888114d8003aa51583d65054c64736f6c63430008000033"

    txs: List[Dict[str, Any]] = []
    if factory_address == "":
        txs.append(
            {
                "type": 2,
                "to": "",
                "value": 0,
                "data": FACTORY_BYTECODE,
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
