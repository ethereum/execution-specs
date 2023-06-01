import json
from dataclasses import dataclass
from ethereum import rlp
from typing import Any, Dict, Iterator, List, Optional, Tuple
from ethereum.base_types import U256, Bytes, Bytes32, Uint
from ethereum.crypto.hash import Hash32, keccak256
from ethereum.utils.byte import left_pad_zero_bytes
from ..utils import FatalException, parse_hex_or_int, secp256k1_sign
from ethereum.utils.hexadecimal import hex_to_bytes, hex_to_u256, hex_to_uint

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
    withdrawals: Any
    block_difficulty: Optional[Uint]
    prev_randao: Optional[Bytes32]
    parent_difficulty: Optional[Uint]
    parent_timestamp: Optional[U256]
    base_fee_per_gas: Optional[Uint]
    parent_gas_used: Optional[Uint]
    parent_gas_limit: Optional[Uint]
    parent_base_fee_per_gas: Optional[Uint]
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
        self.read_base_fee_per_gas(data, t8n)
        self.read_randao(data, t8n)
        self.read_block_hashes(data)
        self.read_ommers(data, t8n)
        self.read_withdrawals(data, t8n)

    def read_base_fee_per_gas(self, data: Any, t8n: Any) -> None:
        """
        Read the base_fee_per_gas from the data. If the base fee is
        not present, it is calculated from the parent block parameters.
        """
        self.parent_gas_used = None
        self.parent_gas_limit = None
        self.parent_base_fee_per_gas = None
        self.base_fee_per_gas = None

        if t8n.is_after_fork("ethereum.london"):
            if "currentBaseFee" in data:
                self.base_fee_per_gas = parse_hex_or_int(
                    data["currentBaseFee"], Uint
                )
            else:
                self.parent_gas_used = parse_hex_or_int(
                    data["parentGasUsed"], Uint
                )
                self.parent_gas_limit = parse_hex_or_int(
                    data["parentGasLimit"], Uint
                )
                self.parent_base_fee_per_gas = parse_hex_or_int(
                    data["parentBaseFee"], Uint
                )
                parameters = [
                    self.block_gas_limit,
                    self.parent_gas_limit,
                    self.parent_gas_used,
                    self.parent_base_fee_per_gas,
                ]

                # TODO: See if this explicit check can be removed. See
                # https://github.com/ethereum/execution-specs/issues/740
                if t8n.fork_module == "london":
                    parameters.append(t8n.fork_block == self.block_number)

                self.base_fee_per_gas = t8n.fork.calculate_base_fee_per_gas(
                    *parameters
                )

    def read_randao(self, data: Any, t8n: Any) -> None:
        """
        Read the randao from the data.
        """
        self.prev_randao = None
        if t8n.is_after_fork("ethereum.paris"):
            # tf tool might not always provide an
            # even number of nibbles in the randao
            # This could create issues in the
            # hex_to_bytes function
            current_random = data["currentRandom"]
            if current_random.startswith("0x"):
                current_random = current_random[2:]

            if len(current_random) % 2 == 1:
                current_random = "0" + current_random

            self.prev_randao = Bytes32(
                left_pad_zero_bytes(hex_to_bytes(current_random), 32)
            )

    def read_withdrawals(self, data: Any, t8n: Any) -> None:
        """
        Read the withdrawals from the data.
        """
        self.withdrawals = None
        if t8n.is_after_fork("ethereum.shanghai"):
            self.withdrawals = tuple(
                t8n.json_to_withdrawals(wd) for wd in data["withdrawals"]
            )

    def read_block_difficulty(self, data: Any, t8n: Any) -> None:
        """
        Read the block difficulty from the data.
        If `currentDifficulty` is present, it is used. Otherwise,
        the difficulty is calculated from the parent block.
        """
        self.block_difficulty = None
        self.parent_timestamp = None
        self.parent_difficulty = None
        self.parent_ommers_hash = None
        if t8n.is_after_fork("ethereum.paris"):
            return
        elif "currentDifficulty" in data:
            self.block_difficulty = parse_hex_or_int(
                data["currentDifficulty"], Uint
            )
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
