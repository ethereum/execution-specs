"""
Define the types used by the t8n tool.
"""
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Tuple

from ethereum import rlp
from ethereum.base_types import U256, Uint
from ethereum.crypto.hash import keccak256
from ethereum.utils.hexadecimal import (
    Hash32,
    hex_to_bytes,
    hex_to_u256,
    hex_to_uint,
)

from ..utils import FatalException, parse_hex_or_int, secp256k1_sign


@dataclass
class Ommer:
    """The Ommer type for the t8n tool."""

    delta: str
    address: Any


class Env:
    """
    The environment for the transition tool.
    """

    coinbase: Any
    block_gas_limit: Uint
    block_number: Uint
    block_timestamp: U256
    # TODO: Add Withdrawals for Shanghai
    block_difficulty: Optional[Uint]
    # TODO: Add Randao for Paris
    parent_difficulty: Optional[Uint]
    parent_timestamp: Optional[U256]
    base_fee_per_gas: Optional[Uint]
    # TODO: Check if base fee needs to be derived from parent gas
    # used and gas limit
    # parent_gas_used: Optional[Uint]
    # parent_gas_limit: Optional[Uint]
    block_hashes: Optional[List[Any]]
    parent_ommers_hash: Optional[Hash32]
    ommers: Any

    def __init__(self, t8n: Any, stdin: Optional[Dict] = None):
        if t8n.options.input_env == "stdin":
            assert stdin is not None
            data = stdin["env"]
        else:
            with open(t8n.options.input_env, "r") as f:
                data = json.load(f)

        self.coinbase = t8n.hex_to_address(data["currentCoinbase"])
        self.block_gas_limit = parse_hex_or_int(data["currentGasLimit"], Uint)
        self.block_number = parse_hex_or_int(data["currentNumber"], Uint)
        self.block_timestamp = parse_hex_or_int(data["currentTimestamp"], U256)

        self.read_block_difficulty(data, t8n)

        if t8n.is_after_fork("ethereum.london"):
            self.base_fee_per_gas = parse_hex_or_int(
                data["currentBaseFee"], Uint
            )
        else:
            self.base_fee_per_gas = None
        # TODO: Check if base fee needs to be derived from parent gas
        # used and gas limit

        self.read_block_hashes(data)
        self.read_ommers(data, t8n)

    def read_block_difficulty(self, data: Any, t8n: Any) -> None:
        """
        Read the block difficulty from the data.
        If `currentDifficulty` is present, it is used. Otherwise,
        the difficulty is calculated from the parent block.
        """
        if "currentDifficulty" in data:
            self.block_difficulty = parse_hex_or_int(
                data["currentDifficulty"], Uint
            )
            self.parent_timestamp = None
            self.parent_difficulty = None
            self.parent_ommers_hash = None
        else:
            self.parent_timestamp = parse_hex_or_int(
                data["parentTimestamp"], U256
            )
            self.parent_difficulty = parse_hex_or_int(
                data["parentDifficulty"], Uint
            )
            args = [
                self.block_number,
                self.block_timestamp,
                self.parent_timestamp,
                self.parent_difficulty,
            ]
            if t8n.is_after_fork("ethereum.byzantium"):
                if "parentUncleHash" in data:
                    EMPTY_OMMER_HASH = keccak256(rlp.encode([]))
                    self.parent_ommers_hash = Hash32(
                        hex_to_bytes(data["parentUncleHash"])
                    )
                    parent_has_ommers = (
                        self.parent_ommers_hash != EMPTY_OMMER_HASH
                    )
                    args.append(parent_has_ommers)
                else:
                    args.append(False)
            self.block_difficulty = t8n.fork.calculate_block_difficulty(*args)

    def read_block_hashes(self, data: Any) -> None:
        """
        Read the block hashes. Returns a maximum of 256 block hashes.
        """
        # Read the block hashes
        block_hashes: List[Any] = []
        # Store a maximum of 256 block hashes.
        max_blockhash_count = min(256, self.block_number)
        for number in range(
            self.block_number - max_blockhash_count, self.block_number
        ):
            if "blockHashes" in data and str(number) in data["blockHashes"]:
                block_hashes.append(
                    Hash32(hex_to_bytes(data["blockHashes"][str(number)]))
                )
            else:
                block_hashes.append(None)

        self.block_hashes = block_hashes

    def read_ommers(self, data: Any, t8n: Any) -> None:
        """
        Read the ommers. The ommers data might not have all the details
        needed to obtain the Header.
        """
        ommers = []
        if "ommers" in data:
            for ommer in data["ommers"]:
                ommers.append(
                    Ommer(
                        ommer["delta"],
                        t8n.hex_to_address(ommer["address"]),
                    )
                )
        self.ommers = ommers


class Alloc:
    """
    The alloc (state) type for the t8n tool.
    """

    state: Any
    state_backup: Any

    def __init__(self, t8n: Any, stdin: Optional[Dict] = None):
        """Read the alloc file and return the state."""
        if t8n.options.input_alloc == "stdin":
            assert stdin is not None
            data = stdin["alloc"]
        else:
            with open(t8n.options.input_alloc, "r") as f:
                data = json.load(f)

        # The json_to_state functions expects the values to hex
        # strings, so we convert them here.
        for address, account in data.items():
            for key, value in account.items():
                if key == "storage":
                    continue
                elif not value.startswith("0x"):
                    data[address][key] = "0x" + hex(int(value))

        self.state = t8n.json_to_state(data)

    def to_json(self) -> Any:
        """Encode the state to JSON"""
        data = {}
        for address, account in self.state._main_trie._data.items():

            account_data: Dict[str, Any] = {}

            if account.balance:
                account_data["balance"] = hex(account.balance)

            if account.nonce:
                account_data["nonce"] = hex(account.nonce)

            if account.code:
                account_data["code"] = account.code.hex()

            if address in self.state._storage_tries:
                account_data["storage"] = {
                    k.hex(): hex(v)
                    for k, v in self.state._storage_tries[
                        address
                    ]._data.items()
                }

            data["0x" + address.hex()] = account_data

        return data


