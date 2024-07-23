"""
JSON-RPC methods and helper functions for EEST consume based hive simulators.
"""

import time
from itertools import count
from typing import Any, ClassVar, Dict, List, Literal, Union

import requests
from jwt import encode
from tenacity import retry, stop_after_attempt, wait_exponential

from ethereum_test_base_types import Address, Bytes, Hash, to_json
from ethereum_test_types import Transaction

from .types import (
    ForkchoiceState,
    ForkchoiceUpdateResponse,
    GetPayloadResponse,
    JSONRPCError,
    PayloadAttributes,
    PayloadStatus,
    TransactionByHashResponse,
)

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

        if "error" in response_json:
            exception = JSONRPCError(**response_json["error"])
            raise exception.exception(method)

        assert "result" in response_json, "RPC response didn't contain a result field"
        result = response_json["result"]
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

    def get_code(self, address: Address, block_number: BlockNumberType = "latest") -> Bytes:
        """
        `eth_getCode`: Returns code at a given address.
        """
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return Bytes(self.post_request("getCode", f"{address}", block))

    def get_transaction_count(
        self, address: Address, block_number: BlockNumberType = "latest"
    ) -> int:
        """
        `eth_getTransactionCount`: Returns the number of transactions sent from an address.
        """
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return int(self.post_request("getTransactionCount", f"{address}", block), 16)

    def get_transaction_by_hash(self, transaction_hash: Hash) -> TransactionByHashResponse:
        """
        `eth_getTransactionByHash`: Returns transaction details.
        """
        return TransactionByHashResponse(
            **self.post_request("getTransactionByHash", f"{transaction_hash}")
        )

    def get_storage_at(
        self, address: Address, position: Hash, block_number: BlockNumberType = "latest"
    ) -> Hash:
        """
        `eth_getStorageAt`: Returns the value from a storage position at a given address.
        """
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return Hash(self.post_request("getStorageAt", f"{address}", f"{position}", block))

    def send_transaction(self, transaction: Transaction):
        """
        `eth_sendRawTransaction`: Send a transaction to the client.
        """
        result_hash = Hash(self.post_request("sendRawTransaction", f"0x{transaction.rlp.hex()}"))
        assert result_hash == transaction.hash

    def send_transactions(self, transactions: List[Transaction]):
        """
        Uses `eth_sendRawTransaction` to send a list of transactions to the client.
        """
        for tx in transactions:
            self.send_transaction(tx)

    def storage_at_keys(
        self, account: Address, keys: List[Hash], block_number: BlockNumberType = "latest"
    ) -> Dict[Hash, Hash]:
        """
        Helper to retrieve the storage values for the specified keys at a given address and block
        number.
        """
        results: Dict[Hash, Hash] = {}
        for key in keys:
            storage_value = self.get_storage_at(account, key, block_number)
            results[key] = storage_value
        return results

    def wait_for_transaction(
        self, transaction: Transaction, timeout: int = 60
    ) -> TransactionByHashResponse:
        """
        Uses `eth_getTransactionByHash` to wait until a transaction is included in a block.
        """
        tx_hash = transaction.hash
        for _ in range(timeout):
            tx = self.get_transaction_by_hash(tx_hash)
            if tx.block_number is not None:
                return tx
            time.sleep(1)
        raise Exception(f"Transaction {tx_hash} not included in a block after {timeout} seconds")

    def wait_for_transactions(
        self, transactions: List[Transaction], timeout: int = 60
    ) -> List[TransactionByHashResponse]:
        """
        Uses `eth_getTransactionByHash` to wait unitl all transactions in list are included in a
        block.
        """
        tx_hashes = [tx.hash for tx in transactions]
        responses: List[TransactionByHashResponse] = []
        for _ in range(timeout):
            i = 0
            while i < len(tx_hashes):
                tx_hash = tx_hashes[i]
                tx = self.get_transaction_by_hash(tx_hash)
                if tx.block_number is not None:
                    responses.append(tx)
                    tx_hashes.pop(i)
                else:
                    i += 1
            if not tx_hashes:
                return responses
            time.sleep(1)
        raise Exception(f"Transaction {tx_hash} not included in a block after {timeout} seconds")

    def send_wait_transaction(self, transaction: Transaction, timeout: int = 60):
        """
        Sends a transaction and waits until it is included in a block.
        """
        self.send_transaction(transaction)
        return self.wait_for_transaction(transaction, timeout)

    def send_wait_transactions(self, transactions: List[Transaction], timeout: int = 60):
        """
        Sends a list of transactions and waits until all of them are included in a block.
        """
        self.send_transactions(transactions)
        return self.wait_for_transactions(transactions, timeout)


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
        return PayloadStatus(
            **self.post_request(f"newPayloadV{version}", *[to_json(param) for param in params])
        )

    def forkchoice_updated(
        self,
        forkchoice_state: ForkchoiceState,
        payload_attributes: PayloadAttributes | None = None,
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
                to_json(payload_attributes) if payload_attributes is not None else None,
            )
        )

    def get_payload(
        self,
        payload_id: Bytes,
        *,
        version: int,
    ) -> GetPayloadResponse:
        """
        `engine_getPayloadVX`: Retrieves a payload that was requested through
        `engine_forkchoiceUpdatedVX`.
        """
        return GetPayloadResponse(
            **self.post_request(
                f"getPayloadV{version}",
                f"{payload_id}",
            )
        )
