"""
The `eth_simulateV1` request, parsed.

These types mirror `EthSimulatePayload` in execution-apis'
`src/schemas/execute.yaml`. They are deliberately a straight
transcription rather than a reuse of anything in the testing package:
the schema is the only specification of this request, so drift between
the two is the risk worth guarding against.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ethereum_types.bytes import Bytes, Bytes20, Bytes32
from ethereum_types.numeric import U256

ZERO_ADDRESS = Bytes20(b"\0" * 20)


def parse_address(value: str) -> Bytes20:
    """Parse a hex address."""
    return Bytes20(bytes.fromhex(value.removeprefix("0x")))


def parse_bytes(value: str) -> Bytes:
    """Parse a hex byte string."""
    return Bytes(bytes.fromhex(value.removeprefix("0x")))


def parse_hash(value: str) -> Bytes32:
    """
    Parse a hex 32-byte value, left-padding a short one.

    The schema asks for exactly 32 bytes, but a storage key written as
    `0x2` is unambiguous and clients accept it, so this does too.
    """
    digits = value.removeprefix("0x")
    raw = bytes.fromhex(digits.zfill(len(digits) + len(digits) % 2))
    return Bytes32(raw.rjust(32, b"\0"))


def _quantity(raw: Dict[str, Any], name: str) -> Optional[int]:
    """Read an optional hex quantity out of a JSON object."""
    if name not in raw or raw[name] is None:
        return None
    return int(raw[name], 16)


def _storage(raw: Optional[Dict[str, str]]) -> Optional[Dict[Bytes32, U256]]:
    """Parse a storage mapping, keeping `None` distinct from empty."""
    if raw is None:
        return None
    return {
        parse_hash(key): U256(int(value, 16)) for key, value in raw.items()
    }


@dataclass
class AccountOverride:
    """State replacing an account before a simulated block executes."""

    nonce: Optional[int] = None
    balance: Optional[int] = None
    code: Optional[Bytes] = None
    state: Optional[Dict[Bytes32, U256]] = None
    state_diff: Optional[Dict[Bytes32, U256]] = None
    move_precompile_to_address: Optional[Bytes20] = None

    @staticmethod
    def parse(raw: Dict[str, Any]) -> "AccountOverride":
        """Build an override from its JSON form."""
        return AccountOverride(
            nonce=_quantity(raw, "nonce"),
            balance=_quantity(raw, "balance"),
            code=parse_bytes(raw["code"]) if "code" in raw else None,
            state=_storage(raw.get("state")),
            state_diff=_storage(raw.get("stateDiff")),
            move_precompile_to_address=(
                parse_address(raw["movePrecompileToAddress"])
                if "movePrecompileToAddress" in raw
                else None
            ),
        )


@dataclass
class WithdrawalOverride:
    """A withdrawal the caller asks a simulated block to pay out."""

    index: int
    validator_index: int
    address: Bytes20
    amount: int

    @staticmethod
    def parse(raw: Dict[str, Any]) -> "WithdrawalOverride":
        """Build a withdrawal from its JSON form."""
        return WithdrawalOverride(
            index=int(raw["index"], 16),
            validator_index=int(raw["validatorIndex"], 16),
            address=parse_address(raw["address"]),
            amount=int(raw["amount"], 16),
        )


@dataclass
class BlockOverrides:
    """Block context fields the caller replaced."""

    number: Optional[int] = None
    time: Optional[int] = None
    gas_limit: Optional[int] = None
    fee_recipient: Optional[Bytes20] = None
    prev_randao: Optional[int] = None
    base_fee_per_gas: Optional[int] = None
    blob_base_fee: Optional[int] = None
    withdrawals: Optional[List[WithdrawalOverride]] = None

    @staticmethod
    def parse(raw: Dict[str, Any]) -> "BlockOverrides":
        """Build block overrides from their JSON form."""
        withdrawals = raw.get("withdrawals")
        return BlockOverrides(
            number=_quantity(raw, "number"),
            time=_quantity(raw, "time"),
            gas_limit=_quantity(raw, "gasLimit"),
            fee_recipient=(
                parse_address(raw["feeRecipient"])
                if "feeRecipient" in raw
                else None
            ),
            prev_randao=_quantity(raw, "prevRandao"),
            base_fee_per_gas=_quantity(raw, "baseFeePerGas"),
            blob_base_fee=_quantity(raw, "blobBaseFee"),
            withdrawals=(
                [WithdrawalOverride.parse(entry) for entry in withdrawals]
                if withdrawals is not None
                else None
            ),
        )


@dataclass
class AccessListEntry:
    """One `(address, storage keys)` pair of an access list."""

    address: Bytes20
    storage_keys: Tuple[Bytes32, ...]

    @staticmethod
    def parse(raw: Dict[str, Any]) -> "AccessListEntry":
        """Build an access list entry from its JSON form."""
        return AccessListEntry(
            address=parse_address(raw["address"]),
            storage_keys=tuple(
                parse_hash(key) for key in raw.get("storageKeys", [])
            ),
        )


@dataclass
class Call:
    """One message call inside a simulated block."""

    sender: Bytes20 = ZERO_ADDRESS
    to: Optional[Bytes20] = None
    value: int = 0
    data: Bytes = Bytes(b"")
    gas: Optional[int] = None
    nonce: Optional[int] = None
    gas_price: Optional[int] = None
    max_fee_per_gas: Optional[int] = None
    max_priority_fee_per_gas: Optional[int] = None
    max_fee_per_blob_gas: Optional[int] = None
    blob_versioned_hashes: Optional[Tuple[Bytes32, ...]] = None
    access_list: Optional[Tuple[AccessListEntry, ...]] = None
    call_type: Optional[int] = None
    """
    The transaction type the caller named in `type`, if any.

    Left as `None` the call is synthesized as the type its own fields
    imply, which is what a client does for a payload that names none.
    """

    @staticmethod
    def parse(raw: Dict[str, Any]) -> "Call":
        """Build a call from its JSON form."""
        access_list = raw.get("accessList")
        blob_hashes = raw.get("blobVersionedHashes")
        return Call(
            sender=(
                parse_address(raw["from"]) if "from" in raw else ZERO_ADDRESS
            ),
            to=parse_address(raw["to"]) if raw.get("to") else None,
            value=_quantity(raw, "value") or 0,
            data=parse_bytes(raw["input"]) if "input" in raw else Bytes(b""),
            gas=_quantity(raw, "gas"),
            nonce=_quantity(raw, "nonce"),
            gas_price=_quantity(raw, "gasPrice"),
            max_fee_per_gas=_quantity(raw, "maxFeePerGas"),
            max_priority_fee_per_gas=_quantity(raw, "maxPriorityFeePerGas"),
            max_fee_per_blob_gas=_quantity(raw, "maxFeePerBlobGas"),
            blob_versioned_hashes=(
                tuple(parse_hash(entry) for entry in blob_hashes)
                if blob_hashes is not None
                else None
            ),
            access_list=(
                tuple(AccessListEntry.parse(entry) for entry in access_list)
                if access_list is not None
                else None
            ),
            call_type=_quantity(raw, "type"),
        )


@dataclass
class BlockStateCall:
    """One simulated block: its context, its overrides and its calls."""

    block_overrides: BlockOverrides = field(default_factory=BlockOverrides)
    state_overrides: Dict[Bytes20, AccountOverride] = field(
        default_factory=dict
    )
    calls: List[Call] = field(default_factory=list)

    @staticmethod
    def parse(raw: Dict[str, Any]) -> "BlockStateCall":
        """Build a block state call from its JSON form."""
        return BlockStateCall(
            block_overrides=BlockOverrides.parse(
                raw.get("blockOverrides", {})
            ),
            state_overrides={
                parse_address(address): AccountOverride.parse(override)
                for address, override in raw.get("stateOverrides", {}).items()
            },
            calls=[Call.parse(call) for call in raw.get("calls", [])],
        )


@dataclass
class SimulatePayload:
    """The whole `eth_simulateV1` first parameter."""

    block_state_calls: List[BlockStateCall] = field(default_factory=list)
    trace_transfers: bool = False
    validation: bool = False
    return_full_transactions: bool = False

    @staticmethod
    def parse(raw: Dict[str, Any]) -> "SimulatePayload":
        """Build a payload from its JSON form."""
        return SimulatePayload(
            block_state_calls=[
                BlockStateCall.parse(entry)
                for entry in raw.get("blockStateCalls", [])
            ],
            trace_transfers=bool(raw.get("traceTransfers", False)),
            validation=bool(raw.get("validation", False)),
            return_full_transactions=bool(
                raw.get("returnFullTransactions", False)
            ),
        )


__all__ = [
    "AccessListEntry",
    "AccountOverride",
    "BlockOverrides",
    "BlockStateCall",
    "Call",
    "SimulatePayload",
    "WithdrawalOverride",
    "ZERO_ADDRESS",
    "parse_address",
    "parse_bytes",
    "parse_hash",
]
