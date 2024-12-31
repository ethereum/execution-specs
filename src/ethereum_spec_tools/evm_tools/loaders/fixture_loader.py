"""
Defines Load class for loading json fixtures for the evm
tools (t8n, b11r, etc.) as well as the execution specs
testing framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Tuple

from ethereum_rlp import rlp
from ethereum_types.numeric import U256

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.utils.hexadecimal import (
    hex_to_bytes,
    hex_to_bytes8,
    hex_to_bytes32,
    hex_to_hash,
    hex_to_u64,
    hex_to_u256,
    hex_to_uint,
)

from .fork_loader import ForkLoad
from .transaction_loader import TransactionLoad


class BaseLoad(ABC):
    """Base class for loading JSON fixtures"""

    @abstractmethod
    def json_to_header(self, json_data: Any) -> Any:
        """Converts json header data to a header object"""
        raise NotImplementedError()

    @abstractmethod
    def json_to_state(self, json_data: Any) -> Any:
        """Converts json state data to a state object"""
        raise NotImplementedError()

    @abstractmethod
    def json_to_block(self, json_data: Any) -> Any:
        """Converts json block data to a list of blocks"""
        raise NotImplementedError()


class Load(BaseLoad):
    """Class for loading json fixtures"""

    _network: str
    _fork_module: str
    fork: ForkLoad

    def __init__(self, network: str, fork_module: str):
        self._network = network
        self._fork_module = fork_module
        self.fork = ForkLoad(fork_module)

    def json_to_state(self, raw: Any) -> Any:
        """Converts json state data to a state object"""
        state = self.fork.State()
        set_storage = self.fork.set_storage

        for address_hex, account_state in raw.items():
            address = self.fork.hex_to_address(address_hex)
            account = self.fork.Account(
                nonce=hex_to_uint(account_state.get("nonce", "0x0")),
                balance=U256(hex_to_uint(account_state.get("balance", "0x0"))),
                code=hex_to_bytes(account_state.get("code", "")),
            )
            self.fork.set_account(state, address, account)

            for k, v in account_state.get("storage", {}).items():
                set_storage(
                    state,
                    address,
                    hex_to_bytes32(k),
                    U256.from_be_bytes(hex_to_bytes32(v)),
                )
        return state

    def json_to_withdrawals(self, raw: Any) -> Any:
        """Converts json withdrawal data to a withdrawal object"""
        parameters = [
            hex_to_u64(raw.get("index")),
            hex_to_u64(raw.get("validatorIndex")),
            self.fork.hex_to_address(raw.get("address")),
            hex_to_u256(raw.get("amount")),
        ]

        return self.fork.Withdrawal(*parameters)

    def json_to_block(
        self,
        json_block: Any,
    ) -> Tuple[Any, Hash32, bytes]:
        """Converts json block data to a block object"""
        if "rlp" in json_block:
            # Always decode from rlp
            block_rlp = hex_to_bytes(json_block["rlp"])
            block = rlp.decode_to(self.fork.Block, block_rlp)
            block_header_hash = keccak256(rlp.encode(block.header))
            return block, block_header_hash, block_rlp

        header = self.json_to_header(json_block["blockHeader"])
        transactions = tuple(
            TransactionLoad(tx, self.fork).read()
            for tx in json_block["transactions"]
        )
        uncles = tuple(
            self.json_to_header(uncle) for uncle in json_block["uncleHeaders"]
        )

        parameters = [
            header,
            transactions,
            uncles,
        ]

        if "withdrawals" in json_block:
            withdrawals = tuple(
                self.json_to_withdrawals(wd)
                for wd in json_block["withdrawals"]
            )
            parameters.append(withdrawals)

        block = self.fork.Block(*parameters)
        block_header_hash = Hash32(
            hex_to_bytes(json_block["blockHeader"]["hash"])
        )
        block_rlp = hex_to_bytes(json_block["rlp"])

        return block, block_header_hash, block_rlp

    def json_to_header(self, raw: Any) -> Any:
        """Converts json header data to a header object"""
        parameters = [
            hex_to_hash(raw.get("parentHash")),
            hex_to_hash(raw.get("uncleHash") or raw.get("sha3Uncles")),
            self.fork.hex_to_address(raw.get("coinbase") or raw.get("miner")),
            self.fork.hex_to_root(raw.get("stateRoot")),
            self.fork.hex_to_root(
                raw.get("transactionsTrie") or raw.get("transactionsRoot")
            ),
            self.fork.hex_to_root(
                raw.get("receiptTrie") or raw.get("receiptsRoot")
            ),
            self.fork.Bloom(
                hex_to_bytes(raw.get("bloom") or raw.get("logsBloom"))
            ),
            hex_to_uint(raw.get("difficulty")),
            hex_to_uint(raw.get("number")),
            hex_to_uint(raw.get("gasLimit")),
            hex_to_uint(raw.get("gasUsed")),
            hex_to_u256(raw.get("timestamp")),
            hex_to_bytes(raw.get("extraData")),
            hex_to_bytes32(raw.get("mixHash")),
            hex_to_bytes8(raw.get("nonce")),
        ]

        if "baseFeePerGas" in raw:
            base_fee_per_gas = hex_to_uint(raw.get("baseFeePerGas"))
            parameters.append(base_fee_per_gas)

        if "withdrawalsRoot" in raw:
            withdrawals_root = self.fork.hex_to_root(
                raw.get("withdrawalsRoot")
            )
            parameters.append(withdrawals_root)

        if "excessBlobGas" in raw:
            blob_gas_used = hex_to_u64(raw.get("blobGasUsed"))
            parameters.append(blob_gas_used)
            excess_blob_gas = hex_to_u64(raw.get("excessBlobGas"))
            parameters.append(excess_blob_gas)
            parent_beacon_block_root = self.fork.hex_to_root(
                raw.get("parentBeaconBlockRoot")
            )
            parameters.append(parent_beacon_block_root)

        return self.fork.Header(*parameters)
