"""
Define the types used by the b11r tool.
"""
import json
from typing import Any, List, Optional, Tuple

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes8, Bytes20, Bytes32, Bytes256
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.utils.hexadecimal import hex_to_bytes, hex_to_bytes8

from ..utils import parse_hex_or_int

DEFAULT_TRIE_ROOT = (
    "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
)
DEFAULT_COINBASE = "0x0000000000000000000000000000000000000000"


class Body:
    """
    A class representing a block body.
    """

    transactions: rlp.Extended
    ommers: rlp.Extended
    withdrawals: Optional[List[Tuple[U64, U64, Bytes20, Uint]]]

    def __init__(self, options: Any, stdin: Any = None):
        # Parse transactions
        if options.input_txs == "stdin":
            assert stdin is not None
            txs_data = stdin["txs"]
        else:
            with open(options.input_txs) as f:
                txs_data = json.load(f)

        # The tf tool inputs "" when there are no transactions
        if txs_data == "":
            self.transactions = []
        else:
            self.transactions = rlp.decode(hex_to_bytes(txs_data))

        # Parse ommers
        if options.input_ommers == "stdin":
            assert stdin is not None
            # The tests use "ommers" whereas the tf tool uses "uncles"
            try:
                ommers_data = stdin["ommers"]
            except KeyError:
                ommers_data = stdin["uncles"]
        else:
            with open(options.input_ommers) as f:
                ommers_data = json.load(f)

        self.ommers = []
        for ommer in ommers_data:
            decoded_ommer = rlp.decode(hex_to_bytes(ommer))
            assert not isinstance(decoded_ommer, bytes)
            self.ommers.append(decoded_ommer[0])  # ommer[0] is the header

        # Parse withdrawals
        if options.input_withdrawals is None:
            self.withdrawals = None
            return

        if options.input_withdrawals == "stdin":
            assert stdin is not None
            # The tf tool does not pass empty list when there
            # are no withdrawals.
            withdrawals_data = stdin.get("withdrawals", [])
        else:
            with open(options.input_withdrawals) as f:
                withdrawals_data = json.load(f)

        self.withdrawals = []
        for wd in withdrawals_data:
            self.withdrawals.append(
                (
                    parse_hex_or_int(wd["index"], U64),
                    parse_hex_or_int(wd["validatorIndex"], U64),
                    Bytes20(hex_to_bytes(wd["address"])),
                    parse_hex_or_int(wd["amount"], Uint),
                )
            )


class Header:
    """
    A class representing a block header.
    """

    parent_hash: Hash32
    ommers_hash: Hash32
    coinbase: Bytes20
    state_root: Hash32
    transactions_root: Hash32
    receipt_root: Hash32
    bloom: Bytes256
    difficulty: Uint
    number: Uint
    gas_limit: Uint
    gas_used: Uint
    timestamp: U256
    extra_data: Bytes
    mix_digest: Bytes32
    nonce: Bytes8
    base_fee_per_gas: Optional[Uint]
    withdrawals_root: Optional[Hash32]

    def __init__(self, options: Any, body: Body, stdin: Any = None):
        if options.input_header == "stdin":
            assert stdin is not None
            data = stdin["header"]
        else:
            with open(options.input_header) as f:
                data = json.load(f)

        self.parent_hash = Hash32(hex_to_bytes(data["parentHash"]))
        try:
            self.ommers_hash = Hash32(hex_to_bytes(data["ommersHash"]))
        except KeyError:
            self.ommers_hash = keccak256(rlp.encode(body.ommers))

        self.coinbase = Bytes20(
            hex_to_bytes(data.get("miner", DEFAULT_COINBASE))
        )
        self.state_root = Hash32(hex_to_bytes(data["stateRoot"]))
        self.transactions_root = Hash32(
            hex_to_bytes(
                data.get(
                    "transactionsRoot",
                    DEFAULT_TRIE_ROOT,
                )
            )
        )
        self.receipt_root = Hash32(
            hex_to_bytes(
                data.get(
                    "receiptsRoot",
                    DEFAULT_TRIE_ROOT,
                )
            )
        )
        self.bloom = Bytes256(hex_to_bytes(data["logsBloom"]))
        self.difficulty = parse_hex_or_int(data.get("difficulty", 0), Uint)
        self.number = parse_hex_or_int(data["number"], Uint)
        self.gas_limit = parse_hex_or_int(data["gasLimit"], Uint)
        self.gas_used = parse_hex_or_int(data["gasUsed"], Uint)
        self.timestamp = parse_hex_or_int(data["timestamp"], U256)
        self.extra_data = hex_to_bytes(data.get("extraData", "0x"))
        self.mix_digest = Bytes32(hex_to_bytes(data["mixHash"]))
        self.nonce = hex_to_bytes8(data.get("nonce", "0x0000000000000000"))

        try:
            self.base_fee_per_gas = parse_hex_or_int(
                data["baseFeePerGas"], Uint
            )
        except KeyError:
            self.base_fee_per_gas = None

        try:
            self.withdrawals_root = Hash32(
                hex_to_bytes(data["withdrawalsRoot"])
            )
            # Cannot have withdrawal root but no base fee
            if self.base_fee_per_gas is None:
                self.base_fee_per_gas = Uint(0)
        except KeyError:
            self.withdrawals_root = None
