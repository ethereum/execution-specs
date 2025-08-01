"""
Define t8n Env class
"""
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.utils.byte import left_pad_zero_bytes
from ethereum.utils.hexadecimal import hex_to_bytes

from ..utils import parse_hex_or_int

if TYPE_CHECKING:
    from ethereum_spec_tools.evm_tools.t8n import T8N


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
    parent_hash: Any
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
    parent_beacon_block_root: Optional[Hash32]
    parent_excess_blob_gas: Optional[U64]
    parent_blob_gas_used: Optional[U64]
    excess_blob_gas: Optional[U64]
    requests: Any

    def __init__(self, t8n: "T8N", stdin: Optional[Dict] = None):
        if t8n.options.input_env == "stdin":
            assert stdin is not None
            data = stdin["env"]
        else:
            with open(t8n.options.input_env, "r") as f:
                data = json.load(f)

        self.coinbase = t8n.fork.hex_to_address(data["currentCoinbase"])
        self.block_gas_limit = parse_hex_or_int(data["currentGasLimit"], Uint)
        self.block_number = parse_hex_or_int(data["currentNumber"], Uint)
        self.block_timestamp = parse_hex_or_int(data["currentTimestamp"], U256)

        self.read_block_difficulty(data, t8n)
        self.read_base_fee_per_gas(data, t8n)
        self.read_randao(data, t8n)
        self.read_block_hashes(data, t8n)
        self.read_ommers(data, t8n)
        self.read_withdrawals(data, t8n)

        self.parent_beacon_block_root = None
        if t8n.fork.is_after_fork("ethereum.cancun"):
            if not t8n.options.state_test:
                parent_beacon_block_root_hex = data["parentBeaconBlockRoot"]
                self.parent_beacon_block_root = (
                    Bytes32(hex_to_bytes(parent_beacon_block_root_hex))
                    if parent_beacon_block_root_hex is not None
                    else None
                )
            self.read_excess_blob_gas(data, t8n)

    def read_excess_blob_gas(self, data: Any, t8n: "T8N") -> None:
        """
        Read the excess_blob_gas from the data. If the excess blob gas is
        not present, it is calculated from the parent block parameters.
        """
        self.parent_blob_gas_used = U64(0)
        self.parent_excess_blob_gas = U64(0)
        self.excess_blob_gas = None

        if not t8n.fork.is_after_fork("ethereum.cancun"):
            return

        if "currentExcessBlobGas" in data:
            self.excess_blob_gas = parse_hex_or_int(
                data["currentExcessBlobGas"], U64
            )

        if "parentExcessBlobGas" in data:
            self.parent_excess_blob_gas = parse_hex_or_int(
                data["parentExcessBlobGas"], U64
            )

        if "parentBlobGasUsed" in data:
            self.parent_blob_gas_used = parse_hex_or_int(
                data["parentBlobGasUsed"], U64
            )

        if self.excess_blob_gas is not None:
            return

        assert self.parent_excess_blob_gas is not None
        assert self.parent_blob_gas_used is not None

        parent_blob_gas = (
            self.parent_excess_blob_gas + self.parent_blob_gas_used
        )

        target_blob_gas_per_block = t8n.fork.TARGET_BLOB_GAS_PER_BLOCK

        if parent_blob_gas < target_blob_gas_per_block:
            self.excess_blob_gas = U64(0)
        else:
            self.excess_blob_gas = parent_blob_gas - target_blob_gas_per_block

            if t8n.fork.is_after_fork("ethereum.osaka"):
                # Under certain conditions specified in EIP-7918, the
                # the excess_blob_gas is calculated differently in osaka
                assert self.parent_base_fee_per_gas is not None

                GAS_PER_BLOB = t8n.fork.GAS_PER_BLOB
                BLOB_BASE_COST = t8n.fork.BLOB_BASE_COST
                BLOB_SCHEDULE_MAX = t8n.fork.BLOB_SCHEDULE_MAX
                BLOB_SCHEDULE_TARGET = t8n.fork.BLOB_SCHEDULE_TARGET

                target_blob_gas_price = Uint(GAS_PER_BLOB)
                target_blob_gas_price *= t8n.fork.calculate_blob_gas_price(
                    self.parent_excess_blob_gas
                )

                base_blob_tx_price = (
                    BLOB_BASE_COST * self.parent_base_fee_per_gas
                )
                if base_blob_tx_price > target_blob_gas_price:
                    blob_schedule_delta = (
                        BLOB_SCHEDULE_MAX - BLOB_SCHEDULE_TARGET
                    )
                    self.excess_blob_gas = (
                        self.parent_excess_blob_gas
                        + self.parent_blob_gas_used
                        * blob_schedule_delta
                        // BLOB_SCHEDULE_MAX
                    )

    def read_base_fee_per_gas(self, data: Any, t8n: "T8N") -> None:
        """
        Read the base_fee_per_gas from the data. If the base fee is
        not present, it is calculated from the parent block parameters.
        """
        self.parent_gas_used = None
        self.parent_gas_limit = None
        self.parent_base_fee_per_gas = None
        self.base_fee_per_gas = None

        if t8n.fork.is_after_fork("ethereum.london"):
            if "currentBaseFee" in data:
                self.base_fee_per_gas = parse_hex_or_int(
                    data["currentBaseFee"], Uint
                )

            if "parentGasUsed" in data:
                self.parent_gas_used = parse_hex_or_int(
                    data["parentGasUsed"], Uint
                )

            if "parentGasLimit" in data:
                self.parent_gas_limit = parse_hex_or_int(
                    data["parentGasLimit"], Uint
                )

            if "parentBaseFee" in data:
                self.parent_base_fee_per_gas = parse_hex_or_int(
                    data["parentBaseFee"], Uint
                )

            if self.base_fee_per_gas is None:
                assert self.parent_gas_limit is not None
                assert self.parent_gas_used is not None
                assert self.parent_base_fee_per_gas is not None

                parameters: List[object] = [
                    self.block_gas_limit,
                    self.parent_gas_limit,
                    self.parent_gas_used,
                    self.parent_base_fee_per_gas,
                ]

                self.base_fee_per_gas = t8n.fork.calculate_base_fee_per_gas(
                    *parameters
                )

    def read_randao(self, data: Any, t8n: "T8N") -> None:
        """
        Read the randao from the data.
        """
        self.prev_randao = None
        if t8n.fork.is_after_fork("ethereum.paris"):
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

    def read_withdrawals(self, data: Any, t8n: "T8N") -> None:
        """
        Read the withdrawals from the data.
        """
        self.withdrawals = None
        if t8n.fork.is_after_fork("ethereum.shanghai"):
            self.withdrawals = tuple(
                t8n.json_to_withdrawals(wd) for wd in data["withdrawals"]
            )

    def read_block_difficulty(self, data: Any, t8n: "T8N") -> None:
        """
        Read the block difficulty from the data.
        If `currentDifficulty` is present, it is used. Otherwise,
        the difficulty is calculated from the parent block.
        """
        self.block_difficulty = None
        self.parent_timestamp = None
        self.parent_difficulty = None
        self.parent_ommers_hash = None
        if t8n.fork.is_after_fork("ethereum.paris"):
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
            args: List[object] = [
                self.block_number,
                self.block_timestamp,
                self.parent_timestamp,
                self.parent_difficulty,
            ]
            if t8n.fork.is_after_fork("ethereum.byzantium"):
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

    def read_block_hashes(self, data: Any, t8n: "T8N") -> None:
        """
        Read the block hashes. Returns a maximum of 256 block hashes.
        """
        self.parent_hash = None
        if (
            t8n.fork.is_after_fork("ethereum.prague")
            and not t8n.options.state_test
        ):
            self.parent_hash = Hash32(hex_to_bytes(data["parentHash"]))

        # Read the block hashes
        block_hashes: List[Any] = []

        # The hex key strings provided might not have standard formatting
        clean_block_hashes: Dict[int, Hash32] = {}
        if "blockHashes" in data:
            for key, value in data["blockHashes"].items():
                int_key = int(key, 16)
                clean_block_hashes[int_key] = Hash32(hex_to_bytes(value))

        # Store a maximum of 256 block hashes.
        max_blockhash_count = min(Uint(256), self.block_number)
        for number in range(
            self.block_number - max_blockhash_count, self.block_number
        ):
            if number in clean_block_hashes.keys():
                block_hashes.append(clean_block_hashes[number])
            else:
                block_hashes.append(None)

        self.block_hashes = block_hashes

    def read_ommers(self, data: Any, t8n: "T8N") -> None:
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
                        t8n.fork.hex_to_address(ommer["address"]),
                    )
                )
        self.ommers = ommers
