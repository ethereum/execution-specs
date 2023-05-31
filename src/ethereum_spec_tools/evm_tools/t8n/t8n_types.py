"""
Define the types used by the t8n tool.
"""
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Tuple

from ethereum import rlp
from ethereum.base_types import Bytes
from ethereum.utils.hexadecimal import hex_to_bytes, hex_to_u256, hex_to_uint

from ..fixture_loader import UnsupportedTx
from ..utils import FatalException, secp256k1_sign


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

        state = t8n.json_to_state(data)
        if t8n.fork_module == "dao_fork":
            t8n.fork.apply_dao(state)

        self.state = state

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
                account_data["code"] = "0x" + account.code.hex()

            if address in self.state._storage_tries:
                account_data["storage"] = {
                    "0x" + k.hex(): hex(v)
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
    successful_txs: List[Any]
    successful_receipts: List[Any]
    all_txs: List[Any]
    t8n: Any
    data: Any
    rlp_input: bool

    def __init__(self, t8n: Any, stdin: Optional[Dict] = None):
        self.t8n = t8n
        self.rejected_txs = {}
        self.successful_txs = []
        self.successful_receipts = []
        self.rlp_input = False
        self.all_txs = []

        if t8n.options.input_txs == "stdin":
            assert stdin is not None
            self.data = stdin["txs"]
            if self.data is None:
                self.data = []
        else:
            if t8n.options.input_txs.endswith(".rlp"):
                self.rlp_input = True
            with open(t8n.options.input_txs, "r") as f:
                self.data = json.load(f)

    @property
    def transactions(self) -> Iterator[Tuple[int, Any]]:
        """
        Read the transactions file and return a list of transactions.
        Can read from JSON or RLP.
        """
        if self.rlp_input:
            return self.parse_rlp_tx()
        else:
            return self.parse_json_tx()

    def parse_rlp_tx(self) -> Iterator[Tuple[int, Any]]:
        """
        Read transactions from RLP.
        """
        t8n = self.t8n

        txs = rlp.decode(hex_to_bytes(self.data))
        for idx, tx in enumerate(txs):
            tx_rlp = rlp.encode(tx)
            if t8n.is_after_fork("ethereum.berlin"):
                if isinstance(tx, Bytes):
                    transaction = t8n.fork_types.decode_transaction(tx)
                    self.all_txs.append(tx)
                else:
                    transaction = rlp.decode_to(
                        t8n.fork_types.LegacyTransaction, tx_rlp
                    )
                    self.all_txs.append(transaction)
            else:
                transaction = rlp.decode_to(t8n.fork_types.Transaction, tx_rlp)
                self.all_txs.append(transaction)

            yield idx, transaction

    def parse_json_tx(self) -> Iterator[Tuple[int, Any]]:
        """
        Read the transactions from json.
        If a transaction is unsigned but has a `secretKey` field, the
        transaction will be signed.
        """
        t8n = self.t8n

        for idx, json_tx in enumerate(self.data):
            json_tx["gasLimit"] = json_tx["gas"]
            json_tx["data"] = json_tx["input"]
            if "to" not in json_tx:
                json_tx["to"] = ""

            # tf tool might provide None instead of 0
            # for v, r, s
            json_tx["v"] = json_tx.get("v") or "0x00"
            json_tx["r"] = json_tx.get("r") or "0x00"
            json_tx["s"] = json_tx.get("s") or "0x00"

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

            except UnsupportedTx as e:
                t8n.logger.warning(
                    f"Unsupported transaction type {idx}: {e.error_message}"
                )
                self.rejected_txs[
                    idx
                ] = f"Unsupported transaction type: {e.error_message}"
                self.all_txs.append(e.encoded_params)
                continue
            else:
                self.all_txs.append(tx)

            if t8n.is_after_fork("ethereum.berlin"):
                transaction = t8n.fork_types.decode_transaction(tx)
            else:
                transaction = tx

            yield idx, transaction

    def add_transaction(self, tx: Any) -> None:
        """
        Add a transaction to the list of successful transactions.
        """
        if self.t8n.is_after_fork("ethereum.berlin"):
            self.successful_txs.append(
                self.t8n.fork_types.encode_transaction(tx)
            )
        else:
            self.successful_txs.append(tx)

    def add_receipt(self, tx: Any) -> None:
        """
        Add t8n receipt info for valid tx
        """
        data = {"transactionHash": "hash", "blockHash": "hash", "gasUsed": 0}
        self.successful_receipts.append(data)

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
    withdrawals_root: Any = None
    logs_hash: Any = None
    bloom: Any = None
    receipts: Any = None
    rejected: Any = None
    gas_used: Any = None

    def to_json(self) -> Any:
        """Encode the result to JSON"""
        data = {}

        data["stateRoot"] = "0x" + self.state_root.hex()
        data["txRoot"] = "0x" + self.tx_root.hex()
        data["receiptsRoot"] = "0x" + self.receipt_root.hex()
        if self.withdrawals_root:
            data["withdrawalsRoot"] = "0x" + self.withdrawals_root.hex()
        data["logsHash"] = "0x" + self.logs_hash.hex()
        data["logsBloom"] = "0x" + self.bloom.hex()
        data["gasUsed"] = hex(self.gas_used)
        if self.difficulty:
            data["currentDifficulty"] = hex(self.difficulty)
        else:
            data["currentDifficulty"] = None

        if self.base_fee:
            data["currentBaseFee"] = hex(self.base_fee)
        else:
            data["currentBaseFee"] = None

        data["rejected"] = [
            {"index": idx, "error": error}
            for idx, error in self.rejected.items()
        ]

        data["receipts"] = [
            {
                "transactionHash": item["transactionHash"],
                "blockHash": item["blockHash"],
                "gasUsed": item["gasUsed"],
            }
            for item in self.receipts
        ]

        return data
