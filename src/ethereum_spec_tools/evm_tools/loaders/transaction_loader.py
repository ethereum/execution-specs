"""
Read transaction data from json file and return the
relevant transaction.
"""

from dataclasses import fields
from typing import Any, List

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes0, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.utils.hexadecimal import (
    hex_to_bytes,
    hex_to_bytes32,
    hex_to_hash,
    hex_to_u8,
    hex_to_u64,
    hex_to_u256,
    hex_to_uint,
)
from ethereum_spec_tools.evm_tools.utils import parse_hex_or_int


class UnsupportedTxError(Exception):
    """Exception for unsupported transactions."""

    def __init__(
        self, encoded_params: bytes | None, error_message: str
    ) -> None:
        super().__init__(error_message)
        self.encoded_params = encoded_params
        self.error_message = error_message


class TransactionLoad:
    """
    Class for loading transaction data from json file.
    """

    def __init__(self, raw: Any, fork: Any) -> None:
        self.raw = raw
        self.fork = fork

    def json_to_chain_id(self) -> U64:
        """Get chain ID for the transaction."""
        return hex_to_u64(self.raw.get("chainId", "0x01"))

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
        for sublist in self.raw.get("accessList", []):
            access_list.append(
                self.fork.Access(
                    self.fork.hex_to_address(sublist.get("address")),
                    [
                        hex_to_bytes32(key)
                        for key in sublist.get("storageKeys")
                    ],
                )
            )
        return access_list

    def json_to_authorizations(self) -> Any:
        """Get the authorization list of the transaction."""
        authorizations = []
        for sublist in self.raw["authorizationList"]:
            authorizations.append(
                self.fork.Authorization(
                    chain_id=hex_to_u256(sublist.get("chainId")),
                    nonce=hex_to_u64(sublist.get("nonce")),
                    address=self.fork.hex_to_address(sublist.get("address")),
                    y_parity=hex_to_u8(sublist.get("v")),
                    r=hex_to_u256(sublist.get("r")),
                    s=hex_to_u256(sublist.get("s")),
                )
            )
        return authorizations

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

    def json_to_sender(self) -> Any:
        """Get the explicit sender address of a frame transaction."""
        return self.fork.hex_to_address(self.raw.get("sender"))

    def json_to_frames(self) -> Any:
        """Get the frames of a frame transaction."""
        frames = []
        for frame_data in self.raw.get("frames", []):
            target_raw = frame_data.get("target")
            if target_raw is None or target_raw in ("", "0x"):
                to: Any = Bytes0(b"")
            else:
                to = self.fork.hex_to_address(target_raw)
            try:
                frame = self.fork.Frame(
                    mode=self.fork.FrameMode(
                        parse_hex_or_int(frame_data.get("mode", 0), Uint)
                    ),
                    flags=self.fork.FrameFlag(
                        parse_hex_or_int(frame_data.get("flags", 0), Uint)
                    ),
                    to=to,
                    gas=parse_hex_or_int(frame_data.get("gasLimit", 0), U64),
                    value=parse_hex_or_int(frame_data.get("value", 0), U256),
                    data=hex_to_bytes(frame_data.get("data", "0x")),
                )
            except (ValueError, OverflowError) as e:
                # A field value the transaction types reject as they
                # are constructed — an undefined mode, a reserved flag
                # bit, an overflowing gas limit. Such a transaction
                # never decodes, so reject it instead of crashing.
                raise UnsupportedTxError(
                    None, f"invalid frame field: {e}"
                ) from e
            frames.append(frame)
        return tuple(frames)

    def json_to_signatures(self) -> Any:
        """Get the signature entries of a frame transaction."""
        signatures = []
        for sig_data in self.raw.get("signatures", []):
            msg = hex_to_bytes(sig_data.get("msg", "0x"))
            message: Any
            if len(msg) == 0:
                message = Bytes0(b"")
            elif len(msg) == 32:
                message = Bytes32(msg)
            else:
                message = msg
            try:
                signature = self.fork.FrameSignature(
                    scheme=self.fork.FrameSignatureScheme(
                        parse_hex_or_int(sig_data.get("scheme", 0), Uint)
                    ),
                    signer=hex_to_bytes(sig_data.get("signer", "0x")),
                    message=message,
                    signature=hex_to_bytes(sig_data.get("signature", "0x")),
                )
            except (ValueError, OverflowError) as e:
                # A field value the transaction types reject as they
                # are constructed — notably an undefined signature
                # scheme. Such a transaction never decodes, so reject
                # it instead of crashing.
                raise UnsupportedTxError(
                    None, f"invalid frame signature field: {e}"
                ) from e
            signatures.append(signature)
        return tuple(signatures)

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
        """Get the r value of the transaction."""
        return hex_to_u256(self.raw.get("r"))

    def json_to_s(self) -> U256:
        """Get the s value of the transaction."""
        return hex_to_u256(self.raw.get("s"))

    def get_parameters(self, tx_cls: Any) -> List:
        """
        Extract all the transaction parameters from the json file.
        """
        parameters = []
        for field in fields(tx_cls):
            parameters.append(getattr(self, f"json_to_{field.name}")())
        return parameters

    def get_legacy_transaction(self) -> Any:
        """Return the appropriate class for legacy transactions."""
        if hasattr(self.fork, "LegacyTransaction"):
            return self.fork.LegacyTransaction
        else:
            return self.fork.Transaction

    def unsupported_tx_type(self, tx_type: int) -> UnsupportedTxError:
        """Return an unsupported transaction type error for this fork."""
        return UnsupportedTxError(
            None,
            (
                f"transaction type {tx_type} is not supported in "
                f"{self.fork.hardfork.short_name}"
            ),
        )

    def read(self) -> Any:
        """Convert json transaction data to a transaction object."""
        if "type" in self.raw:
            tx_type = parse_hex_or_int(self.raw.get("type"), Uint)
            if tx_type == Uint(6):
                if not self.fork.supports_tx_type(6):
                    raise self.unsupported_tx_type(6)
                tx_cls = self.fork.FrameTransaction
                tx_byte_prefix = b"\x06"
            elif tx_type == Uint(4):
                if not self.fork.supports_tx_type(4):
                    raise self.unsupported_tx_type(4)
                tx_cls = self.fork.SetCodeTransaction
                tx_byte_prefix = b"\x04"
            elif tx_type == Uint(3):
                if not self.fork.supports_tx_type(3):
                    raise self.unsupported_tx_type(3)
                tx_cls = self.fork.BlobTransaction
                tx_byte_prefix = b"\x03"
            elif tx_type == Uint(2):
                if not self.fork.supports_tx_type(2):
                    raise self.unsupported_tx_type(2)
                tx_cls = self.fork.FeeMarketTransaction
                tx_byte_prefix = b"\x02"
            elif tx_type == Uint(1):
                if not self.fork.supports_tx_type(1):
                    raise self.unsupported_tx_type(1)
                tx_cls = self.fork.AccessListTransaction
                tx_byte_prefix = b"\x01"
            elif tx_type == Uint(0):
                tx_cls = self.get_legacy_transaction()
                tx_byte_prefix = b""
            else:
                raise ValueError(f"Unknown transaction type: {tx_type}")
        else:
            if "frames" in self.raw:
                # Checked before the blob fields: frame transactions
                # always carry `maxFeePerBlobGas`.
                if not self.fork.supports_tx_type(6):
                    raise self.unsupported_tx_type(6)
                tx_cls = self.fork.FrameTransaction
                tx_byte_prefix = b"\x06"
            elif "authorizationList" in self.raw:
                if not self.fork.supports_tx_type(4):
                    raise self.unsupported_tx_type(4)
                tx_cls = self.fork.SetCodeTransaction
                tx_byte_prefix = b"\x04"
            elif "maxFeePerBlobGas" in self.raw:
                if not self.fork.supports_tx_type(3):
                    raise self.unsupported_tx_type(3)
                tx_cls = self.fork.BlobTransaction
                tx_byte_prefix = b"\x03"
            elif "maxFeePerGas" in self.raw:
                if not self.fork.supports_tx_type(2):
                    raise self.unsupported_tx_type(2)
                tx_cls = self.fork.FeeMarketTransaction
                tx_byte_prefix = b"\x02"
            elif "accessList" in self.raw:
                if not self.fork.supports_tx_type(1):
                    raise self.unsupported_tx_type(1)
                tx_cls = self.fork.AccessListTransaction
                tx_byte_prefix = b"\x01"
            else:
                tx_cls = self.get_legacy_transaction()
                tx_byte_prefix = b""

        parameters = self.get_parameters(tx_cls)
        try:
            return tx_cls(*parameters)
        except Exception as e:
            raise UnsupportedTxError(
                tx_byte_prefix + rlp.encode(parameters), str(e)
            ) from e
