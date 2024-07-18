"""
JSON-RPC methods and helper functions for EEST consume based hive simulators.
"""

import time
from itertools import count
from typing import Any, ClassVar, Dict, List, Literal, Union

import requests
from jwt import encode
from tenacity import retry, stop_after_attempt, wait_exponential

from ethereum_test_base_types import Address, Hash
from ethereum_test_base_types.json import to_json
from ethereum_test_tools.rpc.types import ForkchoiceState, ForkchoiceUpdateResponse, PayloadStatus

BlockNumberType = Union[int, Literal["latest", "earliest", "pending"]]


class BaseRPC:
    """
    Represents a base RPC class for every RPC call used within EEST based hive simulators.
    """

    namespace: ClassVar[str]

    def __init__(self, url: str, extra_headers: Dict = {}):
        """
        Initializes the BaseRPC class with the given url.
        """
        self.url = url
        self.request_id_counter = count(1)
        self.extra_headers = extra_headers

    def __init_subclass__(cls) -> None:
        """
        Sets the namespace of the RPC class to the lowercase of the class name.
        """
        namespace = cls.__name__
        if namespace.endswith("RPC"):
            namespace = namespace[:-3]
        cls.namespace = namespace.lower()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    def post_request(self, method: str, *params: Any, extra_headers: Dict = {}) -> Any:
        """
        Sends a JSON-RPC POST request to the client RPC server at port defined in the url.
        """
        assert self.namespace, "RPC namespace not set"

        payload = {
            "jsonrpc": "2.0",
            "method": f"{self.namespace}_{method}",
            "params": params,
            "id": next(self.request_id_counter),
        }
        base_header = {
            "Content-Type": "application/json",
        }
        headers = base_header | self.extra_headers | extra_headers

        response = requests.post(self.url, json=payload, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        assert "result" in response_json, "RPC response didn't contain a result field"
        result = response_json["result"]

        if result is None or "error" in result:
            error_info = "result is None; and therefore contains no error info"
            error_code = None
            if result is not None:
                error_info = result["error"]
                error_code = result["error"]["code"]
            raise Exception(
                f"Error calling JSON RPC {method}, code: {error_code}, " f"message: {error_info}"
            )

        return result


class EthRPC(BaseRPC):
    """
    Represents an `eth_X` RPC class for every default ethereum RPC method used within EEST based
    hive simulators.
    """

    def __init__(self, ip: str, *, port: int = 8545, extra_headers: Dict = {}):
        """
        Initializes the EthRPC class with the http port 8545, which requires no authentication.
        """
        super().__init__(f"http://{ip}:{port}", extra_headers=extra_headers)

    BlockNumberType = Union[int, Literal["latest", "earliest", "pending"]]

    def get_block_by_number(self, block_number: BlockNumberType = "latest", full_txs: bool = True):
        """
        `eth_getBlockByNumber`: Returns information about a block by block number.
        """
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return self.post_request("getBlockByNumber", block, full_txs)

    def get_balance(self, address: Address, block_number: BlockNumberType = "latest") -> int:
        """
        `eth_getBalance`: Returns the balance of the account of given address.
        """
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return int(self.post_request("getBalance", f"{address}", block), 16)

    def get_transaction_count(
        self, address: Address, block_number: BlockNumberType = "latest"
    ) -> int:
        """
        `eth_getTransactionCount`: Returns the number of transactions sent from an address.
        """
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return int(self.post_request("getTransactionCount", f"{address}", block), 16)

    def get_transaction_by_hash(self, transaction_hash: str):
        """
        `eth_getTransactionByHash`: Returns transaction details.
        """
        return self.post_request("getTransactionByHash", f"{transaction_hash}")

    def get_storage_at(
        self, address: Address, position: Hash, block_number: BlockNumberType = "latest"
    ):
        """
        `eth_getStorageAt`: Returns the value from a storage position at a given address.
        """
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return self.post_request("getStorageAt", f"{address}", f"{position}", block)

    def storage_at_keys(
        self, account: Address, keys: List[Hash], block_number: BlockNumberType = "latest"
    ) -> Dict:
        """
        Helper to retrieve the storage values for the specified keys at a given address and block
        number.
        """
        results: Dict = {}
        for key in keys:
            storage_value = self.get_storage_at(account, key, block_number)
            results[key] = storage_value
        return results


class DebugRPC(EthRPC):
    """
    Represents an `debug_X` RPC class for every default ethereum RPC method used within EEST based
    hive simulators.
    """

    def trace_call(self, tr: dict[str, str], block_number: str):
        """
        `debug_traceCall`: Returns pre state required for transaction
        """
        return self.post_request("traceCall", tr, block_number, {"tracer": "prestateTracer"})


class EngineRPC(BaseRPC):
    """
    Represents an Engine API RPC class for every Engine API method used within EEST based hive
    simulators.
    """

    def __init__(self, ip: str, *, port: int = 8551, extra_headers: Dict = {}):
        """
        Initializes the EngineRPC class with the http port 8551.
        """
        super().__init__(f"http://{ip}:{port}", extra_headers=extra_headers)

    def post_request(self, method: str, *params: Any, extra_headers: Dict = {}) -> Any:
        """
        Sends a JSON-RPC POST request to the client RPC server at port defined in the url.
        """
        jwt_token = encode(
            {"iat": int(time.time())},
            b"secretsecretsecretsecretsecretse",  # the secret used within clients in hive
            algorithm="HS256",
        )
        extra_headers = {
            "Authorization": f"Bearer {jwt_token}",
        } | extra_headers
        return super().post_request(method, *params, extra_headers=extra_headers)

    def new_payload(self, *params: Any, version: int) -> PayloadStatus:
        """
        `engine_newPayloadVX`: Attempts to execute the given payload on an execution client.
        """
        return PayloadStatus(**self.post_request(f"newPayloadV{version}", *params))

    def forkchoice_updated(
        self,
        forkchoice_state: ForkchoiceState,
        payload_attributes: Dict | None = None,
        *,
        version: int,
    ) -> ForkchoiceUpdateResponse:
        """
        `engine_forkchoiceUpdatedVX`: Updates the forkchoice state of the execution client.
        """
        return ForkchoiceUpdateResponse(
            **self.post_request(
                f"forkchoiceUpdatedV{version}",
                to_json(forkchoice_state),
                payload_attributes,
            )
        )
