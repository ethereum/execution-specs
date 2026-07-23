"""
Gas forwarded to a subcall that asks for more than is available: the EIP-150
"all but one 64th" rule, across CALL / CALLCODE / DELEGATECALL and their
value-transfer and memory-expansion variants.

Ported from:
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

@manually-enhanced: Do not overwrite. The ported fillers pinned the forwarded
gas as an absolute number tied to the tx gas limit (fork-fragile via the
intrinsic). Reframed so an outer call caps the caller frame at a known gas
budget, the callee returns its observed GAS up to the top frame (no lower-frame
SSTORE state-gas trap), and the expected value is derived from the fork:
`all_but_one_64th(caller_gas - call.gas_cost(fork))`.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CALLER_GAS = 100_000
CALL_VALUE = 0xA
MEMORY_SIZE = 0x1F40  # 8000-byte args/ret buffer for the memory variants


@pytest.mark.ported_from(
    [
        "state_tests/stEIP150singleCodeGasPrices/RawCallGasAskFiller.json",
        "state_tests/stEIP150singleCodeGasPrices/RawCallGasValueTransferAskFiller.json",  # noqa: E501
        "state_tests/stEIP150singleCodeGasPrices/RawCallMemoryGasAskFiller.json",  # noqa: E501
        "state_tests/stEIP150singleCodeGasPrices/RawCallGasValueTransferMemoryAskFiller.json",  # noqa: E501
        "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasAskFiller.json",
        "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasMemoryAskFiller.json",  # noqa: E501
        "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasValueTransferAskFiller.json",  # noqa: E501
        "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasValueTransferMemoryAskFiller.json",  # noqa: E501
        "state_tests/stEIP150singleCodeGasPrices/RawDelegateCallGasAskFiller.json",  # noqa: E501
        "state_tests/stEIP150singleCodeGasPrices/RawDelegateCallGasMemoryAskFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "opcode, value, memory",
    [
        pytest.param(Op.CALL, 0, False, id="raw_call_gas_ask"),
        pytest.param(
            Op.CALL, CALL_VALUE, False, id="raw_call_gas_value_transfer_ask"
        ),
        pytest.param(Op.CALL, 0, True, id="raw_call_memory_gas_ask"),
        pytest.param(
            Op.CALL,
            CALL_VALUE,
            True,
            id="raw_call_gas_value_transfer_memory_ask",
        ),
        pytest.param(Op.CALLCODE, 0, False, id="raw_call_code_gas_ask"),
        pytest.param(Op.CALLCODE, 0, True, id="raw_call_code_gas_memory_ask"),
        pytest.param(
            Op.CALLCODE,
            CALL_VALUE,
            False,
            id="raw_call_code_gas_value_transfer_ask",
        ),
        pytest.param(
            Op.CALLCODE,
            CALL_VALUE,
            True,
            id="raw_call_code_gas_value_transfer_memory_ask",
        ),
        pytest.param(
            Op.DELEGATECALL, 0, False, id="raw_delegate_call_gas_ask"
        ),
        pytest.param(
            Op.DELEGATECALL, 0, True, id="raw_delegate_call_gas_memory_ask"
        ),
    ],
)
def test_raw_call_gas_ask(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    value: int,
    memory: bool,
) -> None:
    """A subcall asking for more gas than available receives 63/64 of it."""
    sender = pre.fund_eoa()

    # Callee returns the gas it observed on entry back to the caller.
    gas_return_contract = pre.deploy_contract(
        code=Op.MSTORE(0, Op.GAS) + Op.RETURN(0, 32),
    )

    mem = MEMORY_SIZE if memory else 0
    ret_size = MEMORY_SIZE if memory else 32  # must fit the 32-byte GAS return
    new_memory_size = MEMORY_SIZE if memory else 32

    # The caller asks for "all" gas (the default Op.GAS operand), which exceeds
    # what remains after the call's own cost, so the 63/64 cap kicks in.
    if opcode == Op.DELEGATECALL:
        caller_call_code = Op.DELEGATECALL(
            address=gas_return_contract,
            args_offset=0,
            args_size=mem,
            ret_offset=0,
            ret_size=ret_size,
            address_warm=False,
            new_memory_size=new_memory_size,
        )
    else:
        caller_call_code = opcode(
            address=gas_return_contract,
            value=value,
            args_offset=0,
            args_size=mem,
            ret_offset=0,
            ret_size=ret_size,
            address_warm=False,
            value_transfer=value > 0,
            account_new=False,
            new_memory_size=new_memory_size,
        )
    caller = pre.deploy_contract(
        code=caller_call_code + Op.RETURN(0, 32),
        balance=value,
    )

    # An outer call pins the caller frame's gas to a known budget, so the
    # forwarded amount does not depend on the tx gas limit.
    entry = pre.deploy_contract(
        code=Op.SSTORE(0, 1)
        + Op.CALL(
            gas=CALLER_GAS,
            address=caller,
            value=0,
            args_offset=0,
            args_size=0,
            ret_offset=0,
            ret_size=32,
        )
        + Op.SSTORE(1, Op.MLOAD(0)),
    )

    # EIP-150 forwards "all but one 64th" of the gas left after the call's own
    # cost; a value-bearing call additionally hands the callee the stipend.
    stipend = fork.gas_costs().CALL_STIPEND if value else 0
    available = CALLER_GAS - caller_call_code.gas_cost(fork)
    forwarded = available - available // 64
    expected_gas = forwarded + stipend - Op.GAS.gas_cost(fork)

    tx = Transaction(sender=sender, to=entry)

    post = {entry: Account(storage={0: 1, 1: expected_gas})}

    state_test(pre=pre, post=post, tx=tx)
