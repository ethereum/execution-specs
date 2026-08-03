"""
Measure the gas cost of CALL / CALLCODE / DELEGATECALL with CodeGasMeasure,
across value-transfer and memory-expansion variants. The callee records the
gas it was forwarded.

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

@manually-enhanced: Do not overwrite. Nested call gas via CodeGasMeasure.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    CodeGasMeasure,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

FORWARD_BUFFER = 100  # margin forwarded beyond the callee's own gas cost
MEMORY_SIZE = 0x1F40  # args/ret buffer size for memory variants
CALL_VALUE = 0xA
CALLER_BALANCE = 100


@pytest.mark.ported_from(
    [
        "state_tests/stEIP150singleCodeGasPrices/RawCallGasFiller.json",
        "state_tests/stEIP150singleCodeGasPrices/RawCallGasValueTransferFiller.json",  # noqa: E501
        "state_tests/stEIP150singleCodeGasPrices/RawCallMemoryGasFiller.json",
        "state_tests/stEIP150singleCodeGasPrices/RawCallGasValueTransferMemoryFiller.json",  # noqa: E501
        "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasFiller.json",
        "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasValueTransferFiller.json",  # noqa: E501
        "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasMemoryFiller.json",
        "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasValueTransferMemoryFiller.json",  # noqa: E501
        "state_tests/stEIP150singleCodeGasPrices/RawDelegateCallGasFiller.json",
        "state_tests/stEIP150singleCodeGasPrices/RawDelegateCallGasMemoryFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "opcode, value, memory",
    [
        pytest.param(Op.CALL, 0, False, id="raw_call_gas"),
        pytest.param(
            Op.CALL, CALL_VALUE, False, id="raw_call_gas_value_transfer"
        ),
        pytest.param(Op.CALL, 0, True, id="raw_call_memory_gas"),
        pytest.param(
            Op.CALL, CALL_VALUE, True, id="raw_call_gas_value_transfer_memory"
        ),
        pytest.param(Op.CALLCODE, 0, False, id="raw_call_code_gas"),
        pytest.param(
            Op.CALLCODE,
            CALL_VALUE,
            False,
            id="raw_call_code_gas_value_transfer",
        ),
        pytest.param(Op.CALLCODE, 0, True, id="raw_call_code_gas_memory"),
        pytest.param(
            Op.CALLCODE,
            CALL_VALUE,
            True,
            id="raw_call_code_gas_value_transfer_memory",
        ),
        pytest.param(Op.DELEGATECALL, 0, False, id="raw_delegate_call_gas"),
        pytest.param(
            Op.DELEGATECALL, 0, True, id="raw_delegate_call_gas_memory"
        ),
    ],
)
def test_raw_call_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    value: int,
    memory: bool,
) -> None:
    """Measure call-family gas, with the callee recording forwarded gas."""
    stipend = fork.gas_costs().CALL_STIPEND if value else 0
    mem = MEMORY_SIZE if memory else 0

    # The callee writes a cold (zero->non-zero) slot; SSTORE cost depends only
    # on that transition, not the value, so a placeholder new_value suffices to
    # size the gas to forward (large under EIP-8037 state gas).
    callee_store = Op.SSTORE(
        key=0x2,
        value=Op.GAS,
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    forward_gas = callee_store.gas_cost(fork) + FORWARD_BUFFER
    callee = pre.deploy_contract(code=callee_store + Op.STOP)

    # Callee records the gas it received: forwarded gas plus the value-transfer
    # stipend, minus the GAS opcode it executes.
    callee_gas_seen = forward_gas + stipend - Op.GAS.gas_cost(fork)

    if opcode == Op.DELEGATECALL:
        call_code = Op.DELEGATECALL(
            gas=forward_gas,
            address=callee,
            args_offset=0x0,
            args_size=mem,
            ret_offset=0x0,
            ret_size=mem,
            address_warm=False,
            new_memory_size=mem,
        )
    else:
        call_code = opcode(
            gas=forward_gas,
            address=callee,
            value=value,
            args_offset=0x0,
            args_size=mem,
            ret_offset=0x0,
            ret_size=mem,
            address_warm=False,
            value_transfer=value > 0,
            account_new=False,
            new_memory_size=mem,
        )
    caller = pre.deploy_contract(
        code=CodeGasMeasure(
            code=call_code,
            extra_stack_items=1,
            sstore_key=0x1,
        ),
        balance=CALLER_BALANCE,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        state_gas_reservoir=0,
    )

    # Measured cost = the call's own cost plus the callee's consumption; the
    # value-transfer stipend is forwarded free, not charged to the caller.
    call_gas = call_code.gas_cost(fork) + callee_store.gas_cost(fork) - stipend

    # CALL runs the callee in its own context (slot 2 in the callee); CALLCODE
    # and DELEGATECALL run it in the caller's context (slot 2 in the caller).
    if opcode == Op.CALL:
        callee_storage = {0x2: callee_gas_seen}
        caller_storage = {0x1: call_gas}
    else:
        callee_storage = {}
        caller_storage = {0x1: call_gas, 0x2: callee_gas_seen}

    post = {
        callee: Account(storage=callee_storage),
        caller: Account(storage=caller_storage),
    }

    state_test(pre=pre, post=post, tx=tx)
