"""
Call the ecrecover precompile with CALL and CALLCODE.

Ported from:
state_tests/stPreCompiledContracts2/CallEcrecover0_0inputFiller.json
state_tests/stPreCompiledContracts2/CallEcrecover0_Gas2999Filler.json
state_tests/stPreCompiledContracts2/CallEcrecover0_gas3000Filler.json
state_tests/stPreCompiledContracts2/CallEcrecover0_NoGasFiller.json
state_tests/stPreCompiledContracts2/CallEcrecover0_completeReturnValueFiller.json
state_tests/stPreCompiledContracts2/CallEcrecover0_overlappingInputOutputFiller.json
state_tests/stPreCompiledContracts2/CallEcrecover2Filler.json
state_tests/stPreCompiledContracts2/CallEcrecoverCheckLengthFiller.json
state_tests/stPreCompiledContracts2/CallEcrecoverCheckLengthWrongVFiller.json
state_tests/stPreCompiledContracts2/CALLCODEEcrecover0_0inputFiller.json
state_tests/stPreCompiledContracts2/CALLCODEEcrecover0_Gas2999Filler.json
state_tests/stPreCompiledContracts2/CALLCODEEcrecover0_gas3000Filler.json
state_tests/stPreCompiledContracts2/CALLCODEEcrecover0_NoGasFiller.json
state_tests/stPreCompiledContracts2/CALLCODEEcrecover0_completeReturnValueFiller.json
state_tests/stPreCompiledContracts2/CALLCODEEcrecover0_overlappingInputOutputFiller.json
state_tests/stPreCompiledContracts2/CALLCODEEcrecover2Filler.json

@manually-enhanced: Do not overwrite. Compares against the constant
signer instead of ORIGIN; slots start at a sentinel. EIP-7928 block
access list expectations for `no_gas`: the value-bearing call fails on
the stipend, so the precompile is listed with no balance change and the
offered value stays with the caller.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessListExpectation,
    Bytecode,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

ECRECOVER = Address(0x01)
MESSAGE_HASH = (
    0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C
)
V = 28
R = 0x73B1693892219D736CABA55BDB67216E485557EA6B6AF75F37096C9AA6A5A75F
S = 0xEEB940B1D03B21E36B0E47E79769F095FE2AB855BD91E3A38756B7D75A9C4549
EXPECTED_SIGNER = Address(0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
RETURN_FILLER = (
    0x1122334455667788990011223344556677889900112233445566778899001122
)
SENTINEL = 12
TARGET_BALANCE = 0x1312D00
TX_VALUE = 0x186A0


def signature(v: int = V) -> Bytecode:
    """Store hash, v, r and s as four words at offset 0."""
    return (
        Op.MSTORE(offset=0x0, value=MESSAGE_HASH)
        + Op.MSTORE(offset=0x20, value=v)
        + Op.MSTORE(offset=0x40, value=R)
        + Op.MSTORE(offset=0x60, value=S)
    )


def store_recovered(ret_offset: int) -> Bytecode:
    """Store the recovered address and whether it is the signer."""
    return Op.SSTORE(
        key=0x0, value=Op.MOD(Op.MLOAD(offset=ret_offset), 2**160)
    ) + Op.SSTORE(key=0x1, value=Op.EQ(EXPECTED_SIGNER, Op.SLOAD(key=0x0)))


@pytest.mark.ported_from(
    [
        "state_tests/stPreCompiledContracts2/CallEcrecover0_0inputFiller.json",
        "state_tests/stPreCompiledContracts2/CallEcrecover0_Gas2999Filler.json",
        "state_tests/stPreCompiledContracts2/CallEcrecover0_gas3000Filler.json",
        "state_tests/stPreCompiledContracts2/CallEcrecover0_NoGasFiller.json",
        "state_tests/stPreCompiledContracts2/CallEcrecover0_completeReturnValueFiller.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CallEcrecover0_overlappingInputOutputFiller.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CallEcrecover2Filler.json",
        "state_tests/stPreCompiledContracts2/CallEcrecoverCheckLengthFiller.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CallEcrecoverCheckLengthWrongVFiller.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CALLCODEEcrecover0_0inputFiller.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CALLCODEEcrecover0_Gas2999Filler.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CALLCODEEcrecover0_gas3000Filler.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CALLCODEEcrecover0_NoGasFiller.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CALLCODEEcrecover0_completeReturnValueFiller.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CALLCODEEcrecover0_overlappingInputOutputFiller.json",  # noqa: E501
        "state_tests/stPreCompiledContracts2/CALLCODEEcrecover2Filler.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "case",
    [
        "0input",
        "gas2999",
        "gas3000",
        "no_gas",
        "complete_return_value",
        "overlapping_input_output",
        "ecrecover2",
        "check_length",
        "check_length_wrong_v",
    ],
)
@pytest.mark.parametrize("opcode", [Op.CALL, Op.CALLCODE])
def test_ecrecover_precompile(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    case: str,
) -> None:
    """Call ecrecover and store the success flag and the output."""
    code: Bytecode
    storage: dict[int, int | Address]
    if case == "0input":
        code = Op.SSTORE(
            key=0x2,
            value=opcode(
                gas=300_000,
                address=ECRECOVER,
                args_size=0x80,
                ret_offset=0x80,
                ret_size=0x20,
            ),
        ) + store_recovered(ret_offset=0x80)
        storage = {0: 0, 1: 0, 2: 1}
    elif case in ("gas2999", "gas3000"):
        gas = fork.gas_costs().PRECOMPILE_ECRECOVER
        if case == "gas2999":
            gas -= 1
        code = (
            signature()
            + Op.SSTORE(
                key=0x2,
                value=opcode(
                    gas=gas,
                    address=ECRECOVER,
                    args_size=0x80,
                    ret_offset=0x80,
                    ret_size=0x20,
                ),
            )
            + store_recovered(ret_offset=0x80)
        )
        success = int(case == "gas3000")
        storage = {
            0: EXPECTED_SIGNER if success else 0,
            1: success,
            2: success,
        }
    elif case == "no_gas":
        code = (
            signature()
            + Op.SSTORE(
                key=0x2,
                value=opcode(
                    gas=0,
                    address=ECRECOVER,
                    value=1,
                    args_size=0x80,
                    ret_offset=0x80,
                    ret_size=0x20,
                ),
            )
            + store_recovered(ret_offset=0x80)
        )
        storage = {0: 0, 1: 0, 2: 0}
    elif case == "complete_return_value":
        code = (
            signature()
            + Op.SSTORE(
                key=0x2,
                value=opcode(
                    gas=3000,
                    address=ECRECOVER,
                    args_size=0x80,
                    ret_offset=0x80,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x80))
            + Op.SSTORE(
                key=0x1, value=Op.EQ(EXPECTED_SIGNER, Op.SLOAD(key=0x0))
            )
        )
        storage = {0: EXPECTED_SIGNER, 1: 1, 2: 1}
    elif case == "overlapping_input_output":
        code = (
            signature()
            + Op.SSTORE(
                key=0x2,
                value=opcode(
                    gas=300_000,
                    address=ECRECOVER,
                    args_size=0x80,
                    ret_offset=0x40,
                    ret_size=0x20,
                ),
            )
            + store_recovered(ret_offset=0x40)
        )
        storage = {0: EXPECTED_SIGNER, 1: 1, 2: 1}
    elif case == "ecrecover2":
        # r and s are shifted by one byte, corrupting v.
        code = (
            Op.MSTORE(offset=0x0, value=MESSAGE_HASH)
            + Op.MSTORE(offset=0x20, value=V)
            + Op.MSTORE(offset=0x21, value=R)
            + Op.MSTORE(offset=0x41, value=S)
            + Op.SSTORE(
                key=0x2,
                value=opcode(
                    gas=100_000,
                    address=ECRECOVER,
                    args_size=0x61,
                    ret_offset=0x61,
                    ret_size=0x20,
                ),
            )
            + store_recovered(ret_offset=0x61)
        )
        storage = {0: 0, 1: 0, 2: 1}
    elif case in ("check_length", "check_length_wrong_v"):
        valid = case == "check_length"
        code = (
            Op.MSTORE(offset=0x80, value=RETURN_FILLER)
            + signature(v=V if valid else V + 1)
            + Op.SSTORE(
                key=0x2,
                value=opcode(
                    gas=300_000,
                    address=ECRECOVER,
                    args_size=0x80,
                    ret_offset=0x80,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x80))
            + Op.SSTORE(key=0x1, value=Op.MSIZE)
        )
        storage = {
            0: EXPECTED_SIGNER if valid else RETURN_FILLER,
            1: 0xA0,
            2: 1,
        }
    else:
        raise ValueError(f"unknown case {case}")

    sender = pre.fund_eoa()
    target = pre.deploy_contract(
        code=code,
        storage={0: SENTINEL, 1: SENTINEL, 2: SENTINEL},
        balance=TARGET_BALANCE,
    )

    tx = Transaction(sender=sender, to=target, value=TX_VALUE)

    post = {
        target: Account(storage=storage, balance=TARGET_BALANCE + TX_VALUE)
    }

    expected_block_access_list = None
    if case == "no_gas" and fork.is_eip_enabled(7928):
        expected_block_access_list = BlockAccessListExpectation(
            account_expectations={
                sender: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                target: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=TARGET_BALANCE + TX_VALUE,
                        )
                    ],
                    storage_changes=[
                        BalStorageSlot(
                            slot=slot,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0
                                )
                            ],
                        )
                        for slot in (0, 1, 2)
                    ],
                ),
                ECRECOVER: BalAccountExpectation.empty(),
            }
        )

    state_test(
        pre=pre,
        post=post,
        tx=tx,
        expected_block_access_list=expected_block_access_list,
    )
