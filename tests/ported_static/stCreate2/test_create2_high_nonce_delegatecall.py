"""
Delegate calls CREATE/CREATE2 from an account with max allowed...

Ported from:
state_tests/stCreate2/CREATE2_HighNonceDelegatecallFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreate2/CREATE2_HighNonceDelegatecallFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="A_MaxNonceMinus1_DelegateCall_B_MaxNonceMinus1_Create",
        ),
        pytest.param(
            1,
            0,
            0,
            id="A_MaxNonceMinus1_DelegateCall_B_MaxNonce_Create",
        ),
        pytest.param(
            2,
            0,
            0,
            id="A_MaxNonceMinus1_CallCode_B_MaxNonceMinus1_Create",
        ),
        pytest.param(
            3,
            0,
            0,
            id="A_MaxNonceMinus1_CallCode_B_MaxNonce_Create",
        ),
        pytest.param(
            4,
            0,
            0,
            id="A_MaxNonceMinus1_Call_B_MaxNonceMinus1_Create",
        ),
        pytest.param(
            5,
            0,
            0,
            id="A_MaxNonceMinus1_Call_B_MaxNonce_Create",
        ),
        pytest.param(
            6,
            0,
            0,
            id="A_MaxNonce_DelegateCall_B_MaxNonceMinus1_Create",
        ),
        pytest.param(
            7,
            0,
            0,
            id="A_MaxNonce_DelegateCall_B_MaxNonce_Create",
        ),
        pytest.param(
            8,
            0,
            0,
            id="A_MaxNonce_CallCode_B_MaxNonceMinus1_Create",
        ),
        pytest.param(
            9,
            0,
            0,
            id="A_MaxNonce_CallCode_B_MaxNonce_Create",
        ),
        pytest.param(
            10,
            0,
            0,
            id="A_MaxNonce_Call_B_MaxNonceMinus1_Create",
        ),
        pytest.param(
            11,
            0,
            0,
            id="A_MaxNonce_Call_B_MaxNonce_Create",
        ),
        pytest.param(
            12,
            0,
            0,
            id="A_MaxNonceMinus1_DelegateCall_B_MaxNonceMinus1_Create2",
        ),
        pytest.param(
            13,
            0,
            0,
            id="A_MaxNonceMinus1_DelegateCall_B_MaxNonce_Create2",
        ),
        pytest.param(
            14,
            0,
            0,
            id="A_MaxNonceMinus1_CallCode_B_MaxNonceMinus1_Create2",
        ),
        pytest.param(
            15,
            0,
            0,
            id="A_MaxNonceMinus1_CallCode_B_MaxNonce_Create2",
        ),
        pytest.param(
            16,
            0,
            0,
            id="A_MaxNonceMinus1_Call_B_MaxNonceMinus1_Create2",
        ),
        pytest.param(
            17,
            0,
            0,
            id="A_MaxNonceMinus1_Call_B_MaxNonce_Create2",
        ),
        pytest.param(
            18,
            0,
            0,
            id="A_MaxNonce_DelegateCall_B_MaxNonceMinus1_Create2",
        ),
        pytest.param(
            19,
            0,
            0,
            id="A_MaxNonce_DelegateCall_B_MaxNonce_Create2",
        ),
        pytest.param(
            20,
            0,
            0,
            id="A_MaxNonce_CallCode_B_MaxNonceMinus1_Create2",
        ),
        pytest.param(
            21,
            0,
            0,
            id="A_MaxNonce_CallCode_B_MaxNonce_Create2",
        ),
        pytest.param(
            22,
            0,
            0,
            id="A_MaxNonce_Call_B_MaxNonceMinus1_Create2",
        ),
        pytest.param(
            23,
            0,
            0,
            id="A_MaxNonce_Call_B_MaxNonce_Create2",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2_high_nonce_delegatecall(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Delegate calls CREATE/CREATE2 from an account with max allowed..."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xF79127A3004ABDE26A4CBD80C428CB10F829FA11B54D36E7B326F4F4A5927ACF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[sender] = Account(balance=0x3B9ACA00)
    # Source: yul
    # berlin
    # {
    #   let createtype    := calldataload(0)
    #   let contextnonce  := sload(0xffff)
    #
    #   // initcode: { codecopy(0, 12, 5); return(0, 5); sstore(1, 1) }
    #   mstore(0, 0x6005600c60003960056000f36001600155 )
    #   let addr
    #   if eq(createtype, 0) {
    #     addr := create(0, sub(32, 17), 17)
    #   }
    #   if eq(createtype, 1) {
    #     // We use the context nonce to mimic CREATE's nonce based address calculation and make verification easier  # noqa: E501
    #     addr := create2(0, sub(32, 17), 17, contextnonce)
    #   }
    #   sstore(2, addr)
    #   if gt(addr, 0) { sstore(0xffff, add(contextnonce, 1)) }
    #   mstore(0, addr)
    #   return(0, 32)
    # }
    max_nonce_minus_1 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x0)
        + Op.SLOAD(key=0xFFFF)
        + Op.MSTORE(offset=0x0, value=0x6005600C60003960056000F36001600155)
        + Op.PUSH1[0x0]
        + Op.SWAP2
        + Op.JUMPI(pc=0x5E, condition=Op.EQ(Op.DUP2, 0x0))
        + Op.JUMPDEST
        + Op.PUSH1[0x1]
        + Op.JUMPI(pc=0x4F, condition=Op.EQ)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x2, value=Op.DUP2)
        + Op.JUMPI(pc=0x43, condition=Op.GT(Op.DUP3, 0x0))
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.MSTORE
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0xFFFF, value=Op.ADD)
        + Op.CODESIZE
        + Op.JUMP(pc=0x39)
        + Op.JUMPDEST
        + Op.SWAP1
        + Op.POP
        + Op.CREATE2(value=0x0, offset=0xF, size=0x11, salt=Op.DUP1)
        + Op.SWAP1
        + Op.JUMP(pc=0x2D)
        + Op.JUMPDEST
        + Op.SWAP2
        + Op.POP
        + Op.PUSH1[0x1]
        + Op.CREATE(value=0x0, offset=0xF, size=0x11)
        + Op.SWAP3
        + Op.SWAP1
        + Op.POP
        + Op.JUMP(pc=0x26),
        storage={65535: 0xFFFFFFFFFFFFFFFE},
        nonce=18446744073709551614,
        address=Address(0xCF7DD310DB9459FA2E6EEC97D4B972BA24FF23EB),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   let createtype    := calldataload(0)
    #   let contextnonce  := sload(0xffff)
    #
    #   // initcode: { codecopy(0, 12, 5); return(0, 5); sstore(1, 1) }
    #   mstore(0, 0x6005600c60003960056000f36001600155)
    #   let addr
    #   if eq(createtype, 0) {
    #     addr := create(0, sub(32, 17), 17)
    #   }
    #   if eq(createtype, 1) {
    #     // We use the context nonce to mimic CREATE's nonce based address calculation and make verification easier  # noqa: E501
    #     addr := create2(0, sub(32, 17), 17, contextnonce)
    #   }
    #   sstore(2, addr)
    #   if gt(addr, 0) { sstore(0xffff, add(contextnonce, 1)) }
    #   mstore(0, addr)
    #   return(0, 32)
    # }
    max_nonce = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x0)
        + Op.SLOAD(key=0xFFFF)
        + Op.MSTORE(offset=0x0, value=0x6005600C60003960056000F36001600155)
        + Op.PUSH1[0x0]
        + Op.SWAP2
        + Op.JUMPI(pc=0x5E, condition=Op.EQ(Op.DUP2, 0x0))
        + Op.JUMPDEST
        + Op.PUSH1[0x1]
        + Op.JUMPI(pc=0x4F, condition=Op.EQ)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x2, value=Op.DUP2)
        + Op.JUMPI(pc=0x43, condition=Op.GT(Op.DUP3, 0x0))
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.MSTORE
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0xFFFF, value=Op.ADD)
        + Op.CODESIZE
        + Op.JUMP(pc=0x39)
        + Op.JUMPDEST
        + Op.SWAP1
        + Op.POP
        + Op.CREATE2(value=0x0, offset=0xF, size=0x11, salt=Op.DUP1)
        + Op.SWAP1
        + Op.JUMP(pc=0x2D)
        + Op.JUMPDEST
        + Op.SWAP2
        + Op.POP
        + Op.PUSH1[0x1]
        + Op.CREATE(value=0x0, offset=0xF, size=0x11)
        + Op.SWAP3
        + Op.SWAP1
        + Op.POP
        + Op.JUMP(pc=0x26),
        storage={65535: 0xFFFFFFFFFFFFFFFF},
        nonce=18446744073709551615,
        address=Address(0xE51BC07F90C9661FA42DB3BDE8DD52B942AC69E0),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   let calltype      := calldataload(4)
    #   let callernonce   := calldataload(36)
    #   let destnonce     := calldataload(68)
    #   let createtype    := calldataload(100)
    #
    #   for { let contextnonce := sload(0xffff) } lt(contextnonce, callernonce) { contextnonce := sload(0xffff) } {  # noqa: E501
    #     // We have a lower nonce than required for the caller, create dummy contract to increase nonce  # noqa: E501
    #     mstore(0, 0x60016000f3)
    #     let addr := create(0, sub(32, 5), 5)
    #     if gt(addr, 0) { sstore(0xffff, add(contextnonce, 1)) }
    #   }
    #
    #   mstore(0, createtype)
    #   if eq(calltype, 0) {
    #     pop(delegatecall(sub(gas(), 1000), destnonce, 0, 32, 0, 32))
    #   }
    #   if eq(calltype, 1) {
    #     pop(callcode(sub(gas(), 1000), destnonce, 0, 0, 32, 0, 32))
    #   }
    #   if eq(calltype, 2) {
    #     pop(call(sub(gas(), 1000), destnonce, 0, 0, 32, 0, 32))
    #   }
    #   let result := mload(0)
    #   sstore(1, result)
    #   if gt(result, 0) {
    #     pop(call(sub(gas(), 1000), result, 0, 0, 0, 0, 0))
    #   }
    # }
    entry = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x4)
        + Op.CALLDATALOAD(offset=0x24)
        + Op.SWAP1
        + Op.CALLDATALOAD(offset=0x44)
        + Op.SWAP1
        + Op.CALLDATALOAD(offset=0x64)
        + Op.SLOAD(key=0xFFFF)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x8B, condition=Op.LT(Op.DUP2, Op.DUP5))
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.MSTORE
        + Op.PUSH1[0x2]
        + Op.SWAP1
        + Op.JUMPI(pc=0x79, condition=Op.ISZERO(Op.DUP1))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x66, condition=Op.EQ(Op.DUP2, 0x1))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x52, condition=Op.EQ)
        + Op.JUMPDEST
        + Op.POP
        + Op.MLOAD(offset=0x0)
        + Op.SSTORE(key=0x1, value=Op.DUP1)
        + Op.JUMPI(pc=0x43, condition=Op.GT(Op.DUP2, 0x0))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.DUP1 * 4
        + Op.SWAP5
        + Op.SUB(Op.GAS, 0x3E8)
        + Op.CALL
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.PUSH1[0x20]
        + Op.DUP2
        + Op.DUP1
        + Op.DUP3
        + Op.SWAP5
        + Op.SUB(Op.GAS, 0x3E8)
        + Op.POP(Op.CALL)
        + Op.DUP1
        + Op.JUMP(pc=0x32)
        + Op.JUMPDEST
        + Op.POP(
            Op.CALLCODE(
                gas=Op.SUB(Op.GAS, 0x3E8),
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=Op.DUP2,
                ret_offset=0x0,
                ret_size=0x20,
            )
        )
        + Op.JUMP(pc=0x2D)
        + Op.JUMPDEST
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.SUB(Op.GAS, 0x3E8),
                address=Op.DUP7,
                args_offset=Op.DUP2,
                args_size=Op.DUP2,
                ret_offset=0x0,
                ret_size=0x20,
            )
        )
        + Op.JUMP(pc=0x25)
        + Op.JUMPDEST
        + Op.PUSH5[0x60016000F3]
        + Op.PUSH1[0x0]
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.CREATE(value=Op.DUP3, offset=0x1B, size=0x5)
        + Op.JUMPI(pc=0xAA, condition=Op.GT)
        + Op.JUMPDEST
        + Op.POP
        + Op.SLOAD(key=0xFFFF)
        + Op.JUMP(pc=0x12)
        + Op.JUMPDEST
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0xFFFF, value=Op.ADD)
        + Op.CODESIZE
        + Op.JUMP(pc=0xA1),
        storage={65535: 0xFFFFFFFFFFFFFFFE},
        nonce=18446744073709551614,
        address=Address(0xD7D7B37FC131964CD181D47C9B705028776FE3D4),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [8, 9, 6, 7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                entry: Account(
                    storage={1: 0, 2: 0, 65535: 0xFFFFFFFFFFFFFFFF},
                    nonce=18446744073709551615,
                ),
                max_nonce_minus_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    nonce=18446744073709551614,
                ),
                max_nonce: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    nonce=18446744073709551615,
                ),
                Address(
                    0x3689DBE15F5217CDA3865B4158DA57C7A3F9AD88
                ): Account.NONEXISTENT,
                Address(
                    0xD77662C5102179C42ABBCAFCCC90AB351E7A1E4B
                ): Account.NONEXISTENT,
                Address(
                    0xB840E64C3AA027210A2CEBA09411CF1DD48C56A7
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [10], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                entry: Account(
                    storage={
                        1: 0x99F1BFB202FDF527E07FB8EB682A03C713AEAF11,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    nonce=18446744073709551615,
                ),
                max_nonce_minus_1: Account(
                    storage={
                        2: 0x99F1BFB202FDF527E07FB8EB682A03C713AEAF11,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    nonce=18446744073709551615,
                ),
                max_nonce: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    nonce=18446744073709551615,
                ),
                Address(0x99F1BFB202FDF527E07FB8EB682A03C713AEAF11): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                Address(
                    0x3689DBE15F5217CDA3865B4158DA57C7A3F9AD88
                ): Account.NONEXISTENT,
                Address(
                    0xD77662C5102179C42ABBCAFCCC90AB351E7A1E4B
                ): Account.NONEXISTENT,
                Address(
                    0xB840E64C3AA027210A2CEBA09411CF1DD48C56A7
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [11], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                entry: Account(
                    storage={1: 0, 65535: 0xFFFFFFFFFFFFFFFF},
                    nonce=18446744073709551615,
                ),
                max_nonce_minus_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    nonce=18446744073709551614,
                ),
                max_nonce: Account(
                    storage={2: 0, 65535: 0xFFFFFFFFFFFFFFFF},
                    nonce=18446744073709551615,
                ),
                Address(
                    0x3689DBE15F5217CDA3865B4158DA57C7A3F9AD88
                ): Account.NONEXISTENT,
                Address(
                    0xD77662C5102179C42ABBCAFCCC90AB351E7A1E4B
                ): Account.NONEXISTENT,
                Address(
                    0xB840E64C3AA027210A2CEBA09411CF1DD48C56A7
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [0, 1, 2, 3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                entry: Account(
                    storage={
                        1: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        2: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    nonce=18446744073709551615,
                ),
                max_nonce_minus_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    nonce=18446744073709551614,
                ),
                max_nonce: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    nonce=18446744073709551615,
                ),
                Address(0x74F5960E3479218EC095E853ED1FC95E285ADC3B): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                Address(
                    0x3689DBE15F5217CDA3865B4158DA57C7A3F9AD88
                ): Account.NONEXISTENT,
                Address(
                    0xD77662C5102179C42ABBCAFCCC90AB351E7A1E4B
                ): Account.NONEXISTENT,
                Address(
                    0xB840E64C3AA027210A2CEBA09411CF1DD48C56A7
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                entry: Account(
                    storage={
                        1: 0x99F1BFB202FDF527E07FB8EB682A03C713AEAF11,
                        65535: 0xFFFFFFFFFFFFFFFE,
                    },
                    nonce=18446744073709551614,
                ),
                max_nonce_minus_1: Account(
                    storage={
                        2: 0x99F1BFB202FDF527E07FB8EB682A03C713AEAF11,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    nonce=18446744073709551615,
                ),
                max_nonce: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    nonce=18446744073709551615,
                ),
                Address(0x99F1BFB202FDF527E07FB8EB682A03C713AEAF11): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                Address(
                    0x3689DBE15F5217CDA3865B4158DA57C7A3F9AD88
                ): Account.NONEXISTENT,
                Address(
                    0xD77662C5102179C42ABBCAFCCC90AB351E7A1E4B
                ): Account.NONEXISTENT,
                Address(
                    0xB840E64C3AA027210A2CEBA09411CF1DD48C56A7
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                entry: Account(
                    storage={1: 0, 65535: 0xFFFFFFFFFFFFFFFE},
                    nonce=18446744073709551614,
                ),
                max_nonce_minus_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    nonce=18446744073709551614,
                ),
                max_nonce: Account(
                    storage={2: 0, 65535: 0xFFFFFFFFFFFFFFFF},
                    nonce=18446744073709551615,
                ),
                Address(
                    0x3689DBE15F5217CDA3865B4158DA57C7A3F9AD88
                ): Account.NONEXISTENT,
                Address(
                    0xD77662C5102179C42ABBCAFCCC90AB351E7A1E4B
                ): Account.NONEXISTENT,
                Address(
                    0xB840E64C3AA027210A2CEBA09411CF1DD48C56A7
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [18, 19, 20, 21], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                entry: Account(
                    storage={1: 0, 2: 0, 65535: 0xFFFFFFFFFFFFFFFF},
                    nonce=18446744073709551615,
                ),
                max_nonce_minus_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    nonce=18446744073709551614,
                ),
                max_nonce: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    nonce=18446744073709551615,
                ),
                Address(
                    0x4E060B3A192FD2A082A00259BE2F021AD996D71C
                ): Account.NONEXISTENT,
                Address(
                    0xAA17FC42EF60F987CD7BC803EC28BCC9F0ED1C31
                ): Account.NONEXISTENT,
                Address(
                    0x76E76DCFBBE7DB1A0A9AB7D6B12E3A309188018A
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [22], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                entry: Account(
                    storage={
                        1: 0x1CFC908BB573719841CAD6A8BC34E7C1CE5EE020,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    nonce=18446744073709551615,
                ),
                max_nonce_minus_1: Account(
                    storage={
                        2: 0x1CFC908BB573719841CAD6A8BC34E7C1CE5EE020,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    nonce=18446744073709551615,
                ),
                max_nonce: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    nonce=18446744073709551615,
                ),
                Address(0x1CFC908BB573719841CAD6A8BC34E7C1CE5EE020): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                Address(
                    0x4E060B3A192FD2A082A00259BE2F021AD996D71C
                ): Account.NONEXISTENT,
                Address(
                    0xAA17FC42EF60F987CD7BC803EC28BCC9F0ED1C31
                ): Account.NONEXISTENT,
                Address(
                    0x76E76DCFBBE7DB1A0A9AB7D6B12E3A309188018A
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [23], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                entry: Account(
                    storage={1: 0, 65535: 0xFFFFFFFFFFFFFFFF},
                    nonce=18446744073709551615,
                ),
                max_nonce_minus_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    nonce=18446744073709551614,
                ),
                max_nonce: Account(
                    storage={2: 0, 65535: 0xFFFFFFFFFFFFFFFF},
                    nonce=18446744073709551615,
                ),
                Address(
                    0x4E060B3A192FD2A082A00259BE2F021AD996D71C
                ): Account.NONEXISTENT,
                Address(
                    0xAA17FC42EF60F987CD7BC803EC28BCC9F0ED1C31
                ): Account.NONEXISTENT,
                Address(
                    0x76E76DCFBBE7DB1A0A9AB7D6B12E3A309188018A
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [12, 13, 14, 15], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                entry: Account(
                    storage={
                        1: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        2: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    nonce=18446744073709551615,
                ),
                max_nonce_minus_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    nonce=18446744073709551614,
                ),
                max_nonce: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    nonce=18446744073709551615,
                ),
                Address(0x09F07A698496A643301174853C4F7F1EAAB166BE): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                Address(
                    0x4E060B3A192FD2A082A00259BE2F021AD996D71C
                ): Account.NONEXISTENT,
                Address(
                    0xAA17FC42EF60F987CD7BC803EC28BCC9F0ED1C31
                ): Account.NONEXISTENT,
                Address(
                    0x76E76DCFBBE7DB1A0A9AB7D6B12E3A309188018A
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [16], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                entry: Account(
                    storage={
                        1: 0x1CFC908BB573719841CAD6A8BC34E7C1CE5EE020,
                        65535: 0xFFFFFFFFFFFFFFFE,
                    },
                    nonce=18446744073709551614,
                ),
                max_nonce_minus_1: Account(
                    storage={
                        2: 0x1CFC908BB573719841CAD6A8BC34E7C1CE5EE020,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    },
                    nonce=18446744073709551615,
                ),
                max_nonce: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF},
                    nonce=18446744073709551615,
                ),
                Address(0x1CFC908BB573719841CAD6A8BC34E7C1CE5EE020): Account(
                    storage={1: 1}, code=bytes.fromhex("6001600155")
                ),
                Address(
                    0x4E060B3A192FD2A082A00259BE2F021AD996D71C
                ): Account.NONEXISTENT,
                Address(
                    0xAA17FC42EF60F987CD7BC803EC28BCC9F0ED1C31
                ): Account.NONEXISTENT,
                Address(
                    0x76E76DCFBBE7DB1A0A9AB7D6B12E3A309188018A
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [17], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                entry: Account(
                    storage={1: 0, 65535: 0xFFFFFFFFFFFFFFFE},
                    nonce=18446744073709551614,
                ),
                max_nonce_minus_1: Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE},
                    nonce=18446744073709551614,
                ),
                max_nonce: Account(
                    storage={2: 0, 65535: 0xFFFFFFFFFFFFFFFF},
                    nonce=18446744073709551615,
                ),
                Address(
                    0x4E060B3A192FD2A082A00259BE2F021AD996D71C
                ): Account.NONEXISTENT,
                Address(
                    0xAA17FC42EF60F987CD7BC803EC28BCC9F0ED1C31
                ): Account.NONEXISTENT,
                Address(
                    0x76E76DCFBBE7DB1A0A9AB7D6B12E3A309188018A
                ): Account.NONEXISTENT,
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0xFFFFFFFFFFFFFFFE)
        + Hash(max_nonce_minus_1, left_padding=True)
        + Hash(0x0),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0xFFFFFFFFFFFFFFFE)
        + Hash(max_nonce, left_padding=True)
        + Hash(0x0),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0xFFFFFFFFFFFFFFFE)
        + Hash(max_nonce_minus_1, left_padding=True)
        + Hash(0x0),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0xFFFFFFFFFFFFFFFE)
        + Hash(max_nonce, left_padding=True)
        + Hash(0x0),
        Bytes("917694f9")
        + Hash(0x2)
        + Hash(0xFFFFFFFFFFFFFFFE)
        + Hash(max_nonce_minus_1, left_padding=True)
        + Hash(0x0),
        Bytes("917694f9")
        + Hash(0x2)
        + Hash(0xFFFFFFFFFFFFFFFE)
        + Hash(max_nonce, left_padding=True)
        + Hash(0x0),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0xFFFFFFFFFFFFFFFF)
        + Hash(max_nonce_minus_1, left_padding=True)
        + Hash(0x0),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0xFFFFFFFFFFFFFFFF)
        + Hash(max_nonce, left_padding=True)
        + Hash(0x0),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0xFFFFFFFFFFFFFFFF)
        + Hash(max_nonce_minus_1, left_padding=True)
        + Hash(0x0),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0xFFFFFFFFFFFFFFFF)
        + Hash(max_nonce, left_padding=True)
        + Hash(0x0),
        Bytes("917694f9")
        + Hash(0x2)
        + Hash(0xFFFFFFFFFFFFFFFF)
        + Hash(max_nonce_minus_1, left_padding=True)
        + Hash(0x0),
        Bytes("917694f9")
        + Hash(0x2)
        + Hash(0xFFFFFFFFFFFFFFFF)
        + Hash(max_nonce, left_padding=True)
        + Hash(0x0),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0xFFFFFFFFFFFFFFFE)
        + Hash(max_nonce_minus_1, left_padding=True)
        + Hash(0x1),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0xFFFFFFFFFFFFFFFE)
        + Hash(max_nonce, left_padding=True)
        + Hash(0x1),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0xFFFFFFFFFFFFFFFE)
        + Hash(max_nonce_minus_1, left_padding=True)
        + Hash(0x1),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0xFFFFFFFFFFFFFFFE)
        + Hash(max_nonce, left_padding=True)
        + Hash(0x1),
        Bytes("917694f9")
        + Hash(0x2)
        + Hash(0xFFFFFFFFFFFFFFFE)
        + Hash(max_nonce_minus_1, left_padding=True)
        + Hash(0x1),
        Bytes("917694f9")
        + Hash(0x2)
        + Hash(0xFFFFFFFFFFFFFFFE)
        + Hash(max_nonce, left_padding=True)
        + Hash(0x1),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0xFFFFFFFFFFFFFFFF)
        + Hash(max_nonce_minus_1, left_padding=True)
        + Hash(0x1),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0xFFFFFFFFFFFFFFFF)
        + Hash(max_nonce, left_padding=True)
        + Hash(0x1),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0xFFFFFFFFFFFFFFFF)
        + Hash(max_nonce_minus_1, left_padding=True)
        + Hash(0x1),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0xFFFFFFFFFFFFFFFF)
        + Hash(max_nonce, left_padding=True)
        + Hash(0x1),
        Bytes("917694f9")
        + Hash(0x2)
        + Hash(0xFFFFFFFFFFFFFFFF)
        + Hash(max_nonce_minus_1, left_padding=True)
        + Hash(0x1),
        Bytes("917694f9")
        + Hash(0x2)
        + Hash(0xFFFFFFFFFFFFFFFF)
        + Hash(max_nonce, left_padding=True)
        + Hash(0x1),
    ]
    tx_gas = [16777216]

    tx = Transaction(
        sender=sender,
        to=entry,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
