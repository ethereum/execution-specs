"""
Read transaction data from json file and return the
relevant transaction.
"""

from dataclasses import fields
from typing import Any, List

from ethereum import rlp
from ethereum.base_types import U64, U256, Bytes, Bytes0, Bytes32, Uint
from ethereum.utils.hexadecimal import (
    hex_to_bytes,
    hex_to_bytes32,
    hex_to_hash,
    hex_to_u256,
    hex_to_uint,
)


class UnsupportedTx(Exception):
    """Exception for unsupported transactions"""

    def __init__(self, encoded_params: bytes, error_message: str) -> None:
        super().__init__(error_message)
        self.encoded_params = encoded_params
        self.error_message = error_message


class TransactionLoad:
    """
    Class for loading transaction data from json file
    """

    def __init__(self, raw: Any, fork: Any) -> None:
        self.raw = raw
        self.fork = fork

    def json_to_chain_id(self) -> U64:
        """Get chain ID for the transaction."""
        return U64(1)

    def json_to_nonce(self) -> U256:
        """Get the nonce for the transaction."""
        return hex_to_u256(self.raw.get("nonce"))

    def json_to_gas_price(self) -> Uint:
        """Get the gas price for the transaction."""
        return hex_to_uint(self.raw.get("gasPrice"))

    def json_to_gas(self) -> Uint:
        """Get the gas limit for the transaction."""
        return hex_to_uint(self.raw.get("gasLimit"))

    def json_to_to(self) -> Bytes:
        """Get to address for the transaction."""
        if self.raw.get("to") == "":
            return Bytes0(b"")
        return self.fork.hex_to_address(self.raw.get("to"))

    def json_to_value(self) -> U256:
        """Get the value of the transaction."""
        value = self.raw.get("value")
        if value == "0x":
            return U256(0)
        return hex_to_u256(value)

    def json_to_data(self) -> Bytes:
        """Get the data of the transaction."""
        return hex_to_bytes(self.raw.get("data"))

    def json_to_access_list(self) -> Any:
        """Get the access list of the transaction."""
        access_list = []
        for sublist in self.raw["accessList"]:
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

    def json_to_max_priority_fee_per_gas(self) -> Uint:
        """Get the max priority fee per gas of the transaction."""
        return hex_to_uint(self.raw.get("maxPriorityFeePerGas"))

    def json_to_max_fee_per_gas(self) -> Uint:
        """Get the max fee per gas of the transaction."""
        return hex_to_uint(self.raw.get("maxFeePerGas"))

    def json_to_max_fee_per_blob_gas(self) -> U256:
        """
        Get the max priority fee per blobgas of the transaction.
        """
        return hex_to_u256(self.raw.get("maxFeePerBlobGas"))

    def json_to_blob_versioned_hashes(self) -> List[Bytes32]:
        """Get the blob versioned hashes of the transaction."""
        return [
            hex_to_hash(blob_hash)
            for blob_hash in self.raw.get("blobVersionedHashes")
        ]

    def json_to_v(self) -> U256:
        """Get the v value of the transaction."""
        return hex_to_u256(
            self.raw.get("y_parity")
            if "y_parity" in self.raw
            else self.raw.get("v")
        )

    def json_to_y_parity(self) -> U256:
        """Get the y parity of the transaction."""
        return self.json_to_v()

    def json_to_r(self) -> U256:
        """Get the r value of the transaction"""
        return hex_to_u256(self.raw.get("r"))

    def json_to_s(self) -> U256:
        """Get the s value of the transaction"""
        return hex_to_u256(self.raw.get("s"))

    def get_parameters(self, tx_cls: Any) -> List:
        """
        Extract all the transaction parameters from the json file
        """
        parameters = []
        for field in fields(tx_cls):
            parameters.append(getattr(self, f"json_to_{field.name}")())
        return parameters

    def get_legacy_transaction(self) -> Any:
        """Return the approprtiate class for legacy transactions."""
        if hasattr(self.fork, "LegacyTransaction"):
            return self.fork.LegacyTransaction
        else:
            return self.fork.Transaction

    def read(self) -> Any:
        """Convert json transaction data to a transaction object"""
        if "type" in self.raw:
            tx_type = self.raw.get("type")
            if tx_type == "0x3":
                tx_cls = self.fork.BlobTransaction
                tx_byte_prefix = b"\x03"
            elif tx_type == "0x2":
                tx_cls = self.fork.FeeMarketTransaction
                tx_byte_prefix = b"\x02"
            elif tx_type == "0x1":
                tx_cls = self.fork.AccessListTransaction
                tx_byte_prefix = b"\x01"
            elif tx_type == "0x0":
                tx_cls = self.get_legacy_transaction()
                tx_byte_prefix = b""
            else:
                raise ValueError(f"Unknown transaction type: {tx_type}")
        else:
            if "maxFeePerBlobGas" in self.raw:
                tx_cls = self.fork.BlobTransaction
                tx_byte_prefix = b"\x03"
            elif "maxFeePerGas" in self.raw:
                tx_cls = self.fork.FeeMarketTransaction
                tx_byte_prefix = b"\x02"
            elif "accessList" in self.raw:
                tx_cls = self.fork.AccessListTransaction
                tx_byte_prefix = b"\x01"
            else:
                tx_cls = self.get_legacy_transaction()
                tx_byte_prefix = b""

        parameters = self.get_parameters(tx_cls)
        try:
            return tx_cls(*parameters)
        except Exception as e:
            raise UnsupportedTx(
                tx_byte_prefix + rlp.encode(parameters), str(e)
            ) from e
