"""Strategies and helpers for driving an EIP-8037 `GasMeter` directly."""

from types import ModuleType
from typing import Any, List, NamedTuple, Optional, Set, Tuple

from ethereum_types.numeric import Uint
from hypothesis import strategies as st

POOL_BOUND = 1 << 24
AMOUNT_BOUND = 1 << 22

MeterOp = Tuple[str, int]

CHARGES = ("regular", "state", "spill")
CHARGES_AND_REFUNDS = CHARGES + ("refund",)


class FrameStub:
    """
    Stand-in for `Evm` holding only what the gas functions and
    `incorporate_child` read.
    """

    def __init__(self, gas_meter: Any) -> None:
        self.gas_meter = gas_meter
        self.error: Any = None
        self.logs: Tuple[Any, ...] = ()
        self.accounts_to_delete: Set[Any] = set()
        self.accessed_addresses: Set[Any] = set()
        self.accessed_storage_keys: Set[Any] = set()


def fresh_frame(gas: ModuleType, gas_left: int, reservoir: int) -> FrameStub:
    """Return a frame as it enters, with its baseline at the reservoir."""
    return FrameStub(
        gas.GasMeter(
            gas_left=Uint(gas_left),
            state_gas_left=Uint(reservoir),
            state_gas_baseline=Uint(reservoir),
        )
    )


class MeterFields(NamedTuple):
    """Every `GasMeter` field as a plain int."""

    gas_left: int
    state_gas_left: int
    state_gas_baseline: int
    refund_counter: int
    state_gas_spilled: int
    state_gas_committed_spill: int


def meter_fields(meter: Any) -> MeterFields:
    """Read every field of `meter`, for exact comparisons."""
    return MeterFields(
        gas_left=int(meter.gas_left),
        state_gas_left=int(meter.state_gas_left),
        state_gas_baseline=int(meter.state_gas_baseline),
        refund_counter=int(meter.refund_counter),
        state_gas_spilled=int(meter.state_gas_spilled),
        state_gas_committed_spill=int(meter.state_gas_committed_spill),
    )


def pools() -> st.SearchStrategy[int]:
    """Return pool sizes, weighted toward empty and small pools."""
    # 63, 64 and 65 sit around the point where the 1/64 a parent keeps from
    # a child's grant first becomes nonzero.
    return st.one_of(
        st.sampled_from(
            [0, 1, 2, 63, 64, 65, AMOUNT_BOUND // 2, AMOUNT_BOUND]
        ),
        st.integers(min_value=0, max_value=AMOUNT_BOUND),
        st.integers(min_value=0, max_value=POOL_BOUND),
    )


def amounts() -> st.SearchStrategy[int]:
    """Return charge and refund amounts, weighted toward small values."""
    return st.one_of(
        st.sampled_from([0, 1, 2, AMOUNT_BOUND]),
        st.integers(min_value=0, max_value=AMOUNT_BOUND),
    )


def op_lists(
    kinds: Tuple[str, ...], max_size: int = 12
) -> st.SearchStrategy[List[MeterOp]]:
    """Return sequences of `(kind, amount)` meter operations."""
    return st.lists(
        st.tuples(st.sampled_from(kinds), amounts()), max_size=max_size
    )


def apply_ops(
    gas: ModuleType,
    frame: FrameStub,
    ops: List[MeterOp],
    applied: Optional[List[MeterOp]] = None,
) -> Tuple[int, int, int]:
    """
    Apply meter operations and return the regular gas charged, state gas
    charged and state gas refunded.

    Each operation that runs is appended to `applied`, as a plain charge
    or refund of its final amount, so it can be replayed in another frame.
    """
    meter = frame.gas_meter
    regular = state = refunded = 0
    # Skip charges the pools cannot cover, where a real frame runs out.
    for kind, amount in ops:
        if kind == "regular":
            if int(meter.gas_left) < amount:
                continue
            gas.charge_gas(frame, Uint(amount))
            regular += amount
        elif kind == "spill":
            # Size the charge past the reservoir so the spill branch runs.
            kind = "state"
            amount = int(meter.state_gas_left) + min(
                amount, int(meter.gas_left)
            )
            gas.charge_state_gas(frame, Uint(amount))
            state += amount
        elif kind == "state":
            if int(meter.gas_left) + int(meter.state_gas_left) < amount:
                continue
            gas.charge_state_gas(frame, Uint(amount))
            state += amount
        elif kind == "refund":
            gas.credit_state_gas_refund(meter, Uint(amount))
            refunded += amount
        else:
            raise ValueError(f"unknown meter op: {kind}")
        if applied is not None:
            applied.append((kind, amount))
    return regular, state, refunded
