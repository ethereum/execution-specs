"""
Define the types used by the t8n tool.
"""
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from ethereum_rlp import Simple, rlp
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.utils.hexadecimal import hex_to_bytes, hex_to_u256, hex_to_uint

from ..loaders.transaction_loader import TransactionLoad, UnsupportedTx
from ..utils import FatalException, encode_to_hex, secp256k1_sign

if TYPE_CHECKING:
    from . import T8N


class Alloc:
    """
    The alloc (state) type for the t8n tool.
    """

    state: Any
    state_backup: Any

    def __init__(self, t8n: "T8N", stdin: Optional[Dict] = None):
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
                if key == "storage" or not value:
                    continue
                elif not value.startswith("0x"):
                    data[address][key] = "0x" + hex(int(value))

        state = t8n.json_to_state(data)
        if t8n.fork.fork_module == "dao_fork":
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

    def __init__(self, t8n: "T8N", stdin: Optional[Dict] = None):
        self.t8n = t8n
        self.successfully_parsed: List[int] = []
        self.transactions: List[Tuple[Uint, Any]] = []
        self.rejected_txs = {}
        self.rlp_input = False
        self.all_txs = []

        if t8n.options.input_txs == "stdin":
            assert stdin is not None
            data = stdin["txs"]
        else:
            with open(t8n.options.input_txs, "r") as f:
                data = json.load(f)

        if data is None:
            self.data: Simple = []
        elif isinstance(data, str):
            self.rlp_input = True
            self.data = rlp.decode(hex_to_bytes(data))
        else:
            self.data = data

        for idx, raw_tx in enumerate(self.data):
            try:
                if self.rlp_input:
                    self.transactions.append(self.parse_rlp_tx(raw_tx))
                    self.successfully_parsed.append(idx)
                else:
                    self.transactions.append(self.parse_json_tx(raw_tx))
                    self.successfully_parsed.append(idx)
            except UnsupportedTx as e:
                self.t8n.logger.warning(
                    f"Unsupported transaction type {idx}: "
                    f"{e.error_message}"
                )
                self.rejected_txs[
                    idx
                ] = f"Unsupported transaction type: {e.error_message}"
                self.all_txs.append(e.encoded_params)
            except Exception as e:
                msg = f"Failed to parse transaction {idx}: {str(e)}"
                self.t8n.logger.warning(msg, exc_info=e)
                self.rejected_txs[idx] = msg

    def parse_rlp_tx(self, raw_tx: Any) -> Any:
        """
        Read transactions from RLP.
        """
        t8n = self.t8n

        tx_rlp = rlp.encode(raw_tx)
        if t8n.fork.is_after_fork("ethereum.berlin"):
            if isinstance(raw_tx, Bytes):
                transaction = t8n.fork.decode_transaction(raw_tx)
                self.all_txs.append(raw_tx)
            else:
                transaction = rlp.decode_to(t8n.fork.LegacyTransaction, tx_rlp)
                self.all_txs.append(transaction)
        else:
            transaction = rlp.decode_to(t8n.fork.Transaction, tx_rlp)
            self.all_txs.append(transaction)

        return transaction

    def parse_json_tx(self, raw_tx: Any) -> Any:
        """
        Read the transactions from json.
        If a transaction is unsigned but has a `secretKey` field, the
        transaction will be signed.
        """
        t8n = self.t8n

        # for idx, json_tx in enumerate(self.data):
        raw_tx["gasLimit"] = raw_tx["gas"]
        raw_tx["data"] = raw_tx["input"]
        if "to" not in raw_tx or raw_tx["to"] is None:
            raw_tx["to"] = ""

        # tf tool might provide None instead of 0
        # for v, r, s
        raw_tx["v"] = raw_tx.get("v") or raw_tx.get("y_parity") or "0x00"
        raw_tx["r"] = raw_tx.get("r") or "0x00"
        raw_tx["s"] = raw_tx.get("s") or "0x00"

        v = hex_to_u256(raw_tx["v"])
        r = hex_to_u256(raw_tx["r"])
        s = hex_to_u256(raw_tx["s"])

        if "secretKey" in raw_tx and v == r == s == 0:
            self.sign_transaction(raw_tx)

        tx = TransactionLoad(raw_tx, t8n.fork).read()
        self.all_txs.append(tx)

        if t8n.fork.is_after_fork("ethereum.berlin"):
            transaction = t8n.fork.decode_transaction(tx)
        else:
            transaction = tx

        return transaction

    def sign_transaction(self, json_tx: Any) -> None:
        """
        Sign a transaction. This function will be invoked if a `secretKey`
        is provided in the transaction.
        Post spurious dragon, the transaction is signed according to EIP-155
        if the protected flag is missing or set to true.
        """
        t8n = self.t8n
        protected = json_tx.get("protected", True)

        tx = TransactionLoad(json_tx, t8n.fork).read()

        if isinstance(tx, bytes):
            tx_decoded = t8n.fork.decode_transaction(tx)
        else:
            tx_decoded = tx

        secret_key = hex_to_uint(json_tx["secretKey"][2:])
        if t8n.fork.is_after_fork("ethereum.berlin"):
            Transaction = t8n.fork.LegacyTransaction
        else:
            Transaction = t8n.fork.Transaction

        v_addend: U256
        if isinstance(tx_decoded, Transaction):
            if t8n.fork.is_after_fork("ethereum.spurious_dragon"):
                if protected:
                    signing_hash = t8n.fork.signing_hash_155(
                        tx_decoded, U64(1)
                    )
                    v_addend = U256(37)  # Assuming chain_id = 1
                else:
                    signing_hash = t8n.fork.signing_hash_pre155(tx_decoded)
                    v_addend = U256(27)
            else:
                signing_hash = t8n.fork.signing_hash(tx_decoded)
                v_addend = U256(27)
        elif isinstance(tx_decoded, t8n.fork.AccessListTransaction):
            signing_hash = t8n.fork.signing_hash_2930(tx_decoded)
            v_addend = U256(0)
        elif isinstance(tx_decoded, t8n.fork.FeeMarketTransaction):
            signing_hash = t8n.fork.signing_hash_1559(tx_decoded)
            v_addend = U256(0)
        elif isinstance(tx_decoded, t8n.fork.BlobTransaction):
            signing_hash = t8n.fork.signing_hash_4844(tx_decoded)
            v_addend = U256(0)
        elif isinstance(tx_decoded, t8n.fork.SetCodeTransaction):
            signing_hash = t8n.fork.signing_hash_7702(tx_decoded)
            v_addend = U256(0)
        else:
            raise FatalException("Unknown transaction type")

        r, s, y = secp256k1_sign(signing_hash, int(secret_key))
        json_tx["r"] = hex(r)
        json_tx["s"] = hex(s)
        json_tx["v"] = hex(y + v_addend)

        if v_addend == 0:
            json_tx["y_parity"] = json_tx["v"]


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
    excess_blob_gas: Optional[U64] = None
    blob_gas_used: Optional[Uint] = None
    requests_hash: Optional[Hash32] = None
    requests: Optional[List[Bytes]] = None

    def get_receipts_from_tries(
        self, t8n: Any, tx_trie: Any, receipts_trie: Any
    ) -> List[Any]:
        """
        Get receipts from the transaction and receipts tries.
        """
        receipts: List[Any] = []
        for index in tx_trie._data:
            if index not in receipts_trie._data:
                # Meaning the transaction has somehow failed
                return receipts

            tx = tx_trie._data.get(index)
            tx_hash = t8n.fork.get_transaction_hash(tx)

            receipt = receipts_trie._data.get(index)

            if hasattr(t8n.fork, "decode_receipt"):
                decoded_receipt = t8n.fork.decode_receipt(receipt)
            else:
                decoded_receipt = receipt

            gas_consumed = decoded_receipt.cumulative_gas_used

            receipts.append(
                {
                    "transactionHash": "0x" + tx_hash.hex(),
                    "gasUsed": hex(gas_consumed),
                }
            )

        return receipts

    def update(self, t8n: "T8N", block_env: Any, block_output: Any) -> None:
        """
        Update the result after processing the inputs.
        """
        self.gas_used = block_output.block_gas_used
        self.tx_root = t8n.fork.root(block_output.transactions_trie)
        self.receipt_root = t8n.fork.root(block_output.receipts_trie)
        self.bloom = t8n.fork.logs_bloom(block_output.block_logs)
        self.logs_hash = keccak256(rlp.encode(block_output.block_logs))
        self.state_root = t8n.fork.state_root(block_env.state)
        self.receipts = self.get_receipts_from_tries(
            t8n, block_output.transactions_trie, block_output.receipts_trie
        )

        if hasattr(block_env, "base_fee_per_gas"):
            self.base_fee = block_env.base_fee_per_gas

        if hasattr(block_output, "withdrawals_trie"):
            self.withdrawals_root = t8n.fork.root(
                block_output.withdrawals_trie
            )

        if hasattr(block_env, "excess_blob_gas"):
            self.excess_blob_gas = block_env.excess_blob_gas

        if hasattr(block_output, "requests"):
            self.requests = block_output.requests
            self.requests_hash = t8n.fork.compute_requests_hash(self.requests)

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

        if self.excess_blob_gas is not None:
            data["currentExcessBlobGas"] = hex(self.excess_blob_gas)

        if self.blob_gas_used is not None:
            data["blobGasUsed"] = hex(self.blob_gas_used)

        data["rejected"] = [
            {"index": idx, "error": error}
            for idx, error in self.rejected.items()
        ]

        data["receipts"] = self.receipts

        if self.requests_hash is not None:
            assert self.requests is not None

            data["requestsHash"] = encode_to_hex(self.requests_hash)
            # T8N doesn't consider the request type byte to be part of the
            # request
            data["requests"] = [encode_to_hex(req) for req in self.requests]

        return data
