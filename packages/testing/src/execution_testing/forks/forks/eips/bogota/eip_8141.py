"""
EIP-8141: Frame Transaction.

Add a new transaction type constructed from a series of frames,
abstractly defining validity conditions and gas payment.

https://eips.ethereum.org/EIPS/eip-8141
"""

from dataclasses import replace
from typing import List, Mapping, Sequence

from execution_testing.base_types import Bytes
from execution_testing.base_types.conversions import BytesConvertible

from ....base_fork import (
    BaseFork,
    FrameEntryGasCalculator,
    FrameGasInfo,
    FrameSignatureGasInfo,
    FrameTransactionDataFloorCostCalculator,
    FrameTransactionIntrinsicCostCalculator,
)
from ....gas_costs import GasCosts

EXPIRY_VERIFIER_ADDRESS = 0x0000000000000000000000000000000000008141
EXPIRY_VERIFIER_BYTECODE = bytes.fromhex(
    "60083614600a575f5ffd5b5f3560c01c4211601657005b5f5ffd"
)


class _DatalessFrame:
    """Stand-in for a frame carrying no data, no value, no frame gas."""

    data = b""
    gas_limit = 0
    state_gas_limit = 0
    value = 0
    target = None


_DATALESS_FRAME = _DatalessFrame()


