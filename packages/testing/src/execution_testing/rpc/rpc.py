"""
JSON-RPC methods and helper functions for EEST consume based hive simulators.
"""

import logging
import os
import time
from contextlib import AbstractContextManager, nullcontext
from itertools import count
from pprint import pprint
from typing import Any, Callable, ClassVar, Dict, List, Literal, Sequence

import requests
from jwt import encode
from pydantic import ValidationError
from tenacity import (
    RetryCallState,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tenacity import (
    wait_fixed as wait_fixed_tenacity,
)

from execution_testing.base_types import (
    Account,
    Address,
    Alloc,
    Bytes,
    Hash,
    to_json,
)
from execution_testing.logging import (
    get_logger,
)

from .rpc_types import (
    EthConfigResponse,
    ForkchoiceState,
    ForkchoiceUpdateResponse,
    GetBlobsResponse,
    GetPayloadResponse,
    JSONRPCRequest,
    JSONRPCResponse,
    PayloadAttributes,
    PayloadStatus,
    PayloadStatusEnum,
    RPCCall,
    TransactionByHashResponse,
    TransactionProtocol,
)

logger = get_logger(__name__)
BlockNumberType = int | Literal["latest", "earliest", "pending"]


class SendTransactionExceptionError(Exception):
    """
    Represent an exception that is raised when a transaction fails to be sent.
    """

    tx: TransactionProtocol | None = None
    tx_rlp: Bytes | None = None

    def __init__(
        self,
        *args: Any,
        tx: TransactionProtocol | None = None,
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
            rlp_hex = self.tx_rlp.hex()
            # Cap RLP output at 200 characters to avoid overwhelming output
            max_rlp_length = 200
            if len(rlp_hex) > max_rlp_length:
                rlp_display = f"{rlp_hex[:max_rlp_length]}... (truncated)"
            else:
                rlp_display = rlp_hex
            return f"{base} Transaction RLP={rlp_display}"
        return base


class BlockNotAvailableError(Exception):
    """Raised when block is not available after retry attempts."""

    def __init__(
        self,
        block_hash: Hash,
        attempts: int,
        elapsed: float,
        interval: float,
    ):
        """Initialize with retry statistics."""
        self.block_hash = block_hash
        self.attempts = attempts
        self.elapsed = elapsed
        self.interval = interval
        msg = (
            f"Block {block_hash} not available after {attempts} attempts "
            f"over {elapsed:.1f}s (interval: {interval}s)"
        )
        super().__init__(msg)


class ForkchoiceUpdateTimeoutError(Exception):
    """Raised when forkchoice update doesn't reach VALID in time."""

    def __init__(
        self,
        attempts: int,
        elapsed: float,
        interval: float,
        final_status: PayloadStatusEnum,
    ):
        """Initialize with retry statistics and final status."""
        self.attempts = attempts
        self.elapsed = elapsed
        self.interval = interval
        self.final_status = final_status
        msg = (
            f"Forkchoice update failed to reach VALID after {attempts} "
            f"attempts over {elapsed:.1f}s (interval: {interval}s), "
            f"final status: {final_status}"
        )
        super().__init__(msg)


class PeerConnectionTimeoutError(Exception):
    """Raised when peer connection is not established within retry limits."""

    def __init__(
        self,
        attempts: int,
        elapsed: float,
        interval: float,
        expected_peers: int,
        actual_peers: int,
    ):
        """Initialize with retry statistics and peer counts."""
        self.attempts = attempts
        self.elapsed = elapsed
        self.interval = interval
        self.expected_peers = expected_peers
        self.actual_peers = actual_peers
        msg = (
            f"Peer connection not established after {attempts} attempts "
            f"over {elapsed:.1f}s (interval: {interval}s), "
            f"expected >= {expected_peers} peers, got {actual_peers}"
        )
        super().__init__(msg)


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
        self.session = requests.Session()

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
        json_payload: dict[str, Any] | list[dict[str, Any]],
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
        return self.session.post(
            url, json=json_payload, headers=headers, timeout=timeout
        )

    def _build_json_rpc_request(
        self,
        call: RPCCall,
    ) -> JSONRPCRequest:
        """Build a JSON-RPC request object with namespace prefix."""
        assert self.namespace, "RPC namespace not set"

        next_request_id_counter = next(self.request_id_counter)
        request_id = call.request_id
        if request_id is None:
            request_id = next_request_id_counter

        return JSONRPCRequest(
            method=f"{self.namespace}_{call.method}",
            params=call.params,
            id=request_id,
        )

    def namespace_extra_headers(self) -> Dict[str, str]:
        """
        Extra headers that are included by default in this namespace.

        For non-jwt namespaces, this method returns an empty dictionary.
        """
        return {}

    def post_request(
        self,
        *,
        request: RPCCall,
        extra_headers: Dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> JSONRPCResponse:
        """
        Send JSON-RPC POST request to the client RPC server at port defined in
        the url.
        """
        if extra_headers is None:
            extra_headers = {}

        json_rpc_request = self._build_json_rpc_request(request)
        base_header = {
            "Content-Type": "application/json",
        }
        headers = base_header | extra_headers | self.namespace_extra_headers()

        logger.debug(
            f"Sending RPC request to {self.url}, "
            f"method={json_rpc_request.method}, timeout={timeout}..."
        )

        response = self._make_request(
            self.url, json_rpc_request.model_dump(), headers, timeout
        )
        response.raise_for_status()

        return JSONRPCResponse.model_validate(response.json())

    def post_batch_request(
        self,
        *,
        calls: Sequence[RPCCall],
        extra_headers: Dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> List[JSONRPCResponse]:
        """
        Send a JSON-RPC batch POST request to the client RPC server at port
        defined in the url.
        """
        if extra_headers is None:
            extra_headers = {}

        json_rpc_requests = [
            self._build_json_rpc_request(call) for call in calls
        ]
        payload = [r.model_dump() for r in json_rpc_requests]
        base_header = {
            "Content-Type": "application/json",
        }
        headers = base_header | extra_headers | self.namespace_extra_headers()

        logger.debug(
            f"Sending batch RPC request to {self.url}, "
            f"{len(json_rpc_requests)} calls, timeout={timeout}..."
        )

        response = self._make_request(self.url, payload, headers, timeout)
        response.raise_for_status()
        response_json = response.json()

        assert isinstance(response_json, list), (
            "Batch RPC response is not a list"
        )

        response_map: dict[int | str, JSONRPCResponse] = {
            r.id: r
            for r in [
                JSONRPCResponse.model_validate(item) for item in response_json
            ]
        }

        results = []
        for json_rpc_request in json_rpc_requests:
            assert json_rpc_request.id in response_map, (
                f"Missing response for request ID {json_rpc_request.id}"
            )
            results.append(response_map[json_rpc_request.id])

        logger.info(f"Batch RPC: {len(results)} responses received")
        return results


class BaseJwtRPC(BaseRPC):
    """
    Represents an RPC namespace class that uses JWT authentication.
    """

    jwt_secret: bytes

    # Default secret used in hive
    DEFAULT_JWT_SECRET: bytes = b"secretsecretsecretsecretsecretse"

    def __init__(
        self,
        *args: Any,
        jwt_secret: bytes = DEFAULT_JWT_SECRET,
        **kwargs: Any,
    ) -> None:
        """Initialize Engine RPC class with the given JWT secret."""
        super().__init__(*args, **kwargs)
        self.jwt_secret = jwt_secret

    def namespace_extra_headers(self) -> Dict[str, str]:
        """
        Overload to include JWT authentication header field.
        """
        jwt_token = encode(
            {"iat": int(time.time())},
            self.jwt_secret,
            algorithm="HS256",
        )
        return {
            "Authorization": f"Bearer {jwt_token}",
        }


class EthRPC(BaseRPC):
    """
    Represents an `eth_X` RPC class for every default ethereum RPC method used
    within EEST based hive simulators.
    """

    OVERLOAD_THRESHOLD: int = 1000
    DEFAULT_MAX_TRANSACTIONS_PER_BATCH: int = 750

    transaction_wait_timeout: int = 60
    poll_interval: float = 1.0  # how often to poll for tx inclusion
    max_transactions_per_batch: int = DEFAULT_MAX_TRANSACTIONS_PER_BATCH

    gas_information_stale_seconds: int

    _gas_information_cache: Dict[str, int]
    _gas_information_cache_timestamp: Dict[str, float]

    BlockNumberType = int | Literal["latest", "earliest", "pending"]

    def __init__(
        self,
        *args: Any,
        transaction_wait_timeout: int = 60,
        poll_interval: float | None = None,
        gas_information_stale_seconds: int = 12,
        max_transactions_per_batch: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize JWT-authenticated RPC class with the given JWT secret."""
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
        self.gas_information_stale_seconds = gas_information_stale_seconds
        self._gas_information_cache = {
            "gasPrice": 0,
            "maxPriorityFeePerGas": 0,
            "blobBaseFee": 0,
        }
        self._gas_information_cache_timestamp = {
            "gasPrice": 0.0,
            "maxPriorityFeePerGas": 0.0,
            "blobBaseFee": 0.0,
        }

        # Transaction batching configuration
        if max_transactions_per_batch is None:
            max_transactions_per_batch = (
                self.DEFAULT_MAX_TRANSACTIONS_PER_BATCH
            )
        self.max_transactions_per_batch = max_transactions_per_batch
        if max_transactions_per_batch > self.OVERLOAD_THRESHOLD:
            logger.warning(
                f"max_transactions_per_batch ({max_transactions_per_batch}) "
                f"exceeds the safe threshold ({self.OVERLOAD_THRESHOLD}). "
                "This may cause RPC service instability or failures."
            )

    def config(self, timeout: int | None = None) -> EthConfigResponse | None:
        """
        `eth_config`: Returns information about a fork configuration of the
        client.
        """
        try:
            logger.info("Requesting eth_config..")
            response = self.post_request(
                request=RPCCall(method="config"), timeout=timeout
            ).result_or_raise()
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
        logger.info("Requesting chainid of provided RPC endpoint..")
        response = self.post_request(
            request=RPCCall(method="chainId"), timeout=10
        ).result_or_raise()
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
        logger.info(f"Requesting info about block {block}..")
        params = [block, full_txs]
        return self.post_request(
            request=RPCCall(method="getBlockByNumber", params=params)
        ).result_or_raise()

    def get_block_by_hash(
        self, block_hash: Hash, full_txs: bool = True
    ) -> Any | None:
        """`eth_getBlockByHash`: Returns information about a block by hash."""
        logger.info(f"Requesting block info of {block_hash}..")
        params = [f"{block_hash}", full_txs]
        return self.post_request(
            request=RPCCall(method="getBlockByHash", params=params)
        ).result_or_raise()

    def get_block_by_hash_with_retry(
        self,
        block_hash: Hash,
        *,
        max_attempts: int = 5,
        wait_fixed: float = 1.0,
        on_retry: Callable[[RetryCallState], None] | None = None,
    ) -> dict[str, Any]:
        """
        Get block by hash, retrying if not yet available.

        Args:
            block_hash: The hash of the block to retrieve.
            max_attempts: Maximum number of attempts before giving up.
            wait_fixed: Fixed interval in seconds between retries.
            on_retry: Optional callback invoked before each retry sleep.
                Receives tenacity RetryCallState. If None, logs at debug level.

        Returns:
            Block data as a dictionary.

        Raises:
            BlockNotAvailableError: If block not available after max_attempts.

        """
        attempts = 0
        start_time = time.time()

        def default_on_retry(retry_state: RetryCallState) -> None:
            logger.debug(
                f"Block {block_hash} not available, "
                f"attempt {retry_state.attempt_number}, "
                f"retrying in {wait_fixed}s..."
            )

        retry_callback = on_retry if on_retry is not None else default_on_retry

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_fixed_tenacity(wait_fixed),
            before_sleep=retry_callback,
            reraise=True,
        )
        def _get_block() -> dict[str, Any]:
            nonlocal attempts
            attempts += 1
            block = self.get_block_by_hash(block_hash)
            if block is None:
                raise BlockNotAvailableError(
                    block_hash=block_hash,
                    attempts=attempts,
                    elapsed=time.time() - start_time,
                    interval=wait_fixed,
                )
            return block

        return _get_block()

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
        logger.info(f"Requesting balance of {address} at block {block}")
        params = [f"{address}", block]
        response = self.post_request(
            request=RPCCall(method="getBalance", params=params)
        ).result_or_raise()
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
        logger.info(f"Requesting code of {address} at block {block}")
        params = [f"{address}", block]
        response = self.post_request(
            request=RPCCall(method="getCode", params=params)
        ).result_or_raise()
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
        logger.info(f"Requesting nonce of {address}")
        params = [f"{address}", block]
        response = self.post_request(
            request=RPCCall(method="getTransactionCount", params=params)
        ).result_or_raise()
        return int(response, 16)

    def get_transaction_by_hash(
        self, transaction_hash: Hash
    ) -> TransactionByHashResponse | None:
        """`eth_getTransactionByHash`: Returns transaction details."""
        try:
            logger.info(f"Requesting tx details of {transaction_hash}")
            response = self.post_request(
                request=RPCCall(
                    method="getTransactionByHash",
                    params=[f"{transaction_hash}"],
                )
            ).result_or_raise()
            if response is None:
                return None
            return TransactionByHashResponse.model_validate(
                response, context=self.response_validation_context
            )
        except ValidationError as e:
            pprint(e.errors())
            raise e

    def get_transactions_by_hash(
        self, transaction_hashes: Sequence[Hash]
    ) -> List[TransactionByHashResponse | None]:
        """
        Batch `eth_getTransactionByHash` for multiple hashes.

        Return a list of responses in the same order as the input
        hashes. Entries are `None` if the transaction was not found.
        """
        if not transaction_hashes:
            return []
        calls = [
            RPCCall(
                method="getTransactionByHash",
                params=[f"{tx_hash}"],
            )
            for tx_hash in transaction_hashes
        ]
        responses = self.post_batch_request(calls=calls)
        results: List[TransactionByHashResponse | None] = []
        for response in responses:
            result = response.result_or_raise()
            if result is None:
                results.append(None)
            else:
                results.append(
                    TransactionByHashResponse.model_validate(
                        result,
                        context=self.response_validation_context,
                    )
                )
        return results

    def get_transaction_receipt(
        self, transaction_hash: Hash
    ) -> dict[str, Any] | None:
        """
        `eth_getTransactionReceipt`: Returns transaction receipt.

        Used to get the actual gas used by a transaction for gas validation
        in benchmark tests.
        """
        logger.info(f"Requesting tx receipt of {transaction_hash}")
        return self.post_request(
            request=RPCCall(
                method="getTransactionReceipt",
                params=[f"{transaction_hash}"],
            )
        ).result_or_raise()

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
        logger.info(
            f"Requesting storage value mapped to key {position} "
            f"of contract {address}"
        )
        params = [f"{address}", f"{position}", block]
        response = self.post_request(
            request=RPCCall(method="getStorageAt", params=params)
        ).result_or_raise()
        return Hash(response)

    def _get_gas_information(
        self,
        *,
        method: Literal["gasPrice", "maxPriorityFeePerGas", "blobBaseFee"],
    ) -> int:
        """Get gas information from the cache or the RPC server."""
        if (
            time.time() - self._gas_information_cache_timestamp[method]
            > self.gas_information_stale_seconds
        ):
            response = self.post_request(
                request=RPCCall(method=method)
            ).result_or_raise()
            logger.info(f"Requesting stale {method}")
            self._gas_information_cache[method] = int(response, 16)
            self._gas_information_cache_timestamp[method] = time.time()
        return self._gas_information_cache[method]

    def gas_price(self) -> int:
        """
        `eth_gasPrice`: Returns the gas price.
        """
        return self._get_gas_information(method="gasPrice")

    def max_priority_fee_per_gas(self) -> int:
        """
        `eth_maxPriorityFeePerGas`: Return the current max priority fee per
        gas of the network.
        """
        return self._get_gas_information(method="maxPriorityFeePerGas")

    def blob_base_fee(self) -> int:
        """Return the current blob base fee per gas of the network."""
        return self._get_gas_information(method="blobBaseFee")

    def send_raw_transaction(
        self, transaction_rlp: Bytes, request_id: int | str | None = None
    ) -> Hash:
        """`eth_sendRawTransaction`: Send a transaction to the client."""
        try:
            logger.info("Sending raw tx..")
            response = self.post_request(
                request=RPCCall(
                    method="sendRawTransaction",
                    params=[transaction_rlp.hex()],
                    request_id=request_id,
                )
            ).result_or_raise()
            result_hash = Hash(response)
            assert result_hash is not None
            return result_hash
        except Exception as e:
            logger.error(e)
            raise SendTransactionExceptionError(
                str(e), tx_rlp=transaction_rlp
            ) from e

    def send_transaction(self, transaction: TransactionProtocol) -> Hash:
        """
        Convenience method to send a single transaction to the client via
        `eth_sendRawTransaction`.
        """
        try:
            logger.info("Sending tx..")
            response = self.post_request(
                request=RPCCall(
                    method="sendRawTransaction",
                    params=[transaction.rlp().hex()],
                    request_id=transaction.metadata_string(),
                )
            ).result_or_raise()
            result_hash = Hash(response)
            assert result_hash == transaction.hash
            assert result_hash is not None
            return transaction.hash
        except Exception as e:
            raise SendTransactionExceptionError(str(e), tx=transaction) from e

    def send_transactions(
        self, transactions: Sequence[TransactionProtocol]
    ) -> List[Hash]:
        """
        Use `eth_sendRawTransaction` to send a batch of transactions to the
        client.
        """
        if not transactions:
            return []

        calls = [
            RPCCall(
                method="sendRawTransaction",
                params=[tx.rlp().hex()],
                request_id=tx.metadata_string(),
            )
            for tx in transactions
        ]
        responses = self.post_batch_request(calls=calls)

        results: List[Hash] = []
        for tx, response in zip(transactions, responses, strict=True):
            try:
                result_hash = Hash(response.result_or_raise())
                assert result_hash == tx.hash
                assert result_hash is not None
                results.append(tx.hash)
            except Exception as e:
                raise SendTransactionExceptionError(str(e), tx=tx) from e
        return results

    def _build_get_account_calls(
        self,
        address: Address,
        account: Account | None,
        block: str,
        skip_code: bool = False,
    ) -> tuple[List[RPCCall], List[tuple[str, Any]]]:
        """Build the RPC calls needed to fetch an account's state."""
        calls: List[RPCCall] = []
        # (field_name, storage_key)
        call_info: List[tuple[str, Any]] = []

        calls.append(
            RPCCall(
                method="getBalance",
                params=[f"{address}", block],
            )
        )
        call_info.append(("balance", None))
        if not skip_code:
            calls.append(
                RPCCall(
                    method="getCode",
                    params=[f"{address}", block],
                )
            )
            call_info.append(("code", None))
        calls.append(
            RPCCall(
                method="getTransactionCount",
                params=[f"{address}", block],
            )
        )
        call_info.append(("nonce", None))

        if account is not None and "storage" in account.model_fields_set:
            for key in account.storage.root:
                calls.append(
                    RPCCall(
                        method="getStorageAt",
                        params=[
                            f"{address}",
                            f"{Hash(key)}",
                            block,
                        ],
                    )
                )
                call_info.append(("storage", key))

        return calls, call_info

    @staticmethod
    def _parse_account_responses(
        call_info: List[tuple[str, Any]],
        responses: List[JSONRPCResponse],
    ) -> Account:
        """Parse RPC responses into an Account."""
        data: Dict[str, Any] = {}
        for (field, key), response in zip(call_info, responses, strict=True):
            result = response.result_or_raise()
            if field == "balance":
                data["balance"] = int(result, 16)
            elif field == "code":
                data["code"] = Bytes(result)
            elif field == "nonce":
                data["nonce"] = int(result, 16)
            elif field == "storage":
                if "storage" not in data:
                    data["storage"] = {}
                data["storage"][key] = Hash(result)
        return Account(**data)

    def get_account(
        self,
        address: Address,
        account: Account | None = None,
        block_number: BlockNumberType = "latest",
        skip_code: bool = False,
    ) -> Account:
        """
        Fetch account state from the chain for a single address using
        a batch RPC request.

        If `account` is provided, its storage keys are also fetched.
        If `skip_code` is True, the code fetch is omitted.
        """
        block = (
            hex(block_number)
            if isinstance(block_number, int)
            else block_number
        )
        calls, call_info = self._build_get_account_calls(
            address, account, block, skip_code=skip_code
        )
        responses = self.post_batch_request(calls=calls)
        return self._parse_account_responses(call_info, responses)

    def get_alloc(
        self,
        alloc: Alloc,
        block_number: BlockNumberType = "latest",
        skip_code: bool = False,
    ) -> Alloc:
        """
        Fetch account state from the chain for all addresses in the
        given alloc using a batch RPC request.

        If `skip_code` is True, the code fetch is omitted for all
        accounts.
        """
        if not alloc.root:
            return Alloc()

        block = (
            hex(block_number)
            if isinstance(block_number, int)
            else block_number
        )

        all_calls: List[RPCCall] = []
        # (address, per-account call_info list, call count)
        address_info: List[tuple[Address, List[tuple[str, Any]]]] = []

        for address, account in alloc.root.items():
            calls, call_info = self._build_get_account_calls(
                address, account, block, skip_code=skip_code
            )
            all_calls.extend(calls)
            address_info.append((address, call_info))

        responses = self.post_batch_request(calls=all_calls)

        result_alloc: Dict[Address, Account | None] = {}
        offset = 0
        for address, call_info in address_info:
            n = len(call_info)
            result_alloc[address] = self._parse_account_responses(
                call_info, responses[offset : offset + n]
            )
            offset += n

        return Alloc(root=result_alloc)

    @property
    def transaction_polling_context(self) -> AbstractContextManager:
        """
        Return a context manager acquired during transaction polling.

        By default a no-op. Subclasses can override to synchronize
        transaction querying with block building.
        """
        return nullcontext()

    def pending_transactions_handler(self) -> None:
        """
        Called inside the transaction_polling_context context during the
        transaction inclusion wait-loop.

        Useful for subclasses to override to introduce logic to perform
        between transaction waits, such as triggering the block building
        process.

        By default it only waits the `poll_interval`.
        """
        time.sleep(self.poll_interval)

    def wait_for_transaction(
        self, transaction: TransactionProtocol
    ) -> TransactionByHashResponse:
        """
        Use `eth_getTransactionByHash` to wait until a transaction is included
        in a block.
        """
        tx_hash = transaction.hash
        start_time = time.time()
        while True:
            logger.info(f"Waiting for inclusion of tx {tx_hash} in a block..")
            with self.transaction_polling_context:
                tx = self.get_transaction_by_hash(tx_hash)
                if tx is not None and tx.block_number is not None:
                    return tx
                if (time.time() - start_time) > self.transaction_wait_timeout:
                    break
                self.pending_transactions_handler()
        raise Exception(
            f"Transaction {tx_hash} ({transaction.model_dump_json()}) "
            f"not included in a block after "
            f"{self.transaction_wait_timeout} seconds"
        )

    def wait_for_transactions(
        self, transactions: Sequence[TransactionProtocol]
    ) -> List[TransactionByHashResponse]:
        """
        Use `eth_getTransactionByHash` batch requests to wait until all
        transactions in list are included in a block.
        """
        if not transactions:
            return []

        pending: dict[Hash, TransactionProtocol] = {
            tx.hash: tx for tx in transactions
        }
        found: dict[Hash, TransactionByHashResponse] = {}
        start_time = time.time()
        logger.info("Waiting for all transactions to be included in a block..")

        while pending:
            with self.transaction_polling_context:
                pending_hashes = list(pending.keys())
                tx_responses = self.get_transactions_by_hash(pending_hashes)

                newly_found: List[Hash] = []
                for tx_hash, tx_response in zip(
                    pending_hashes, tx_responses, strict=True
                ):
                    if tx_response is None:
                        continue
                    if tx_response.block_number is not None:
                        found[tx_hash] = tx_response
                        newly_found.append(tx_hash)
                        logger.info(
                            f"Tx {tx_response.hash} was included "
                            f"in block {tx_response.block_number}"
                        )

                for tx_hash in newly_found:
                    del pending[tx_hash]

                if not pending:
                    break

                if (time.time() - start_time) > self.transaction_wait_timeout:
                    missing_txs_strings = [
                        f"{tx.hash} ({tx.model_dump_json()})"
                        for tx in transactions
                        if tx.hash in pending
                    ]
                    raise Exception(
                        f"Transactions "
                        f"{', '.join(missing_txs_strings)} not "
                        f"included in a block after "
                        f"{self.transaction_wait_timeout} seconds"
                    )
                self.pending_transactions_handler()

        return [found[tx.hash] for tx in transactions]

    def send_wait_transaction(self, transaction: TransactionProtocol) -> Any:
        """Send transaction and waits until it is included in a block."""
        self.send_transaction(transaction)
        return self.wait_for_transaction(transaction)

    def send_wait_transactions(
        self, transactions: Sequence[TransactionProtocol]
    ) -> List[Any]:
        """
        Send list of transactions and waits until all of them are included in a
        block. Transactions are sent in batches to avoid RPC overload.
        """
        results: List[Any] = []
        batch_size = self.max_transactions_per_batch
        total_txs = len(transactions)

        for i in range(0, total_txs, batch_size):
            batch = transactions[i : i + batch_size]
            if total_txs > batch_size:
                logger.info(
                    f"Sending transaction batch {i // batch_size + 1} "
                    f"({len(batch)} transactions, "
                    f"{i + 1}-{min(i + batch_size, total_txs)} "
                    f"of {total_txs})"
                )
            self.send_transactions(batch)
            results.extend(self.wait_for_transactions(batch))

        return results


class DebugRPC(EthRPC):
    """
    Represents an `debug_X` RPC class for every default ethereum RPC method
    used within EEST based hive simulators.
    """

    def trace_call(self, tr: dict[str, str], block_number: str) -> Any | None:
        """`debug_traceCall`: Returns pre state required for transaction."""
        params = [tr, block_number, {"tracer": "prestateTracer"}]
        return self.post_request(
            request=RPCCall(method="traceCall", params=params)
        ).result_or_raise()


class EngineRPC(BaseJwtRPC):
    """
    Represents an Engine API RPC class for every Engine API method used within
    EEST based hive simulators.
    """

    def new_payload(self, *params: Any, version: int) -> PayloadStatus:
        """
        `engine_newPayloadVX`: Attempts to execute the given payload on an
        execution client.
        """
        method = f"newPayloadV{version}"
        params_list = [to_json(param) for param in params]

        return PayloadStatus.model_validate(
            self.post_request(
                request=RPCCall(method=method, params=params_list)
            ).result_or_raise(),
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
                request=RPCCall(method=method, params=params),
            ).result_or_raise(),
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
                request=RPCCall(method=method, params=[f"{payload_id}"]),
            ).result_or_raise(),
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
            request=RPCCall(method=method, params=[params]),
        ).result_or_raise()
        if response is None:  # for tests that request non-existing blobs
            logger.debug("get_blobs response received but it has value: None")
            return None

        return GetBlobsResponse.model_validate(
            response,
            context=self.response_validation_context,
        )

    def forkchoice_updated_with_retry(
        self,
        forkchoice_state: ForkchoiceState,
        forkchoice_version: int,
        *,
        max_attempts: int = 30,
        wait_fixed: float = 1.0,
        on_retry: Callable[[RetryCallState], None] | None = None,
    ) -> ForkchoiceUpdateResponse:
        """
        Send forkchoice update, retrying while SYNCING until terminal.

        Retries only while the client returns SYNCING status. Returns
        immediately on any terminal status (VALID, INVALID, ACCEPTED, etc.)
        - the caller is responsible for checking if the returned status
        matches expectations.

        Args:
            forkchoice_state: The forkchoice state to send.
            forkchoice_version: The forkchoice updated version (e.g., 1, 2, 3).
            max_attempts: Maximum number of attempts before giving up.
            wait_fixed: Fixed interval in seconds between retries.
            on_retry: Optional callback invoked before each retry sleep.
                Receives tenacity RetryCallState. If None, logs at debug level.

        Returns:
            ForkchoiceUpdateResponse with a terminal status (VALID, etc.).

        Raises:
            ForkchoiceUpdateTimeoutError: If still SYNCING after max_attempts.

        """
        # Track state for exception message in the case of timeout
        attempts = 0
        start_time = time.time()
        last_response: ForkchoiceUpdateResponse | None = None

        def default_on_retry(retry_state: RetryCallState) -> None:
            if last_response:
                status = str(last_response.payload_status.status)
            else:
                status = "N/A"
            logger.debug(
                f"Forkchoice update attempt {retry_state.attempt_number}: "
                f"status={status}, retrying in {wait_fixed}s..."
            )

        retry_callback = on_retry if on_retry is not None else default_on_retry

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_fixed_tenacity(wait_fixed),
            before_sleep=retry_callback,
            reraise=True,
        )
        def _do_forkchoice_update() -> ForkchoiceUpdateResponse:
            nonlocal attempts, last_response
            attempts += 1
            response = self.forkchoice_updated(
                forkchoice_state=forkchoice_state,
                payload_attributes=None,
                version=forkchoice_version,
            )
            last_response = response
            status = response.payload_status.status
            logger.info(f"Forkchoice update attempt {attempts}: {status}")
            if status == PayloadStatusEnum.SYNCING:
                raise ForkchoiceUpdateTimeoutError(
                    attempts=attempts,
                    elapsed=time.time() - start_time,
                    interval=wait_fixed,
                    final_status=status,
                )
            return response

        return _do_forkchoice_update()


class NetRPC(BaseRPC):
    """Represents a net RPC class for network-related RPC calls."""

    def peer_count(self) -> int:
        """`net_peerCount`: Get the number of peers connected to the client."""
        response = self.post_request(
            request=RPCCall(method="peerCount")
        ).result_or_raise()
        return int(response, 16)  # hex -> int

    def wait_for_peer_connection(
        self,
        *,
        min_peers: int = 1,
        max_attempts: int = 15,
        wait_fixed: float = 0.1,
        on_retry: Callable[[RetryCallState], None] | None = None,
    ) -> int:
        """
        Wait for peer connections to be established.

        Args:
            min_peers: Minimum number of peers required.
            max_attempts: Maximum number of attempts before giving up.
            wait_fixed: Fixed interval in seconds between retries.
            on_retry: Optional callback invoked before each retry sleep.
                Receives tenacity RetryCallState. If None, logs at debug level.

        Returns:
            The peer count once min_peers threshold is reached.

        Raises:
            PeerConnectionTimeoutError: If min_peers not reached within limits.

        """
        attempts = 0
        start_time = time.time()
        last_peer_count = 0

        def default_on_retry(retry_state: RetryCallState) -> None:
            attempt = retry_state.attempt_number
            logger.debug(
                f"Waiting for peer connection, attempt {attempt}: "
                f"{last_peer_count} peers, need >= {min_peers}, "
                f"retrying in {wait_fixed}s..."
            )

        retry_callback = on_retry if on_retry is not None else default_on_retry

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_fixed_tenacity(wait_fixed),
            before_sleep=retry_callback,
            reraise=True,
        )
        def _wait_for_peers() -> int:
            nonlocal attempts, last_peer_count
            attempts += 1
            peer_count = self.peer_count()
            last_peer_count = peer_count
            if peer_count < min_peers:
                raise PeerConnectionTimeoutError(
                    attempts=attempts,
                    elapsed=time.time() - start_time,
                    interval=wait_fixed,
                    expected_peers=min_peers,
                    actual_peers=peer_count,
                )
            return peer_count

        return _wait_for_peers()


class TestingRPC(BaseRPC):
    """
    RPC class for the testing namespace, providing access to
    testing-only methods like ``testing_buildBlockV1``.
    """

    def build_block(
        self,
        parent_block_hash: Hash,
        payload_attributes: PayloadAttributes,
        transactions: Sequence[TransactionProtocol] | None,
        extra_data: Bytes | None = None,
        *,
        version: int = 1,
    ) -> GetPayloadResponse:
        """
        Build a block on top of *parent_block_hash* using the
        provided *payload_attributes* and *transactions*.

        Calls ``testing_buildBlockVX``.
        """
        method = f"buildBlockV{version}"
        params: List[Any] = [
            str(parent_block_hash),
            to_json(payload_attributes),
        ]
        if transactions is not None:
            params.append([tx.rlp().hex() for tx in transactions])
        else:
            params.append(None)
        if extra_data is not None:
            params.append(str(extra_data))

        return GetPayloadResponse.model_validate(
            self.post_request(
                request=RPCCall(method=method, params=params)
            ).result_or_raise(),
            context=self.response_validation_context,
        )


class AdminRPC(BaseRPC):
    """Represents an admin RPC class for administrative RPC calls."""

    def add_peer(self, enode: str) -> bool:
        """`admin_addPeer`: Add a peer by enode URL."""
        return self.post_request(
            request=RPCCall(method="addPeer", params=[enode])
        ).result_or_raise()
