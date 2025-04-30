"""JSON-RPC methods and helper functions for EEST consume based hive simulators."""

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
    GetBlobsResponse,
    GetPayloadResponse,
    JSONRPCError,
    PayloadAttributes,
    PayloadStatus,
    TransactionByHashResponse,
)

BlockNumberType = Union[int, Literal["latest", "earliest", "pending"]]


class SendTransactionExceptionError(Exception):
    """Represent an exception that is raised when a transaction fails to be sent."""

    tx: Transaction | None = None
    tx_rlp: Bytes | None = None

    def __init__(self, *args, tx: Transaction | None = None, tx_rlp: Bytes | None = None):
        """Initialize SendTransactionExceptionError class with the given transaction."""
        super().__init__(*args)
        self.tx = tx
        self.tx_rlp = tx_rlp

    def __str__(self):
        """Return string representation of the exception."""
        if self.tx is not None:
            f"{super().__str__()} Transaction={self.tx.model_dump_json()}"
        elif self.tx_rlp is not None:
            return f"{super().__str__()} Transaction RLP={self.tx_rlp.hex()}"
        return super().__str__()


class BaseRPC:
    """Represents a base RPC class for every RPC call used within EEST based hive simulators."""

    namespace: ClassVar[str]
    response_validation_context: Any | None

    def __init__(
        self,
        url: str,
        extra_headers: Dict | None = None,
        response_validation_context: Any | None = None,
    ):
        """Initialize BaseRPC class with the given url."""
        if extra_headers is None:
            extra_headers = {}
        self.url = url
        self.request_id_counter = count(1)
        self.extra_headers = extra_headers
        self.response_validation_context = response_validation_context

    def __init_subclass__(cls) -> None:
        """Set namespace of the RPC class to the lowercase of the class name."""
        namespace = cls.__name__
        if namespace.endswith("RPC"):
            namespace = namespace[:-3]
        cls.namespace = namespace.lower()

    def post_request(self, method: str, *params: Any, extra_headers: Dict | None = None) -> Any:
        """Send JSON-RPC POST request to the client RPC server at port defined in the url."""
        if extra_headers is None:
            extra_headers = {}
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
            raise JSONRPCError(**response_json["error"])

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

    def __init__(
        self,
        url: str,
        extra_headers: Dict | None = None,
        *,
        transaction_wait_timeout: int = 60,
        response_validation_context: Any | None = None,
    ):
        """Initialize EthRPC class with the given url and transaction wait timeout."""
        if extra_headers is None:
            extra_headers = {}
        super().__init__(
            url, extra_headers, response_validation_context=response_validation_context
        )
        self.transaction_wait_timeout = transaction_wait_timeout

    def get_block_by_number(self, block_number: BlockNumberType = "latest", full_txs: bool = True):
        """`eth_getBlockByNumber`: Returns information about a block by block number."""
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return self.post_request("getBlockByNumber", block, full_txs)

    def get_balance(self, address: Address, block_number: BlockNumberType = "latest") -> int:
        """`eth_getBalance`: Returns the balance of the account of given address."""
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return int(self.post_request("getBalance", f"{address}", block), 16)

    def get_code(self, address: Address, block_number: BlockNumberType = "latest") -> Bytes:
        """`eth_getCode`: Returns code at a given address."""
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return Bytes(self.post_request("getCode", f"{address}", block))

    def get_transaction_count(
        self, address: Address, block_number: BlockNumberType = "latest"
    ) -> int:
        """`eth_getTransactionCount`: Returns the number of transactions sent from an address."""
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return int(self.post_request("getTransactionCount", f"{address}", block), 16)

    def get_transaction_by_hash(self, transaction_hash: Hash) -> TransactionByHashResponse | None:
        """`eth_getTransactionByHash`: Returns transaction details."""
        try:
            response = self.post_request("getTransactionByHash", f"{transaction_hash}")
            if response is None:
                return None
            return TransactionByHashResponse.model_validate(
                response, context=self.response_validation_context
            )
        except ValidationError as e:
            pprint(e.errors())
            raise e

    def get_storage_at(
        self, address: Address, position: Hash, block_number: BlockNumberType = "latest"
    ) -> Hash:
        """`eth_getStorageAt`: Returns the value from a storage position at a given address."""
        block = hex(block_number) if isinstance(block_number, int) else block_number
        return Hash(self.post_request("getStorageAt", f"{address}", f"{position}", block))

    def gas_price(self) -> int:
        """`eth_gasPrice`: Returns the number of transactions sent from an address."""
        return int(self.post_request("gasPrice"), 16)

    def send_raw_transaction(self, transaction_rlp: Bytes) -> Hash:
        """`eth_sendRawTransaction`: Send a transaction to the client."""
        try:
            result_hash = Hash(self.post_request("sendRawTransaction", f"{transaction_rlp.hex()}"))
            assert result_hash is not None
            return result_hash
        except Exception as e:
            raise SendTransactionExceptionError(str(e), tx_rlp=transaction_rlp) from e

    def send_transaction(self, transaction: Transaction) -> Hash:
        """`eth_sendRawTransaction`: Send a transaction to the client."""
        try:
            result_hash = Hash(
                self.post_request("sendRawTransaction", f"{transaction.rlp().hex()}")
            )
            assert result_hash == transaction.hash
            assert result_hash is not None
            return transaction.hash
        except Exception as e:
            raise SendTransactionExceptionError(str(e), tx=transaction) from e

    def send_transactions(self, transactions: List[Transaction]) -> List[Hash]:
        """Use `eth_sendRawTransaction` to send a list of transactions to the client."""
        return [self.send_transaction(tx) for tx in transactions]

    def storage_at_keys(
        self, account: Address, keys: List[Hash], block_number: BlockNumberType = "latest"
    ) -> Dict[Hash, Hash]:
        """
        Retrieve the storage values for the specified keys at a given address and block
        number.
        """
        results: Dict[Hash, Hash] = {}
        for key in keys:
            storage_value = self.get_storage_at(account, key, block_number)
            results[key] = storage_value
        return results

    def wait_for_transaction(self, transaction: Transaction) -> TransactionByHashResponse:
        """Use `eth_getTransactionByHash` to wait until a transaction is included in a block."""
        tx_hash = transaction.hash
        start_time = time.time()
        while True:
            tx = self.get_transaction_by_hash(tx_hash)
            if tx is not None and tx.block_number is not None:
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
        Use `eth_getTransactionByHash` to wait until all transactions in list are included in a
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
                if tx is not None and tx.block_number is not None:
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
        """Send transaction and waits until it is included in a block."""
        self.send_transaction(transaction)
        return self.wait_for_transaction(transaction)

    def send_wait_transactions(self, transactions: List[Transaction]):
        """Send list of transactions and waits until all of them are included in a block."""
        self.send_transactions(transactions)
        return self.wait_for_transactions(transactions)