class EIP8141(BaseFork):
    """EIP-8141 class."""

    @classmethod
    def tx_types(cls) -> List[int]:
        """Frame transactions (type 6) are introduced."""
        return super(EIP8141, cls).tx_types() + [6]

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """Add the frame transaction intrinsic gas constants."""
        return replace(
            super(EIP8141, cls).gas_costs(),
            TX_FRAME_INTRINSIC=12_000,
            TX_PER_FRAME=475,
            FRAME_SIGNATURE_SCHEME_ARBITRARY=100,
            FRAME_SIGNATURE_SCHEME_SECP256K1=2_800,
            FRAME_SIGNATURE_SCHEME_P256=6_700,
        )

    @classmethod
    def _frame_transaction_charged_bytes(
        cls,
        frames: Sequence[FrameGasInfo],
        signatures: Sequence[FrameSignatureGasInfo],
    ) -> List[Bytes]:
        """
        Return the transaction's byte fields priced as calldata: the
        `data` of each frame and the `signer`, `msg`, and `signature`
        bytes of each signature entry.
        """
        charged_bytes = [Bytes(frame.data) for frame in frames]
        for signature in signatures:
            charged_bytes += [
                Bytes(signature.signer),
                Bytes(signature.msg),
                Bytes(signature.signature),
            ]
        return charged_bytes

    @classmethod
    def _frame_list(
        cls, frames: Sequence[FrameGasInfo] | int
    ) -> Sequence[FrameGasInfo]:
        """
        Return the frames as a sequence: an integer stands for that
        many frames carrying no data and no frame gas.
        """
        if isinstance(frames, int):
            return (_DATALESS_FRAME,) * frames
        return frames

    @classmethod
    def _frame_transaction_base_cost(
        cls,
        frames: Sequence[FrameGasInfo],
        signatures: Sequence[FrameSignatureGasInfo],
        sender: BytesConvertible | None,
    ) -> int:
        """
        Return the costs a frame transaction always pays regardless of
        execution: the base cost, the per-frame cost, the verification
        cost of each signature entry, and the value transfer cost of
        each value-bearing frame whose explicit target differs from the
        sender.
        """
        gas_costs = cls.gas_costs()
        scheme_gas = {
            0: gas_costs.FRAME_SIGNATURE_SCHEME_ARBITRARY,
            1: gas_costs.FRAME_SIGNATURE_SCHEME_SECP256K1,
            2: gas_costs.FRAME_SIGNATURE_SCHEME_P256,
        }
        value_transfer_cost = 0
        for frame in frames:
            if int(frame.value) == 0 or frame.target is None:
                continue
            assert sender is not None, (
                "sender is required to price a value-bearing frame "
                "with an explicit target"
            )
            if Bytes(frame.target) != Bytes(sender):
                value_transfer_cost += gas_costs.TX_VALUE_COST
        return (
            gas_costs.TX_FRAME_INTRINSIC
            + len(frames) * gas_costs.TX_PER_FRAME
            + sum(scheme_gas[int(sig.scheme)] for sig in signatures)
            + value_transfer_cost
        )

    @classmethod
    def frame_transaction_data_floor_cost_calculator(
        cls,
    ) -> FrameTransactionDataFloorCostCalculator:
        """
        Frame transaction data floor cost is introduced.

        Every charged byte counts uniformly at the floor price on top
        of the costs the transaction always pays regardless of
        execution.
        """
        gas_costs = cls.gas_costs()

        def fn(
            *,
            frames: Sequence[FrameGasInfo] | int,
            signatures: Sequence[FrameSignatureGasInfo] = (),
            sender: BytesConvertible | None = None,
        ) -> int:
            frame_list = cls._frame_list(frames)
            data_length = sum(
                len(data)
                for data in cls._frame_transaction_charged_bytes(
                    frame_list, signatures
                )
            )
            return cls._frame_transaction_base_cost(
                frame_list, signatures, sender
            ) + (
                data_length
                * gas_costs.TX_DATA_TOKEN_STANDARD
                * gas_costs.TX_DATA_TOKEN_FLOOR
            )

        return fn

    @classmethod
    def frame_entry_gas_calculator(cls) -> FrameEntryGasCalculator:
        """
        Frame entry gas is introduced.

        A frame executing its target's code charges the target's warm
        or cold access at entry, and the warm or cold access of the
        delegate when the target carries an EIP-7702 delegation
        designation. A value transfer reviving a dead account charges
        the account creation — ``gas_costs().NEW_ACCOUNT`` — to the
        frame's state gas budget, outside this calculator's execution
        gas result.
        """
        gas_costs = cls.gas_costs()

        def fn(
            *,
            target_warm: bool = False,
            delegated: bool = False,
            delegation_warm: bool = False,
        ) -> int:
            gas = (
                gas_costs.WARM_ACCESS
                if target_warm
                else gas_costs.COLD_ACCOUNT_ACCESS
            )
            if delegated:
                gas += (
                    gas_costs.WARM_ACCESS
                    if delegation_warm
                    else gas_costs.COLD_ACCOUNT_ACCESS
                )
            return gas

        return fn

    @classmethod
    def frame_transaction_intrinsic_cost_calculator(
        cls,
    ) -> FrameTransactionIntrinsicCostCalculator:
        """
        Frame transaction intrinsic cost is introduced.

        The intrinsic cost is the base cost, the per-frame cost, the
        verification cost of each signature entry, the value transfer
        cost of each qualifying value-bearing frame, and the calldata
        cost of the charged byte fields. The transaction's derived gas
        limit is the larger of the intrinsic cost plus the frame gas
        limits in both dimensions and the calldata floor anchor plus
        the frame state gas limits.
        """
        calldata_gas_calculator = cls.calldata_gas_calculator()
        floor_cost_calculator = (
            cls.frame_transaction_data_floor_cost_calculator()
        )

        def fn(
            *,
            frames: Sequence[FrameGasInfo] | int,
            signatures: Sequence[FrameSignatureGasInfo] = (),
            sender: BytesConvertible | None = None,
            return_cost_deducted_prior_execution: bool = False,
        ) -> int:
            frame_list = cls._frame_list(frames)
            intrinsic_cost = cls._frame_transaction_base_cost(
                frame_list, signatures, sender
            ) + sum(
                calldata_gas_calculator(data=data)
                for data in cls._frame_transaction_charged_bytes(
                    frame_list, signatures
                )
            )

            if return_cost_deducted_prior_execution:
                return intrinsic_cost

            total_state_gas = sum(
                int(frame.state_gas_limit) for frame in frame_list
            )
            standard_gas_limit = (
                intrinsic_cost
                + sum(int(frame.gas_limit) for frame in frame_list)
                + total_state_gas
            )
            return max(
                standard_gas_limit,
                floor_cost_calculator(
                    frames=frame_list, signatures=signatures, sender=sender
                )
                + total_state_gas,
            )

        return fn

    @classmethod
    def pre_allocation(cls) -> Mapping:
        """Pre-allocate the expiry verifier contract."""
        return {
            EXPIRY_VERIFIER_ADDRESS: {
                # EIP-8141 installs only the runtime code at
                # activation; the nonce stays zero.
                "nonce": 0,
                "code": EXPIRY_VERIFIER_BYTECODE,
            }
        } | super(EIP8141, cls).pre_allocation()  # type: ignore

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """Pre-allocate the expiry verifier contract."""
        return {
            EXPIRY_VERIFIER_ADDRESS: {
                # EIP-8141 installs only the runtime code at
                # activation; the nonce stays zero.
                "nonce": 0,
                "code": EXPIRY_VERIFIER_BYTECODE,
            }
        } | super(EIP8141, cls).pre_allocation_blockchain()  # type: ignore
