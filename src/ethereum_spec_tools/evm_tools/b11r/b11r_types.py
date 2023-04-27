import json
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Tuple

from ethereum import rlp
from ethereum.base_types import U256, U64, Bytes32, Uint, Bytes20, Bytes256, Bytes, Bytes8
from ethereum.crypto.hash import Hash32, keccak256
from ethereum.utils.byte import left_pad_zero_bytes
from ethereum.utils.hexadecimal import hex_to_bytes, hex_to_u256, hex_to_uint

from ..utils import FatalException, parse_hex_or_int, secp256k1_sign

class Header:
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

    def __init__(self, options, body):
        with open(options.input_header) as f:
            data = json.load(f)

        self.parent_hash = Hash32(hex_to_bytes(data["parentHash"]))
        try:
            self.ommers_hash = Hash32(hex_to_bytes(data["ommersHash"]))
        except KeyError:
            self.ommers_hash = keccak256(rlp.encode(body.ommers))

        self.coinbase = Bytes20(hex_to_bytes(data.get("miner", "0x0000000000000000000000000000000000000000")))
        self.state_root = Hash32(hex_to_bytes(data["stateRoot"]))
        self.transactions_root = Hash32(hex_to_bytes(data.get("transactionsRoot", "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421")))
        self.receipt_root = Hash32(hex_to_bytes(data.get("receiptsRoot", "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421")))
        self.bloom = Bytes256(hex_to_bytes(data["logsBloom"]))
        self.difficulty = parse_hex_or_int(data.get("difficulty", 0), Uint)
        self.number = parse_hex_or_int(data["number"], Uint)
        self.gas_limit = parse_hex_or_int(data["gasLimit"], Uint)
        self.gas_used = parse_hex_or_int(data["gasUsed"], Uint)
        self.timestamp = parse_hex_or_int(data["timestamp"], U256)
        self.extra_data = hex_to_bytes(data.get("extraData", "0x"))
        self.mix_digest = Bytes32(hex_to_bytes(data["mixHash"]))
        self.nonce = hex_to_bytes(data.get("nonce", "0x0000000000000000"))
        
        try:
            self.base_fee_per_gas = parse_hex_or_int(data["baseFeePerGas"], Uint)
        except KeyError:
            self.base_fee_per_gas = None

        try:
            self.withdrawals_root = Hash32(hex_to_bytes(data["withdrawalsRoot"]))
            # Cannot have wirhdrawal root but no base fee
            if self.base_fee_per_gas is None:
                self.base_fee_per_gas = Uint(0)
        except KeyError:
            self.withdrawals_root = None



class Body:

    transactions: List
    ommers: List
    withdrawals: List

    def __init__(self, options):
        # Parse transactions
        with open(options.input_txs) as f:
            txs_data = json.load(f)

        self.transactions = rlp.decode(hex_to_bytes(txs_data))

        # Parse ommers
        with open(options.input_ommers) as f:
            ommers_data = json.load(f)

        self.ommers = []
        for ommer in ommers_data:
            decoded_ommer = rlp.decode(hex_to_bytes(ommer))
            self.ommers.append(decoded_ommer[0]) # ommer[0] is the header

        # Parse withdrawals
        if options.input_withdrawals is None:
            self.withdrawals = []
            return

        with open(options.input_withdrawals) as f:
            withdrawals_data = json.load(f)

        self.withdrawals = []
        for wd in withdrawals_data:
            self.withdrawals.append(
                [
                    parse_hex_or_int(wd["index"], U64),
                    parse_hex_or_int(wd["validatorIndex"], U64),
                    Bytes20(hex_to_bytes(wd["address"])),
                    parse_hex_or_int(wd["amount"], Uint),
                ]
            )