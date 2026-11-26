"""
Test the gas a call charges its caller and forwards to its callee.

Ported from:
state_tests/stEIP150singleCodeGasPrices/RawCallGasFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCallGasValueTransferFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCallMemoryGasFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCallGasValueTransferMemoryFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasValueTransferFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasMemoryFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasValueTransferMemoryFiller.json
state_tests/stEIP150singleCodeGasPrices/RawDelegateCallGasFiller.json
state_tests/stEIP150singleCodeGasPrices/RawDelegateCallGasMemoryFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCallGasAskFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCallGasValueTransferAskFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCallMemoryGasAskFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCallGasValueTransferMemoryAskFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasAskFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasMemoryAskFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasValueTransferAskFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasValueTransferMemoryAskFiller.json
state_tests/stEIP150singleCodeGasPrices/RawDelegateCallGasAskFiller.json
state_tests/stEIP150singleCodeGasPrices/RawDelegateCallGasMemoryAskFiller.json

@manually-enhanced: Do not overwrite. The twenty fillers differed only
in the call opcode, a value transfer, an 8000-byte argument and return
window, and whether the call asked for less gas than the caller held or
for more. `entry` calls `caller` with a fixed `CALLER_GAS`, so what the
caller holds does not depend on the transaction. `caller` makes the
call to `reporter`, which returns the gas it received; `caller` then
returns that together with its own remaining gas, and `entry` stores
both and the success flag. The ask below what is available is forwarded
as is. Since EIP-150 an ask above it is clamped to all but one 64th of
what is left after the call's own cost; before EIP-150 it runs the
caller out of gas. The caller's remaining gas is the same either way,
since the unused grant returns. The expected values come from the
framework gas calculation, with warmth, value transfer and memory size
as call metadata.
"""

from typing import Generator

import pytest
from _pytest.mark.structures import ParameterSet
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op, Opcode

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 0x0BAD
SUCCESS_SLOT = 0
CALLEE_GAS_SLOT = 1
CALLER_GAS_SLOT = 2

CALL_VALUE = 0xA
MEMORY_SIZE = 0x1F40
# Gas `entry` hands `caller`, and the two asks of the fillers: one well
# below what `caller` has left for the call, one far above it.
CALLER_GAS = 100_000
ASKS = {"below_available": 30_000, "above_available": 3_000_000}


def call_variants_by_fork(
    fork: Fork,
) -> Generator[ParameterSet, None, None]:
    """Yield every call opcode on `fork`, with and without value."""
    for call_opcode in fork.call_opcodes():
        name = call_opcode._name_.lower()
        yield pytest.param(call_opcode, False, id=name)
        if call_opcode in (Op.CALL, Op.CALLCODE):
            yield pytest.param(call_opcode, True, id=f"{name}_with_value")


pytestmark = [
    pytest.mark.ported_from(
        [
            "state_tests/stEIP150singleCodeGasPrices/RawCallGasFiller.json",
            "state_tests/stEIP150singleCodeGasPrices/RawCallGasValueTransferFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCallMemoryGasFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCallGasValueTransferMemoryFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasValueTransferFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasMemoryFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasValueTransferMemoryFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawDelegateCallGasFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawDelegateCallGasMemoryFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCallGasAskFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCallGasValueTransferAskFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCallMemoryGasAskFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCallGasValueTransferMemoryAskFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasAskFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasMemoryAskFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasValueTransferAskFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasValueTransferMemoryAskFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawDelegateCallGasAskFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawDelegateCallGasMemoryAskFiller.json",  # noqa: E501
        ],
    ),
    pytest.mark.valid_from("Frontier"),
    pytest.mark.parametrize_by_fork(
        "call_opcode, value_transfer", call_variants_by_fork
    ),
]


@pytest.mark.parametrize("gas_ask", list(ASKS))
@pytest.mark.parametrize(
    "memory_expansion", [False, True], ids=["no_memory", "memory"]
)
def test_raw_call_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Opcode,
    value_transfer: bool,
    memory_expansion: bool,
    gas_ask: str,
) -> None:
    """Store the gas a call forwards and the gas its caller keeps."""
    reporter_code = Op.MSTORE(0, Op.GAS, new_memory_size=0x20) + Op.RETURN(
        0, 0x20
    )
    reporter = pre.deploy_contract(code=reporter_code)

    value = CALL_VALUE if value_transfer else 0
    args_size = MEMORY_SIZE if memory_expansion else 0
    # The return window must at least hold the reported gas word.
    ret_size = MEMORY_SIZE if memory_expansion else 0x20

    call: Bytecode
    if call_opcode in (Op.CALL, Op.CALLCODE):
        call = call_opcode(
            gas=ASKS[gas_ask],
            address=reporter,
            value=value,
            args_size=args_size,
            ret_size=ret_size,
            address_warm=False,
            value_transfer=value_transfer,
            new_memory_size=ret_size,
        )
    elif call_opcode in (Op.DELEGATECALL, Op.STATICCALL):
        call = call_opcode(
            gas=ASKS[gas_ask],
            address=reporter,
            args_size=args_size,
            ret_size=ret_size,
            address_warm=False,
            new_memory_size=ret_size,
        )
    else:
        raise ValueError(f"Unknown call opcode: {call_opcode}")

    caller = pre.deploy_contract(
        code=call + Op.MSTORE(0x20, Op.GAS) + Op.RETURN(0, 0x40),
        balance=value,
    )
    entry = pre.deploy_contract(
        code=Op.SSTORE(
            SUCCESS_SLOT,
            Op.CALL(gas=CALLER_GAS, address=caller, ret_size=0x40),
        )
        + Op.SSTORE(CALLEE_GAS_SLOT, Op.MLOAD(0))
        + Op.SSTORE(CALLER_GAS_SLOT, Op.MLOAD(0x20))
        + Op.STOP,
        storage=dict.fromkeys(
            (SUCCESS_SLOT, CALLEE_GAS_SLOT, CALLER_GAS_SLOT), SENTINEL
        ),
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=entry,
        protected=fork.supports_protected_txs(),
    )

    # A value-bearing call hands the callee a stipend on top of the ask.
    stipend = fork.call_value_stipend() if value_transfer else 0
    available = CALLER_GAS - call.gas_cost(fork)
    # EIP-150 forwards at most all but one 64th of what is left after the
    # call's own cost. Before it, the ask is charged in full up front.
    forwardable = (
        available - available // 64 if fork.is_eip_enabled(150) else available
    )
    assert ASKS["below_available"] < forwardable < ASKS["above_available"]

    entry_storage: dict[int, int]
    if gas_ask == "above_available" and not fork.is_eip_enabled(150):
        # `caller` runs out of gas and returns nothing.
        entry_storage = {
            SUCCESS_SLOT: 0,
            CALLEE_GAS_SLOT: 0,
            CALLER_GAS_SLOT: 0,
        }
    else:
        forwarded = min(ASKS[gas_ask], forwardable)
        # The unused grant and stipend return to `caller`, so it keeps the
        # same gas whatever the call forwarded.
        caller_gas = (
            available
            - reporter_code.gas_cost(fork)
            + stipend
            - Op.GAS.gas_cost(fork)
        )
        entry_storage = {
            SUCCESS_SLOT: 1,
            CALLEE_GAS_SLOT: forwarded + stipend - Op.GAS.gas_cost(fork),
            CALLER_GAS_SLOT: caller_gas,
        }

    post = {entry: Account(storage=entry_storage)}

    state_test(pre=pre, post=post, tx=tx)
