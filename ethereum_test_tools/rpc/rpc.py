"""
JSON-RPC methods and helper functions for EEST consume based hive simulators.
"""

from abc import ABC
from typing import Any, Dict, List, Literal, Optional, Union

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from ethereum_test_base_types import Address

BlockNumberType = Union[int, Literal["latest", "earliest", "pending"]]


class BaseRPC(ABC):
    """
    Represents a base RPC class for every RPC call used within EEST based hive simulators.
    """

    def __init__(self, url: str, extra_headers: Optional[Dict] = None):
        self.url = url
        self.extra_headers = extra_headers

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    def post_request(self, method: str, params: List[Any]) -> Dict:
        """
        Sends a JSON-RPC POST request to the client RPC server at port defined in the url.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }
        base_header = {
            "Content-Type": "application/json",
        }
        headers = (
            base_header if self.extra_headers is None else {**base_header, **self.extra_headers}
        )

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

    def __init__(self, url: str, extra_headers: Optional[Dict] = None):
        """
        Initializes the EthRPC class with the http port 8545, which requires no authentication.
        """
        super().__init__(url, extra_headers=extra_headers)

    BlockNumberType = Union[int, Literal["latest", "earliest", "pending"]]

    def get_block_by_number(self, block_number: BlockNumberType = "latest", full_txs: bool = True):
        """
        `eth_getBlockByNumber`: Returns information about a block by block number.
        """
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return self.post_request("eth_getBlockByNumber", [block, full_txs])

    def get_balance(self, address: str, block_number: BlockNumberType = "latest"):
        """
        `eth_getBalance`: Returns the balance of the account of given address.
        """
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return self.post_request("eth_getBalance", [address, block])

    def get_transaction_count(self, address: Address, block_number: BlockNumberType = "latest"):
        """
        `eth_getTransactionCount`: Returns the number of transactions sent from an address.
        """
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return self.post_request("eth_getTransactionCount", [address, block])

    def get_transaction_by_hash(self, transaction_hash: str):
        """
        `eth_getTransactionByHash`: Returns transaction details.
        """
        return self.post_request("eth_getTransactionByHash", [f"{transaction_hash}"])

    def get_storage_at(
        self, address: str, position: str, block_number: BlockNumberType = "latest"
    ):
        """
        `eth_getStorageAt`: Returns the value from a storage position at a given address.
        """
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return self.post_request("eth_getStorageAt", [address, position, block])

    def storage_at_keys(
        self, account: str, keys: List[str], block_number: BlockNumberType = "latest"
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

    def debug_trace_call(self, tr: dict[str, str], block_number: str):
        """
        `debug_traceCall`: Returns pre state required for transaction
        """
        params = [
            tr,
            block_number,
            {"tracer": "prestateTracer"},
        ]
        return self.post_request("debug_traceCall", params)