class Txs:
    """
    Read the transactions file, sort out the valid transactions and
    return a list of transactions.
    """

    rejected_txs: Dict[int, str]
    t8n: Any
    data: Any

    def __init__(self, t8n: Any, stdin: Optional[Dict] = None):
        self.t8n = t8n
        self.rejected_txs = {}
        # TODO: Add support for reading RLP

        if t8n.options.input_txs == "stdin":
            assert stdin is not None
            self.data = stdin["txs"]
        else:
            with open(t8n.options.input_txs, "r") as f:
                self.data = json.load(f)

    @property
    def transactions(self) -> Iterator[Tuple[int, Any]]:
        """
        Read the transactions file and return a list of transactions.
        If a transaction is unsigned but has a `secretKey` field, the
        transaction will be signed.
        """
        t8n = self.t8n

        for idx, json_tx in enumerate(self.data):
            json_tx["gasLimit"] = json_tx["gas"]
            json_tx["data"] = json_tx["input"]
            if "to" not in json_tx:
                json_tx["to"] = ""

            v = hex_to_u256(json_tx["v"])
            r = hex_to_u256(json_tx["r"])
            s = hex_to_u256(json_tx["s"])

            if "secretKey" in json_tx and v == r == s == 0:
                try:
                    self.sign_transaction(json_tx)
                except Exception as e:
                    # A fatal exception is only raised if an
                    # unsupported transaction type is attempted to be
                    # signed. If a signed unsupported transaction is
                    # provided, it will simply be rejected and the
                    # next transaction is attempted.
                    # See: https://github.com/ethereum/go-ethereum/issues/26861
                    t8n.logger.error(f"Rejected transaction {idx}")
                    raise FatalException(e)

            try:
                tx = t8n.json_to_tx(json_tx)

            except Exception as e:
                t8n.logger.warning(f"Rejected transaction {idx}: {e}")
                self.rejected_txs[idx] = str(e)
                continue

            if t8n.is_after_fork("ethereum.berlin"):
                transaction = t8n.fork_types.decode_transaction(tx)
            else:
                transaction = tx

            yield idx, transaction

    def sign_transaction(self, json_tx: Any) -> None:
        """
        Sign a transaction. This function will be invoked if a `secretKey`
        is provided in the transaction.
        Post spurious dragon, the transaction is signed according to EIP-155
        if the protected flag is missing or set to true.
        """
        t8n = self.t8n
        protected = json_tx.get("protected", True)

        tx = t8n.json_to_tx(json_tx)

        if isinstance(tx, bytes):
            tx_decoded = t8n.fork_types.decode_transaction(tx)
        else:
            tx_decoded = tx

        secret_key = hex_to_uint(json_tx["secretKey"][2:])
        if t8n.is_after_fork("ethereum.berlin"):
            Transaction = t8n.fork_types.LegacyTransaction
        else:
            Transaction = t8n.fork_types.Transaction

        if isinstance(tx_decoded, Transaction):
            if t8n.is_after_fork("ethereum.spurious_dragon"):
                if protected:
                    signing_hash = t8n.fork.signing_hash_155(tx_decoded)
                    v_addend = 37  # Assuming chain_id = 1
                else:
                    signing_hash = t8n.fork.signing_hash_pre155(tx_decoded)
                    v_addend = 27
            else:
                signing_hash = t8n.fork.signing_hash(tx_decoded)
                v_addend = 27
        elif isinstance(tx_decoded, t8n.fork_types.AccessListTransaction):
            signing_hash = t8n.fork.signing_hash_2930(tx_decoded)
            v_addend = 0
        elif isinstance(tx_decoded, t8n.fork_types.FeeMarketTransaction):
            signing_hash = t8n.fork.signing_hash_1559(tx_decoded)
            v_addend = 0
        else:
            raise FatalException("Unknown transaction type")

        r, s, y = secp256k1_sign(signing_hash, secret_key)
        json_tx["r"] = hex(r)
        json_tx["s"] = hex(s)
        json_tx["v"] = hex(y + v_addend)


@dataclass
class Result:
    """Type that represents the result of a transition execution"""

    difficulty: Any
    base_fee: Any
    state_root: Any = None
    tx_root: Any = None
    receipt_root: Any = None
    logs_hash: Any = None
    bloom: Any = None
    # TODO: Add receipts to result
    rejected: Any = None
    gas_used: Any = None

    def to_json(self) -> Any:
        """Encode the result to JSON"""
        data = {}

        data["stateRoot"] = "0x" + self.state_root.hex()
        data["txRoot"] = "0x" + self.tx_root.hex()
        data["receiptsRoot"] = "0x" + self.receipt_root.hex()
        data["logsHash"] = "0x" + self.logs_hash.hex()
        data["logsBloom"] = "0x" + self.bloom.hex()
        data["gasUsed"] = hex(self.gas_used)
        data["currentDifficulty"] = hex(self.difficulty)

        data["rejected"] = [
            {"index": idx, "error": error}
            for idx, error in self.rejected.items()
        ]

        return data
