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
from ethereum_test_types.block_types import Environment

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

    def __init__(self, t8n: "T8N", stdin: Environment):
        self.coinbase = stdin.fee_recipient
        self.block_gas_limit = Uint(stdin.gas_limit)
        self.block_number = Uint(stdin.number)
        self.block_timestamp = U256(stdin.timestamp)

        self.read_block_difficulty(stdin, t8n)
        self.read_base_fee_per_gas(stdin, t8n)
        self.read_randao(stdin, t8n)
        self.read_block_hashes(stdin, t8n)
        self.read_ommers(stdin, t8n)
        self.read_withdrawals(stdin, t8n)

        self.parent_beacon_block_root = None
        if t8n.fork.is_after_fork("ethereum.cancun"):
            if not t8n.options.state_test:
                parent_beacon_block_root_bytes = stdin.parent_beacon_block_root
                self.parent_beacon_block_root = (
                    Bytes32(parent_beacon_block_root_bytes)
                    if parent_beacon_block_root_bytes is not None
                    else None
                )
            self.read_excess_blob_gas(stdin, t8n)

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

        if hasattr(data, "excess_blob_gas") and data.excess_blob_gas is not None:
            self.excess_blob_gas = U64(data.excess_blob_gas)

        if hasattr(data, "parent_excess_blob_gas") and data.parent_excess_blob_gas is not None:
            self.parent_excess_blob_gas = U64(data.parent_excess_blob_gas)

        if hasattr(data, "parent_blob_gas_used") and data.parent_blob_gas_used is not None:
            self.parent_blob_gas_used = U64(data.parent_blob_gas_used)

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
            if hasattr(data, "base_fee_per_gas") and data.base_fee_per_gas is not None:
                self.base_fee_per_gas = Uint(data.base_fee_per_gas)

            if hasattr(data, "parent_gas_used") and data.parent_gas_used is not None:
                self.parent_gas_used = Uint(data.parent_gas_used)

            if hasattr(data, "parent_gas_limit") and data.parent_gas_limit is not None:
                self.parent_gas_limit = Uint(data.parent_gas_limit)

            if hasattr(data, "parent_base_fee_per_gas") and data.parent_base_fee_per_gas is not None:
                self.parent_base_fee_per_gas = Uint(data.parent_base_fee_per_gas)

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
            self.prev_randao = Bytes32(data.prev_randao.to_bytes(32, "big"))

    def read_withdrawals(self, data: Any, t8n: "T8N") -> None:
        """
        Read the withdrawals from the data.
        """
        self.withdrawals = None
        if t8n.fork.is_after_fork("ethereum.shanghai"):
            raw_withdrawals = getattr(data, "withdrawals", None)
            if raw_withdrawals:
                def to_canonical_withdrawal(raw):
                    return t8n.fork.Withdrawal(
                        index=U64(raw.index),
                        validator_index=U64(raw.validator_index),
                        address=raw.address,
                        amount=U256(raw.amount),
                    )
                self.withdrawals = tuple(to_canonical_withdrawal(wd) for wd in raw_withdrawals)
            else:
                self.withdrawals = ()

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
        elif hasattr(data, "difficulty") and data.difficulty is not None:
            self.block_difficulty = Uint(data.difficulty)
        else:
            self.parent_timestamp = U256(data.parent_timestamp)
            self.parent_difficulty = Uint(data.parent_difficulty)
            args: List[object] = [
                self.block_number,
                self.block_timestamp,
                self.parent_timestamp,
                self.parent_difficulty,
            ]
            if t8n.fork.is_after_fork("ethereum.byzantium"):
                if hasattr(data, "parent_ommers_hash") and data.parent_ommers_hash is not None:
                    EMPTY_OMMER_HASH = keccak256(rlp.encode([]))
                    self.parent_ommers_hash = Hash32(
                        data.parent_ommers_hash
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
            self.parent_hash = Hash32(data.parent_hash)

        # Read the block hashes
        block_hashes: List[Any] = []

        # The hex key strings provided might not have standard formatting
        clean_block_hashes: Dict[int, Hash32] = data.block_hashes

        # Store a maximum of 256 block hashes.
        max_blockhash_count = min(Uint(256), self.block_number)
        for number in range(
            self.block_number - max_blockhash_count, self.block_number
        ):
            if number in clean_block_hashes.keys():
                block_hashes.append(Hash32(clean_block_hashes[number]))
            else:
                block_hashes.append(None)

        self.block_hashes = block_hashes

    def read_ommers(self, data: Any, t8n: "T8N") -> None:
        """
        Read the ommers. The ommers data might not have all the details
        needed to obtain the Header.
        """
        ommers = []
        if hasattr(data, "ommers") and data.ommers is not None:
            for ommer in data.ommers:
                ommers.append(
                    Ommer(
                        ommer.delta,
                        ommer.address,
                    )
                )
        self.ommers = ommers
