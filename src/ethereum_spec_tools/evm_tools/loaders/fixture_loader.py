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

    def json_to_state(self, json_data: Any) -> Any:
        """Converts json state data to a state object"""
        state = self.fork.State()
        set_storage = self.fork.set_storage

        for address_hex, account_state in json_data.items():
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
        json_data: Any,
    ) -> Tuple[Any, Hash32, bytes]:
        """Converts json block data to a block object"""
        if "rlp" in json_data:
            # Always decode from rlp
            block_rlp = hex_to_bytes(json_data["rlp"])
            block = rlp.decode_to(self.fork.Block, block_rlp)
            block_header_hash = keccak256(rlp.encode(block.header))
            return block, block_header_hash, block_rlp

        header = self.json_to_header(json_data["blockHeader"])
        transactions = tuple(
            TransactionLoad(tx, self.fork).read()
            for tx in json_data["transactions"]
        )
        uncles = tuple(
            self.json_to_header(uncle) for uncle in json_data["uncleHeaders"]
        )

        parameters = [
            header,
            transactions,
            uncles,
        ]

        if "withdrawals" in json_data:
            withdrawals = tuple(
                self.json_to_withdrawals(wd) for wd in json_data["withdrawals"]
            )
            parameters.append(withdrawals)

        block = self.fork.Block(*parameters)
        block_header_hash = Hash32(
            hex_to_bytes(json_data["blockHeader"]["hash"])
        )
        block_rlp = hex_to_bytes(json_data["rlp"])

        return block, block_header_hash, block_rlp

    def json_to_header(self, json_data: Any) -> Any:
        """Converts json header data to a header object"""
        parameters = [
            hex_to_hash(json_data.get("parentHash")),
            hex_to_hash(
                json_data.get("uncleHash") or json_data.get("sha3Uncles")
            ),
            self.fork.hex_to_address(
                json_data.get("coinbase") or json_data.get("miner")
            ),
            self.fork.hex_to_root(json_data.get("stateRoot")),
            self.fork.hex_to_root(
                json_data.get("transactionsTrie")
                or json_data.get("transactionsRoot")
            ),
            self.fork.hex_to_root(
                json_data.get("receiptTrie") or json_data.get("receiptsRoot")
            ),
            self.fork.Bloom(
                hex_to_bytes(
                    json_data.get("bloom") or json_data.get("logsBloom")
                )
            ),
            hex_to_uint(json_data.get("difficulty")),
            hex_to_uint(json_data.get("number")),
            hex_to_uint(json_data.get("gasLimit")),
            hex_to_uint(json_data.get("gasUsed")),
            hex_to_u256(json_data.get("timestamp")),
            hex_to_bytes(json_data.get("extraData")),
            hex_to_bytes32(json_data.get("mixHash")),
            hex_to_bytes8(json_data.get("nonce")),
        ]

        if "baseFeePerGas" in json_data:
            base_fee_per_gas = hex_to_uint(json_data.get("baseFeePerGas"))
            parameters.append(base_fee_per_gas)

        if "withdrawalsRoot" in json_data:
            withdrawals_root = self.fork.hex_to_root(
                json_data.get("withdrawalsRoot")
            )
            parameters.append(withdrawals_root)

        if "excessBlobGas" in json_data:
            blob_gas_used = hex_to_u64(json_data.get("blobGasUsed"))
            parameters.append(blob_gas_used)
            excess_blob_gas = hex_to_u64(json_data.get("excessBlobGas"))
            parameters.append(excess_blob_gas)
            parent_beacon_block_root = self.fork.hex_to_root(
                json_data.get("parentBeaconBlockRoot")
            )
            parameters.append(parent_beacon_block_root)

        if "requestsHash" in json_data:
            requests_hash = hex_to_bytes32(json_data.get("requestsHash"))
            parameters.append(requests_hash)

        return self.fork.Header(*parameters)