class DebugRPC(EthRPC):
    """
    Represents an `debug_X` RPC class for every default ethereum RPC method used within EEST based
    hive simulators.
    """

    def trace_call(self, tr: dict[str, str], block_number: str):
        """`debug_traceCall`: Returns pre state required for transaction."""
        return self.post_request("traceCall", tr, block_number, {"tracer": "prestateTracer"})


class EngineRPC(BaseRPC):
    """
    Represents an Engine API RPC class for every Engine API method used within EEST based hive
    simulators.
    """

    def post_request(self, method: str, *params: Any, extra_headers: Dict | None = None) -> Any:
        """Send JSON-RPC POST request to the client RPC server at port defined in the url."""
        if extra_headers is None:
            extra_headers = {}
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
        """`engine_newPayloadVX`: Attempts to execute the given payload on an execution client."""
        return PayloadStatus.model_validate(
            self.post_request(f"newPayloadV{version}", *[to_json(param) for param in params]),
            context=self.response_validation_context,
        )

    def forkchoice_updated(
        self,
        forkchoice_state: ForkchoiceState,
        payload_attributes: PayloadAttributes | None = None,
        *,
        version: int,
    ) -> ForkchoiceUpdateResponse:
        """`engine_forkchoiceUpdatedVX`: Updates the forkchoice state of the execution client."""
        return ForkchoiceUpdateResponse.model_validate(
            self.post_request(
                f"forkchoiceUpdatedV{version}",
                to_json(forkchoice_state),
                to_json(payload_attributes) if payload_attributes is not None else None,
            ),
            context=self.response_validation_context,
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
        return GetPayloadResponse.model_validate(
            self.post_request(
                f"getPayloadV{version}",
                f"{payload_id}",
            ),
            context=self.response_validation_context,
        )

    def get_blobs(
        self,
        params: List[Hash],
        *,
        version: int,
    ) -> GetBlobsResponse:
        """`engine_getBlobsVX`: Retrieves blobs from an execution layers tx pool."""
        return GetBlobsResponse.model_validate(
            self.post_request(
                f"getBlobsV{version}",
                *[to_json(param) for param in params],
            ),
            context=self.response_validation_context,
        )
