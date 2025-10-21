"""
JSON-RPC methods and helper functions for EEST consume based hive simulators.
"""

import logging
import os
import time
from itertools import count
from pprint import pprint
from typing import Any, ClassVar, Dict, List, Literal

import requests
from jwt import encode
from pydantic import ValidationError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ethereum_test_base_types import Address, Bytes, Hash, to_json
from ethereum_test_types import Transaction
from pytest_plugins.custom_logging import get_logger

from .rpc_types import (
    EthConfigResponse,
    ForkchoiceState,
    ForkchoiceUpdateResponse,
    GetBlobsResponse,
    GetPayloadResponse,
    JSONRPCError,
    PayloadAttributes,
    PayloadStatus,
    TransactionByHashResponse,
)

logger = get_logger(__name__)
BlockNumberType = int | Literal["latest", "earliest", "pending"]


class SendTransactionExceptionError(Exception):
    """
    Represent an exception that is raised when a transaction fails to be sent.
    """

    tx: Transaction | None = None
    tx_rlp: Bytes | None = None

    def __init__(
        self,
        *args: Any,
        tx: Transaction | None = None,
        tx_rlp: Bytes | None = None,
    ) -> None:
        """
        Initialize SendTransactionExceptionError class with the given
        transaction.
        """
        super().__init__(*args)
        self.tx = tx
        self.tx_rlp = tx_rlp

    def __str__(self) -> str:
        """Return string representation of the exception."""
        base = super().__str__()
        if self.tx is not None:
            return f"{base} Transaction={self.tx.model_dump_json()}"
        elif self.tx_rlp is not None:
            return f"{base} Transaction RLP={self.tx_rlp.hex()}"
        return base


class BaseRPC:
    """
    Represents a base RPC class for every RPC call used within EEST based hive
    simulators.
    """

    namespace: ClassVar[str]
    response_validation_context: Any | None

    def __init__(
        self,
        url: str,
        *,
        response_validation_context: Any | None = None,
    ):
        """Initialize BaseRPC class with the given url."""
        self.url = url
        self.request_id_counter = count(1)
        self.response_validation_context = response_validation_context

    def __init_subclass__(cls, namespace: str | None = None) -> None:
        """
        Set namespace of the RPC class to the lowercase of the class name.
        """
        if namespace is None:
            namespace = cls.__name__
            if namespace.endswith("RPC"):
                namespace = namespace.removesuffix("RPC")
            namespace = namespace.lower()
        cls.namespace = namespace

    @retry(
        retry=retry_if_exception_type(
            (requests.ConnectionError, ConnectionRefusedError)
        ),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4.0),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _make_request(
        self,
        url: str,
        json_payload: dict[str, Any],
        headers: dict[str, str],
        timeout: int | None,
    ) -> requests.Response:
        """
        Make HTTP POST request with retry logic for connection errors only.

        This method only retries network-level connection failures
        (ConnectionError, ConnectionRefusedError). HTTP status errors (4xx/5xx)
        are handled by the caller using response.raise_for_status() WITHOUT
        retries because:
        - 4xx errors are client errors (permanent failures, no point retrying)
        - 5xx errors are server errors that typically indicate
          application-level issues rather than transient network problems
        """
        logger.debug(f"Making HTTP request to {url}, timeout={timeout}")
        return requests.post(
            url, json=json_payload, headers=headers, timeout=timeout
        )

    def post_request(
        self,
        *,
        method: str,
        params: List[Any] | None = None,
        extra_headers: Dict[str, str] | None = None,
        request_id: int | str | None = None,
        timeout: int | None = None,
    ) -> Any:
        """
        Send JSON-RPC POST request to the client RPC server at port defined in
        the url.
        """
        if extra_headers is None:
            extra_headers = {}
        if params is None:
            params = []

        assert self.namespace, "RPC namespace not set"

        next_request_id_counter = next(self.request_id_counter)
        if request_id is None:
            request_id = next_request_id_counter

        payload = {
            "jsonrpc": "2.0",
            "method": f"{self.namespace}_{method}",
            "params": params,
            "id": request_id,
        }
        base_header = {
            "Content-Type": "application/json",
        }
        headers = base_header | extra_headers

        logger.debug(
            f"Sending RPC request to {self.url}, method={self.namespace}_{method}, "
            f"timeout={timeout}..."
        )

        response = self._make_request(self.url, payload, headers, timeout)
        response.raise_for_status()
        response_json = response.json()

        if "error" in response_json:
            raise JSONRPCError(**response_json["error"])

        assert "result" in response_json, (
            "RPC response didn't contain a result field"
        )
        result = response_json["result"]
        return result


