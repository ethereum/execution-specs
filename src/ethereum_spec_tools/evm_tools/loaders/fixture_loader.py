"""
Defines Load class for loading json fixtures for the evm
tools (t8n, b11r, etc.) as well as the execution specs
testing framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Tuple

from ethereum import rlp
from ethereum.base_types import U64, U256, Bytes0
from ethereum.crypto.hash import Hash32
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


class UnsupportedTx(Exception):
    """Exception for unsupported transactions"""

    def __init__(self, encoded_params: bytes, error_message: str) -> None:
        super().__init__(error_message)
        self.encoded_params = encoded_params
        self.error_message = error_message


class BaseLoad(ABC):
    """Base class for loading json fixtures"""

    @abstractmethod
    def json_to_header(self, json_data: Any) -> Any:
        """Converts json header data to a header object"""
        pass

    @abstractmethod
    def json_to_state(self, json_data: Any) -> Any:
        """Converts json state data to a state object"""
        pass

    @abstractmethod
    def json_to_block(self, json_data: Any) -> Any:
        """Converts json block data to a list of blocks"""
        pass


class Load(BaseLoad):
    """Class for loading json fixtures"""

    _network: str
    _fork_module: str

    def __init__(self, network: str, fork_name: str):
        self._network = network
        self.fork = ForkLoad(fork_name)

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

    def json_to_access_list(self, raw: Any) -> Any:
        """Converts json access list data to a list of access list entries"""
        access_list = []
        for sublist in raw:
            access_list.append(
                (
                    self.fork.hex_to_address(sublist.get("address")),
                    [
                        hex_to_bytes32(key)
                        for key in sublist.get("storageKeys")
                    ],
                )
            )
        return access_list

    def json_to_tx(self, raw: Any) -> Any:
        """Converts json transaction data to a transaction object"""
        parameters = [
            hex_to_u256(raw.get("nonce")),
            hex_to_u256(raw.get("gasLimit")),
            Bytes0(b"")
            if raw.get("to") == ""
            else self.fork.hex_to_address(raw.get("to")),
            hex_to_u256(raw.get("value")),
            hex_to_bytes(raw.get("data")),
            hex_to_u256(
                raw.get("y_parity") if "y_parity" in raw else raw.get("v")
            ),
            hex_to_u256(raw.get("r")),
            hex_to_u256(raw.get("s")),
        ]

        # Cancun and beyond
        if "maxFeePerBlobGas" in raw:
            parameters.insert(0, U64(1))
            parameters.insert(2, hex_to_u256(raw.get("maxPriorityFeePerGas")))
            parameters.insert(3, hex_to_u256(raw.get("maxFeePerGas")))
            parameters.insert(
                8, self.json_to_access_list(raw.get("accessList"))
            )
            parameters.insert(9, hex_to_u256(raw.get("maxFeePerBlobGas")))
            parameters.insert(
                10,
                [
                    hex_to_hash(blob_hash)
                    for blob_hash in raw.get("blobVersionedHashes")
                ],
            )

            try:
                return b"\x03" + rlp.encode(
                    self.fork.BlobTransaction(*parameters)
                )
            except AttributeError as e:
                raise UnsupportedTx(
                    b"\x03" + rlp.encode(parameters), str(e)
                ) from e

        # London and beyond
        if "maxFeePerGas" in raw and "maxPriorityFeePerGas" in raw:
            parameters.insert(0, U64(1))
            parameters.insert(2, hex_to_u256(raw.get("maxPriorityFeePerGas")))
            parameters.insert(3, hex_to_u256(raw.get("maxFeePerGas")))
            parameters.insert(
                8, self.json_to_access_list(raw.get("accessList"))
            )
            try:
                return b"\x02" + rlp.encode(
                    self.fork.FeeMarketTransaction(*parameters)
                )
            except AttributeError as e:
                raise UnsupportedTx(
                    b"\x02" + rlp.encode(parameters), str(e)
                ) from e

        parameters.insert(1, hex_to_u256(raw.get("gasPrice")))
        # Access List Transaction
        if "accessList" in raw:
            parameters.insert(0, U64(1))
            parameters.insert(
                7, self.json_to_access_list(raw.get("accessList"))
            )
            try:
                return b"\x01" + rlp.encode(
                    self.fork.AccessListTransaction(*parameters)
                )
            except AttributeError as e:
                raise UnsupportedTx(
                    b"\x01" + rlp.encode(parameters), str(e)
                ) from e

        # Legacy Transaction
        try:
            return self.fork.LegacyTransaction(*parameters)
        except AttributeError:
            return self.fork.Transaction(*parameters)

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
            block_header_hash = rlp.rlp_hash(block.header)
            return block, block_header_hash, block_rlp

        header = self.json_to_header(json_block["blockHeader"])
        transactions = tuple(
            self.json_to_tx(tx) for tx in json_block["transactions"]
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
