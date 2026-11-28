"""
STATICCALL the ECRECOVER precompile and check what it writes back.

Ported from:
state_tests/stStaticCall/static_CallEcrecover0_completeReturnValueFiller.json
state_tests/stStaticCall/static_CallEcrecover0_gas3000Filler.json
state_tests/stStaticCall/static_CallEcrecover0_Gas2999Filler.json
state_tests/stStaticCall/static_CallEcrecover0_NoGasFiller.json
state_tests/stStaticCall/static_CallEcrecover0_overlappingInputOutputFiller.json
state_tests/stStaticCall/static_CallEcrecover2Filler.json
state_tests/stStaticCall/static_CallEcrecoverCheckLengthFiller.json
state_tests/stStaticCall/static_CallEcrecoverCheckLengthWrongVFiller.json

@manually-enhanced: Do not overwrite. Merged; signer is a constant.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

ECRECOVER = 0x1
GAS_MARGIN = 10_000
MESSAGE_HASH = (
    0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C
)
SIGNATURE_R = (
    0x73B1693892219D736CABA55BDB67216E485557EA6B6AF75F37096C9AA6A5A75F
)
SIGNATURE_S = (
    0xEEB940B1D03B21E36B0E47E79769F095FE2AB855BD91E3A38756B7D75A9C4549
)
SIGNER = Address(0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
SENTINEL = 0x1122334455667788990011223344556677889900112233445566778899001122
OUTPUT_SLOT = 0
RECOVERED_SLOT = 1
SUCCESS_SLOT = 2
MSIZE_SLOT = 3


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_CallEcrecover0_completeReturnValueFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_CallEcrecover0_gas3000Filler.json",
        "state_tests/stStaticCall/static_CallEcrecover0_Gas2999Filler.json",
        "state_tests/stStaticCall/static_CallEcrecover0_NoGasFiller.json",
        "state_tests/stStaticCall/static_CallEcrecover0_overlappingInputOutputFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_CallEcrecover2Filler.json",
        "state_tests/stStaticCall/static_CallEcrecoverCheckLengthFiller.json",
        "state_tests/stStaticCall/static_CallEcrecoverCheckLengthWrongVFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "gas_offset, v, misaligned, ret_offset, succeeds, recovers",
    [
        pytest.param(
            GAS_MARGIN, 28, False, 0x80, True, True,
            id="complete_return_value",
        ),
        pytest.param(0, 28, False, 0x80, True, True, id="gas3000"),
        pytest.param(-1, 28, False, 0x80, False, False, id="gas2999"),
        pytest.param(None, 28, False, 0x80, False, False, id="no_gas"),
        pytest.param(
            GAS_MARGIN, 28, False, 0x40, True, True,
            id="overlapping_input_output",
        ),
        pytest.param(
            GAS_MARGIN, 28, True, 0x61, True, False, id="misaligned_input"
        ),
        pytest.param(GAS_MARGIN, 29, False, 0x80, True, False, id="wrong_v"),
    ],
)  # fmt: skip
def test_static_call_ecrecover(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_offset: int | None,
    v: int,
    misaligned: bool,
    ret_offset: int,
    succeeds: bool,
    recovers: bool,
) -> None:
    """
    Verify the success flag, the output word and the memory size after a
    STATICCALL to ECRECOVER given its gas cost plus `gas_offset`, or no
    gas when `gas_offset` is None.

    The output area holds a sentinel beforehand, so a call that fails or
    returns no data leaves it in place. With a `ret_offset` of 0x40, the
    output area is the input's R word, which replaces the sentinel.
    """
    call_gas = (
        0
        if gas_offset is None
        else fork.gas_costs().PRECOMPILE_ECRECOVER + gas_offset
    )
    r_offset = 0x21 if misaligned else 0x40
    input_size = r_offset + 0x40
    code = (
        Op.MSTORE(ret_offset, SENTINEL)
        + Op.MSTORE(0x0, MESSAGE_HASH)
        + Op.MSTORE(0x20, v)
        + Op.MSTORE(r_offset, SIGNATURE_R)
        + Op.MSTORE(r_offset + 0x20, SIGNATURE_S)
        + Op.SSTORE(
            SUCCESS_SLOT,
            Op.STATICCALL(
                gas=call_gas,
                address=ECRECOVER,
                args_size=input_size,
                ret_offset=ret_offset,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(OUTPUT_SLOT, Op.MLOAD(ret_offset))
        + Op.SSTORE(RECOVERED_SLOT, Op.EQ(SIGNER, Op.MLOAD(ret_offset)))
        + Op.SSTORE(MSIZE_SLOT, Op.MSIZE)
        + Op.STOP
    )
    contract = pre.deploy_contract(code=code)

    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    output = SIGNER if recovers else SENTINEL
    memory_size = (max(input_size, ret_offset + 0x20) + 31) // 32 * 32
    post = {
        contract: Account(
            storage={
                SUCCESS_SLOT: int(succeeds),
                OUTPUT_SLOT: output,
                RECOVERED_SLOT: int(recovers),
                MSIZE_SLOT: memory_size,
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)