class EthRPC(BaseRPC):
    """
    Represents an `eth_X` RPC class for every default ethereum RPC method used
    within EEST based hive simulators.
    """

    transaction_wait_timeout: int = 60
    poll_interval: float = 1.0  # how often to poll for tx inclusion

    BlockNumberType = int | Literal["latest", "earliest", "pending"]

    def __init__(
        self,
        *args: Any,
        transaction_wait_timeout: int = 60,
        poll_interval: float | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize EthRPC class with the given url and transaction wait
        timeout.
        """
        super().__init__(*args, **kwargs)
        self.transaction_wait_timeout = transaction_wait_timeout

        # Allow overriding via env "flag" EEST_POLL_INTERVAL or ctor arg
        # Priority: ctor arg > env var > default (1.0)
        env_val = os.getenv("EEST_POLL_INTERVAL")
        if poll_interval is not None:
            self.poll_interval = float(poll_interval)
        elif env_val:
            try:
                self.poll_interval = float(env_val)
            except ValueError:
                logger.warning(
                    "Invalid EEST_POLL_INTERVAL=%r; falling back to 1.0s",
                    env_val,
                )
                self.poll_interval = 1.0
        else:
            self.poll_interval = 1.0

    def config(self, timeout: int | None = None) -> EthConfigResponse | None:
        """
        `eth_config`: Returns information about a fork configuration of the
        client.
        """
        try:
            response = self.post_request(method="config", timeout=timeout)
            if response is None:
                logger.warning("eth_config request: failed to get response")
                return None
            return EthConfigResponse.model_validate(
                response, context=self.response_validation_context
            )
        except ValidationError as e:
            pprint(e.errors())
            raise e
        except Exception as e:
            logger.debug(
                f"exception occurred when sending JSON-RPC request: {e}"
            )
            raise e

    def chain_id(self) -> int:
        """`eth_chainId`: Returns the current chain id."""
        response = self.post_request(method="chainId", timeout=10)
        return int(response, 16)

    def get_block_by_number(
        self, block_number: BlockNumberType = "latest", full_txs: bool = True
    ) -> Any | None:
        """
        `eth_getBlockByNumber`: Returns information about a block by block
        number.
        """
        block = (
            hex(block_number)
            if isinstance(block_number, int)
            else block_number
        )
        params = [block, full_txs]
        response = self.post_request(method="getBlockByNumber", params=params)
        return response

    def get_block_by_hash(
        self, block_hash: Hash, full_txs: bool = True
    ) -> Any | None:
        """`eth_getBlockByHash`: Returns information about a block by hash."""
        params = [f"{block_hash}", full_txs]
        response = self.post_request(method="getBlockByHash", params=params)
        return response

    def get_balance(
        self, address: Address, block_number: BlockNumberType = "latest"
    ) -> int:
        """
        `eth_getBalance`: Returns the balance of the account of given address.
        """
        block = (
            hex(block_number)
            if isinstance(block_number, int)
            else block_number
        )
        params = [f"{address}", block]
        response = self.post_request(method="getBalance", params=params)
        return int(response, 16)

    def get_code(
        self, address: Address, block_number: BlockNumberType = "latest"
    ) -> Bytes:
        """`eth_getCode`: Returns code at a given address."""
        block = (
            hex(block_number)
            if isinstance(block_number, int)
            else block_number
        )
        params = [f"{address}", block]
        response = self.post_request(method="getCode", params=params)
        return Bytes(response)

    def get_transaction_count(
        self, address: Address, block_number: BlockNumberType = "latest"
    ) -> int:
        """
        `eth_getTransactionCount`: Returns the number of transactions sent from
        an address.
        """
        block = (
            hex(block_number)
            if isinstance(block_number, int)
            else block_number
        )
        params = [f"{address}", block]
        response = self.post_request(
            method="getTransactionCount", params=params
        )
        return int(response, 16)

    def get_transaction_by_hash(
        self, transaction_hash: Hash
    ) -> TransactionByHashResponse | None:
        """`eth_getTransactionByHash`: Returns transaction details."""
        try:
            response = self.post_request(
                method="getTransactionByHash", params=[f"{transaction_hash}"]
            )
            if response is None:
                return None
            return TransactionByHashResponse.model_validate(
                response, context=self.response_validation_context
            )
        except ValidationError as e:
            pprint(e.errors())
            raise e

    def get_transaction_receipt(
        self, transaction_hash: Hash
    ) -> dict[str, Any] | None:
        """
        `eth_getTransactionReceipt`: Returns transaction receipt.

        Used to get the actual gas used by a transaction for gas validation
        in benchmark tests.
        """
        response = self.post_request(
            method="getTransactionReceipt", params=[f"{transaction_hash}"]
        )
        return response

    def get_storage_at(
        self,
        address: Address,
        position: Hash,
        block_number: BlockNumberType = "latest",
    ) -> Hash:
        """
        `eth_getStorageAt`: Returns the value from a storage position at a
        given address.
        """
        block = (
            hex(block_number)
            if isinstance(block_number, int)
            else block_number
        )
        params = [f"{address}", f"{position}", block]
        response = self.post_request(method="getStorageAt", params=params)
        return Hash(response)

    def gas_price(self) -> int:
        """
        `eth_gasPrice`: Returns the number of transactions sent from an
        address.
        """
        response = self.post_request(method="gasPrice")
        return int(response, 16)

    def send_raw_transaction(
        self, transaction_rlp: Bytes, request_id: int | str | None = None
    ) -> Hash:
        """`eth_sendRawTransaction`: Send a transaction to the client."""
        try:
            response = self.post_request(
                method="sendRawTransaction",
                params=[transaction_rlp.hex()],
                request_id=request_id,
            )
            result_hash = Hash(response)
            assert result_hash is not None
            return result_hash
        except Exception as e:
            raise SendTransactionExceptionError(
                str(e), tx_rlp=transaction_rlp
            ) from e

    def send_transaction(self, transaction: Transaction) -> Hash:
        """`eth_sendRawTransaction`: Send a transaction to the client."""
        # TODO: is this a copypaste error from above?
        try:
            response = self.post_request(
                method="sendRawTransaction",
                params=[transaction.rlp().hex()],
                request_id=transaction.metadata_string(),
            )
            result_hash = Hash(response)
            assert result_hash == transaction.hash
            assert result_hash is not None
            return transaction.hash
        except Exception as e:
            raise SendTransactionExceptionError(str(e), tx=transaction) from e

    def send_transactions(self, transactions: List[Transaction]) -> List[Hash]:
        """
        Use `eth_sendRawTransaction` to send a list of transactions to the
        client.
        """
        return [self.send_transaction(tx) for tx in transactions]

    def storage_at_keys(
        self,
        account: Address,
        keys: List[Hash],
        block_number: BlockNumberType = "latest",
    ) -> Dict[Hash, Hash]:
        """
        Retrieve the storage values for the specified keys at a given address
        and block number.
        """
        results: Dict[Hash, Hash] = {}
        for key in keys:
            storage_value = self.get_storage_at(account, key, block_number)
            results[key] = storage_value
        return results

    def wait_for_transaction(
        self, transaction: Transaction
    ) -> TransactionByHashResponse:
        """
        Use `eth_getTransactionByHash` to wait until a transaction is included
        in a block.
        """
        tx_hash = transaction.hash
        start_time = time.time()
        while True:
            tx = self.get_transaction_by_hash(tx_hash)
            if tx is not None and tx.block_number is not None:
                return tx
            if (time.time() - start_time) > self.transaction_wait_timeout:
                break
            time.sleep(self.poll_interval)
        raise Exception(
            f"Transaction {tx_hash} ({transaction.model_dump_json()}) not included in a "
            f"block after {self.transaction_wait_timeout} seconds"
        )

    def wait_for_transactions(
        self, transactions: List[Transaction]
    ) -> List[TransactionByHashResponse]:
        """
        Use `eth_getTransactionByHash` to wait until all transactions in list
        are included in a block.
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
            time.sleep(self.poll_interval)
        missing_txs_strings = [
            f"{tx.hash} ({tx.model_dump_json()})"
            for tx in transactions
            if tx.hash in tx_hashes
        ]
        raise Exception(
            f"Transactions {', '.join(missing_txs_strings)} not included in a block "
            f"after {self.transaction_wait_timeout} seconds"
        )

    def send_wait_transaction(self, transaction: Transaction) -> Any:
        """Send transaction and waits until it is included in a block."""
        self.send_transaction(transaction)
        return self.wait_for_transaction(transaction)

    def send_wait_transactions(
        self, transactions: List[Transaction]
    ) -> List[Any]:
        """
        Send list of transactions and waits until all of them are included in a
        block.
        """
        self.send_transactions(transactions)
        return self.wait_for_transactions(transactions)


class DebugRPC(EthRPC):
    """
    Represents an `debug_X` RPC class for every default ethereum RPC method
    used within EEST based hive simulators.
    """

    def trace_call(self, tr: dict[str, str], block_number: str) -> Any | None:
        """`debug_traceCall`: Returns pre state required for transaction."""
        params = [tr, block_number, {"tracer": "prestateTracer"}]
        return self.post_request(method="traceCall", params=params)


class EngineRPC(BaseRPC):
    """
    Represents an Engine API RPC class for every Engine API method used within
    EEST based hive simulators.
    """

    jwt_secret: bytes

    def __init__(
        self,
        *args: Any,
        jwt_secret: bytes = b"secretsecretsecretsecretsecretse",  # Default secret used in hive
        **kwargs: Any,
    ) -> None:
        """Initialize Engine RPC class with the given JWT secret."""
        super().__init__(*args, **kwargs)
        self.jwt_secret = jwt_secret

    def post_request(
        self,
        *,
        method: str,
        params: Any | None = None,
        extra_headers: Dict[str, str] | None = None,
        request_id: int | str | None = None,
        timeout: int | None = None,
    ) -> Any:
        """
        Send JSON-RPC POST request to the client RPC server at port defined in
        the url.
        """
        if extra_headers is None:
            extra_headers = {}
        jwt_token = encode(
            {"iat": int(time.time())},
            self.jwt_secret,
            algorithm="HS256",
        )
        extra_headers = {
            "Authorization": f"Bearer {jwt_token}",
        } | extra_headers

        return super().post_request(
            method=method,
            params=params,
            extra_headers=extra_headers,
            timeout=timeout,
            request_id=request_id,
        )

    def new_payload(self, *params: Any, version: int) -> PayloadStatus:
        """
        `engine_newPayloadVX`: Attempts to execute the given payload on an
        execution client.
        """
        method = f"newPayloadV{version}"
        params_list = [to_json(param) for param in params]

        return PayloadStatus.model_validate(
            self.post_request(method=method, params=params_list),
            context=self.response_validation_context,
        )

    def forkchoice_updated(
        self,
        forkchoice_state: ForkchoiceState,
        payload_attributes: PayloadAttributes | None = None,
        *,
        version: int,
    ) -> ForkchoiceUpdateResponse:
        """
        `engine_forkchoiceUpdatedVX`: Updates the forkchoice state of the
        execution client.
        """
        method = f"forkchoiceUpdatedV{version}"

        if payload_attributes is None:
            params = [to_json(forkchoice_state), None]
        else:
            params = [to_json(forkchoice_state), to_json(payload_attributes)]

        return ForkchoiceUpdateResponse.model_validate(
            self.post_request(
                method=method,
                params=params,
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
        method = f"getPayloadV{version}"

        return GetPayloadResponse.model_validate(
            self.post_request(
                method=method,
                params=[f"{payload_id}"],
            ),
            context=self.response_validation_context,
        )

    def get_blobs(
        self,
        versioned_hashes: List[Hash],
        *,
        version: int,
    ) -> GetBlobsResponse | None:
        """
        `engine_getBlobsVX`: Retrieves blobs from an execution layers tx pool.
        """
        method = f"getBlobsV{version}"
        params = [f"{h}" for h in versioned_hashes]

        response = self.post_request(
            method=method,
            params=[params],
        )
        if response is None:  # for tests that request non-existing blobs
            logger.debug("get_blobs response received but it has value: None")
            return None

        return GetBlobsResponse.model_validate(
            response,
            context=self.response_validation_context,
        )


class NetRPC(BaseRPC):
    """Represents a net RPC class for network-related RPC calls."""

    def peer_count(self) -> int:
        """`net_peerCount`: Get the number of peers connected to the client."""
        response = self.post_request(method="peerCount")
        return int(response, 16)  # hex -> int


class AdminRPC(BaseRPC):
    """Represents an admin RPC class for administrative RPC calls."""

    def add_peer(self, enode: str) -> bool:
        """`admin_addPeer`: Add a peer by enode URL."""
        return self.post_request(method="addPeer", params=[enode])
