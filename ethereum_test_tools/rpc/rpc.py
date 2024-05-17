"""
JSON-RPC methods and helper functions for EEST consume based hive simulators.
"""

from abc import ABC
from typing import Any, Dict, List, Literal, Optional, Union

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from ethereum_test_tools import Address

BlockNumberType = Union[int, Literal["latest", "earliest", "pending"]]


class BaseRPC(ABC):
    """
    Represents a base RPC class for every RPC call used within EEST based hive simulators.
    """

    def __init__(self, client_ip: str, port: int):
        self.ip = client_ip
        self.url = f"http://{client_ip}:{port}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    def post_request(
        self, method: str, params: List[Any], extra_headers: Optional[Dict] = None
    ) -> Dict:
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
        headers = base_header if extra_headers is None else {**base_header, **extra_headers}

        response = requests.post(self.url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json().get("result")

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

    def __init__(self, client_ip):
        """
        Initializes the EthRPC class with the http port 8545, which requires no authentication.
        """
        super().__init__(client_ip, port=8545)

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
