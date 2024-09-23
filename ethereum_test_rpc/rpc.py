"""
JSON-RPC methods and helper functions for EEST consume based hive simulators.
"""

import time
from itertools import count
from pprint import pprint
from typing import Any, ClassVar, Dict, List, Literal, Union

import requests
from jwt import encode
from pydantic import ValidationError

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


class SendTransactionException(Exception):
    """
    Represents an exception that is raised when a transaction fails to be sent.
    """

    tx: Transaction

    def __init__(self, *args, tx: Transaction):
        """
        Initializes the SendTransactionException class with the given transaction
        """
        super().__init__(*args)
        self.tx = tx

    def __str__(self):
        """
        Returns a string representation of the exception.
        """
        return f"{super().__str__()} Transaction={self.tx.model_dump_json()}"


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

    transaction_wait_timeout: int = 60

    BlockNumberType = Union[int, Literal["latest", "earliest", "pending"]]

    def __init__(self, url: str, extra_headers: Dict = {}, *, transaction_wait_timeout: int = 60):
        """
        Initializes the EthRPC class with the given url and transaction wait timeout.
        """
        super().__init__(url, extra_headers)
        self.transaction_wait_timeout = transaction_wait_timeout

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
        try:
            resp = TransactionByHashResponse(
                **self.post_request("getTransactionByHash", f"{transaction_hash}")
            )
            return resp
        except ValidationError as e:
            pprint(e.errors())
            raise e

    def get_storage_at(
        self, address: Address, position: Hash, block_number: BlockNumberType = "latest"
    ) -> Hash:
        """
        `eth_getStorageAt`: Returns the value from a storage position at a given address.
        """
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return Hash(self.post_request("getStorageAt", f"{address}", f"{position}", block))

    def gas_price(self) -> int:
        """
        `eth_gasPrice`: Returns the number of transactions sent from an address.
        """
        return int(self.post_request("gasPrice"), 16)

    def send_transaction(self, transaction: Transaction) -> Hash:
        """
        `eth_sendRawTransaction`: Send a transaction to the client.
        """
        try:
            result_hash = Hash(
                self.post_request("sendRawTransaction", f"0x{transaction.rlp.hex()}")
            )
            assert result_hash == transaction.hash
            assert result_hash is not None
            return transaction.hash
        except Exception as e:
            raise SendTransactionException(str(e), tx=transaction)

    def send_transactions(self, transactions: List[Transaction]) -> List[Hash]:
        """
        Uses `eth_sendRawTransaction` to send a list of transactions to the client.
        """
        return [self.send_transaction(tx) for tx in transactions]

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

    def wait_for_transaction(self, transaction: Transaction) -> TransactionByHashResponse:
        """
        Uses `eth_getTransactionByHash` to wait until a transaction is included in a block.
        """
        tx_hash = transaction.hash
        start_time = time.time()
        while True:
            tx = self.get_transaction_by_hash(tx_hash)
            if tx.block_number is not None:
                return tx
            if (time.time() - start_time) > self.transaction_wait_timeout:
                break
            time.sleep(1)
        raise Exception(
            f"Transaction {tx_hash} ({transaction.model_dump_json()}) not included in a "
            f"block after {self.transaction_wait_timeout} seconds"
        )

    def wait_for_transactions(
        self, transactions: List[Transaction]
    ) -> List[TransactionByHashResponse]:
        """
        Uses `eth_getTransactionByHash` to wait unitl all transactions in list are included in a
        block.
        """
        tx_hashes = [tx.hash for tx in transactions]
        responses: List[TransactionByHashResponse] = []
        start_time = time.time()
        while True:
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
            if (time.time() - start_time) > self.transaction_wait_timeout:
                break
            time.sleep(1)
        missing_txs_strings = [
            f"{tx.hash} ({tx.model_dump_json()})" for tx in transactions if tx.hash in tx_hashes
        ]
        raise Exception(
            f"Transactions {', '.join(missing_txs_strings)} not included in a block "
            f"after {self.transaction_wait_timeout} seconds"
        )

    def send_wait_transaction(self, transaction: Transaction):
        """
        Sends a transaction and waits until it is included in a block.
        """
        self.send_transaction(transaction)
        return self.wait_for_transaction(transaction)

    def send_wait_transactions(self, transactions: List[Transaction]):
        """
        Sends a list of transactions and waits until all of them are included in a block.
        """
        self.send_transactions(transactions)
        return self.wait_for_transactions(transactions)


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
