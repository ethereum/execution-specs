"""
Delegate calls CREATE/CREATE2 from an account with max allowed nonce/max allowed nonce - 1.

Ported from:
state_tests/stCreate2/CREATE2_HighNonceDelegatecallFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",
    "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",
    "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",
    "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",
    "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",
    "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",
    "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",
    "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",
    "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",
    "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",
    "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",
    "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",
    "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",
    "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",
    "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",
    "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",
    "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",
    "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",
    "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",
    "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",
    "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",
    "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",
    "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",
    "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",
]
TX_GAS = [16777216]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stCreate2/CREATE2_HighNonceDelegatecallFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="A_MaxNonceMinus1_DelegateCall_B_MaxNonceMinus1_Create",
        ),
        pytest.param(
            1, 0, 0,
            id="A_MaxNonceMinus1_DelegateCall_B_MaxNonce_Create",
        ),
        pytest.param(
            2, 0, 0,
            id="A_MaxNonceMinus1_CallCode_B_MaxNonceMinus1_Create",
        ),
        pytest.param(
            3, 0, 0,
            id="A_MaxNonceMinus1_CallCode_B_MaxNonce_Create",
        ),
        pytest.param(
            4, 0, 0,
            id="A_MaxNonceMinus1_Call_B_MaxNonceMinus1_Create",
        ),
        pytest.param(
            5, 0, 0,
            id="A_MaxNonceMinus1_Call_B_MaxNonce_Create",
        ),
        pytest.param(
            6, 0, 0,
            id="A_MaxNonce_DelegateCall_B_MaxNonceMinus1_Create",
        ),
        pytest.param(
            7, 0, 0,
            id="A_MaxNonce_DelegateCall_B_MaxNonce_Create",
        ),
        pytest.param(
            8, 0, 0,
            id="A_MaxNonce_CallCode_B_MaxNonceMinus1_Create",
        ),
        pytest.param(
            9, 0, 0,
            id="A_MaxNonce_CallCode_B_MaxNonce_Create",
        ),
        pytest.param(
            10, 0, 0,
            id="A_MaxNonce_Call_B_MaxNonceMinus1_Create",
        ),
        pytest.param(
            11, 0, 0,
            id="A_MaxNonce_Call_B_MaxNonce_Create",
        ),
        pytest.param(
            12, 0, 0,
            id="A_MaxNonceMinus1_DelegateCall_B_MaxNonceMinus1_Create2",
        ),
        pytest.param(
            13, 0, 0,
            id="A_MaxNonceMinus1_DelegateCall_B_MaxNonce_Create2",
        ),
        pytest.param(
            14, 0, 0,
            id="A_MaxNonceMinus1_CallCode_B_MaxNonceMinus1_Create2",
        ),
        pytest.param(
            15, 0, 0,
            id="A_MaxNonceMinus1_CallCode_B_MaxNonce_Create2",
        ),
        pytest.param(
            16, 0, 0,
            id="A_MaxNonceMinus1_Call_B_MaxNonceMinus1_Create2",
        ),
        pytest.param(
            17, 0, 0,
            id="A_MaxNonceMinus1_Call_B_MaxNonce_Create2",
        ),
        pytest.param(
            18, 0, 0,
            id="A_MaxNonce_DelegateCall_B_MaxNonceMinus1_Create2",
        ),
        pytest.param(
            19, 0, 0,
            id="A_MaxNonce_DelegateCall_B_MaxNonce_Create2",
        ),
        pytest.param(
            20, 0, 0,
            id="A_MaxNonce_CallCode_B_MaxNonceMinus1_Create2",
        ),
        pytest.param(
            21, 0, 0,
            id="A_MaxNonce_CallCode_B_MaxNonce_Create2",
        ),
        pytest.param(
            22, 0, 0,
            id="A_MaxNonce_Call_B_MaxNonceMinus1_Create2",
        ),
        pytest.param(
            23, 0, 0,
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
    """Delegate calls CREATE/CREATE2 from an account with max allowed nonc..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xf79127a3004abde26a4cbd80c428cb10f829fa11b54d36e7b326f4f4a5927acf
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[sender] = Account(balance=0x3b9aca00)
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
    #     // We use the context nonce to mimic CREATE's nonce based address calculation and make verification easier
    #     addr := create2(0, sub(32, 17), 17, contextnonce)
    #   }
    #   sstore(2, addr)
    #   if gt(addr, 0) { sstore(0xffff, add(contextnonce, 1)) }
    #   mstore(0, addr)
    #   return(0, 32)
    # }
    max_nonce_minus_1 = pre.deploy_contract(
        code=Op.CALLDATALOAD(offset=0x0) + Op.SLOAD(key=0xffff)
        + Op.MSTORE(offset=0x0, value=0x6005600c60003960056000f36001600155)
        + Op.PUSH1[0x0] + Op.SWAP2
        + Op.JUMPI(pc=0x5e, condition=Op.EQ(Op.DUP2, 0x0)) + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.JUMPI(pc=0x4f, condition=Op.EQ) + Op.JUMPDEST
        + Op.SSTORE(key=0x2, value=Op.DUP2)
        + Op.JUMPI(pc=0x43, condition=Op.GT(Op.DUP3, 0x0)) + Op.JUMPDEST + Op.POP
        + Op.PUSH1[0x0] + Op.MSTORE + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST + Op.PUSH1[0x1] + Op.SSTORE(key=0xffff, value=Op.ADD)
        + Op.CODESIZE + Op.JUMP(pc=0x39) + Op.JUMPDEST + Op.SWAP1 + Op.POP
        + Op.CREATE2(value=0x0, offset=0xf, size=0x11, salt=Op.DUP1) + Op.SWAP1
        + Op.JUMP(pc=0x2d) + Op.JUMPDEST + Op.SWAP2 + Op.POP + Op.PUSH1[0x1]
        + Op.CREATE(value=0x0, offset=0xf, size=0x11) + Op.SWAP3 + Op.SWAP1
        + Op.POP + Op.JUMP(pc=0x26),
        storage={65535: 0xfffffffffffffffe},
        nonce=18446744073709551614,
        address=Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"),  # noqa: E501
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
    #     // We use the context nonce to mimic CREATE's nonce based address calculation and make verification easier
    #     addr := create2(0, sub(32, 17), 17, contextnonce)
    #   }
    #   sstore(2, addr)
    #   if gt(addr, 0) { sstore(0xffff, add(contextnonce, 1)) }
    #   mstore(0, addr)
    #   return(0, 32)
    # }
    max_nonce = pre.deploy_contract(
        code=Op.CALLDATALOAD(offset=0x0) + Op.SLOAD(key=0xffff)
        + Op.MSTORE(offset=0x0, value=0x6005600c60003960056000f36001600155)
        + Op.PUSH1[0x0] + Op.SWAP2
        + Op.JUMPI(pc=0x5e, condition=Op.EQ(Op.DUP2, 0x0)) + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.JUMPI(pc=0x4f, condition=Op.EQ) + Op.JUMPDEST
        + Op.SSTORE(key=0x2, value=Op.DUP2)
        + Op.JUMPI(pc=0x43, condition=Op.GT(Op.DUP3, 0x0)) + Op.JUMPDEST + Op.POP
        + Op.PUSH1[0x0] + Op.MSTORE + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST + Op.PUSH1[0x1] + Op.SSTORE(key=0xffff, value=Op.ADD)
        + Op.CODESIZE + Op.JUMP(pc=0x39) + Op.JUMPDEST + Op.SWAP1 + Op.POP
        + Op.CREATE2(value=0x0, offset=0xf, size=0x11, salt=Op.DUP1) + Op.SWAP1
        + Op.JUMP(pc=0x2d) + Op.JUMPDEST + Op.SWAP2 + Op.POP + Op.PUSH1[0x1]
        + Op.CREATE(value=0x0, offset=0xf, size=0x11) + Op.SWAP3 + Op.SWAP1
        + Op.POP + Op.JUMP(pc=0x26),
        storage={65535: 0xffffffffffffffff},
        nonce=18446744073709551615,
        address=Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   let calltype      := calldataload(4)
    #   let callernonce   := calldataload(36)
    #   let destnonce     := calldataload(68)
    #   let createtype    := calldataload(100)
    # 
    #   for { let contextnonce := sload(0xffff) } lt(contextnonce, callernonce) { contextnonce := sload(0xffff) } {
    #     // We have a lower nonce than required for the caller, create dummy contract to increase nonce
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
    entry = pre.deploy_contract(
        code=Op.CALLDATALOAD(offset=0x4) + Op.CALLDATALOAD(offset=0x24) + Op.SWAP1
        + Op.CALLDATALOAD(offset=0x44) + Op.SWAP1 + Op.CALLDATALOAD(offset=0x64)
        + Op.SLOAD(key=0xffff) + Op.JUMPDEST
        + Op.JUMPI(pc=0x8b, condition=Op.LT(Op.DUP2, Op.DUP5)) + Op.POP
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x2] + Op.SWAP1
        + Op.JUMPI(pc=0x79, condition=Op.ISZERO(Op.DUP1)) + Op.JUMPDEST
        + Op.JUMPI(pc=0x66, condition=Op.EQ(Op.DUP2, 0x1)) + Op.JUMPDEST
        + Op.JUMPI(pc=0x52, condition=Op.EQ) + Op.JUMPDEST + Op.POP
        + Op.MLOAD(offset=0x0) + Op.SSTORE(key=0x1, value=Op.DUP1)
        + Op.JUMPI(pc=0x43, condition=Op.GT(Op.DUP2, 0x0)) + Op.STOP
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.DUP1 * 4 + Op.SWAP5
        + Op.SUB(Op.GAS, 0x3e8) + Op.CALL + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.DUP2 + Op.DUP1 + Op.DUP3 + Op.SWAP5
        + Op.SUB(Op.GAS, 0x3e8) + Op.POP(Op.CALL) + Op.DUP1 + Op.JUMP(pc=0x32)
        + Op.JUMPDEST
        + Op.POP(Op.CALLCODE(gas=Op.SUB(Op.GAS, 0x3e8), address=Op.DUP8, value=Op.DUP1, args_offset=Op.DUP2, args_size=Op.DUP2, ret_offset=0x0, ret_size=0x20))
        + Op.JUMP(pc=0x2d) + Op.JUMPDEST
        + Op.POP(Op.DELEGATECALL(gas=Op.SUB(Op.GAS, 0x3e8), address=Op.DUP7, args_offset=Op.DUP2, args_size=Op.DUP2, ret_offset=0x0, ret_size=0x20))
        + Op.JUMP(pc=0x25) + Op.JUMPDEST + Op.PUSH5[0x60016000f3] + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.DUP2 + Op.MSTORE
        + Op.CREATE(value=Op.DUP3, offset=0x1b, size=0x5)
        + Op.JUMPI(pc=0xaa, condition=Op.GT) + Op.JUMPDEST + Op.POP
        + Op.SLOAD(key=0xffff) + Op.JUMP(pc=0x12) + Op.JUMPDEST + Op.PUSH1[0x1]
        + Op.SSTORE(key=0xffff, value=Op.ADD) + Op.CODESIZE + Op.JUMP(pc=0xa1),
        storage={65535: 0xfffffffffffffffe},
        nonce=18446744073709551614,
        address=Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [8, 9, 6, 7], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        entry: Account(
                storage={1: 0, 2: 0, 65535: 0xffffffffffffffff},
                nonce=18446744073709551615,
            ),
        max_nonce_minus_1: Account(
                storage={65535: 0xfffffffffffffffe},
                nonce=18446744073709551614,
            ),
        max_nonce: Account(
                storage={65535: 0xffffffffffffffff},
                nonce=18446744073709551615,
            ),
        Address("0x3689dbe15f5217cda3865b4158da57c7a3f9ad88"): Account.NONEXISTENT,  # noqa: E501
        Address("0xd77662c5102179c42abbcafccc90ab351e7a1e4b"): Account.NONEXISTENT,  # noqa: E501
        Address("0xb840e64c3aa027210a2ceba09411cf1dd48c56a7"): Account.NONEXISTENT,  # noqa: E501
    },
        },
        {
            "indexes": {'data': [10], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        entry: Account(
                storage={
            1: 0x99f1bfb202fdf527e07fb8eb682a03c713aeaf11,
            65535: 0xffffffffffffffff,
        },
                nonce=18446744073709551615,
            ),
        max_nonce_minus_1: Account(
                storage={
            2: 0x99f1bfb202fdf527e07fb8eb682a03c713aeaf11,
            65535: 0xffffffffffffffff,
        },
                nonce=18446744073709551615,
            ),
        max_nonce: Account(
                storage={65535: 0xffffffffffffffff},
                nonce=18446744073709551615,
            ),
        Address("0x99f1bfb202fdf527e07fb8eb682a03c713aeaf11"): Account(storage={1: 1}, code=bytes.fromhex("6001600155")),  # noqa: E501
        Address("0x3689dbe15f5217cda3865b4158da57c7a3f9ad88"): Account.NONEXISTENT,  # noqa: E501
        Address("0xd77662c5102179c42abbcafccc90ab351e7a1e4b"): Account.NONEXISTENT,  # noqa: E501
        Address("0xb840e64c3aa027210a2ceba09411cf1dd48c56a7"): Account.NONEXISTENT,  # noqa: E501
    },
        },
        {
            "indexes": {'data': [11], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        entry: Account(
                storage={1: 0, 65535: 0xffffffffffffffff},
                nonce=18446744073709551615,
            ),
        max_nonce_minus_1: Account(
                storage={65535: 0xfffffffffffffffe},
                nonce=18446744073709551614,
            ),
        max_nonce: Account(
                storage={2: 0, 65535: 0xffffffffffffffff},
                nonce=18446744073709551615,
            ),
        Address("0x3689dbe15f5217cda3865b4158da57c7a3f9ad88"): Account.NONEXISTENT,  # noqa: E501
        Address("0xd77662c5102179c42abbcafccc90ab351e7a1e4b"): Account.NONEXISTENT,  # noqa: E501
        Address("0xb840e64c3aa027210a2ceba09411cf1dd48c56a7"): Account.NONEXISTENT,  # noqa: E501
    },
        },
        {
            "indexes": {'data': [0, 1, 2, 3], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        entry: Account(
                storage={
            1: 0x74f5960e3479218ec095e853ed1fc95e285adc3b,
            2: 0x74f5960e3479218ec095e853ed1fc95e285adc3b,
            65535: 0xffffffffffffffff,
        },
                nonce=18446744073709551615,
            ),
        max_nonce_minus_1: Account(
                storage={65535: 0xfffffffffffffffe},
                nonce=18446744073709551614,
            ),
        max_nonce: Account(
                storage={65535: 0xffffffffffffffff},
                nonce=18446744073709551615,
            ),
        Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(storage={1: 1}, code=bytes.fromhex("6001600155")),  # noqa: E501
        Address("0x3689dbe15f5217cda3865b4158da57c7a3f9ad88"): Account.NONEXISTENT,  # noqa: E501
        Address("0xd77662c5102179c42abbcafccc90ab351e7a1e4b"): Account.NONEXISTENT,  # noqa: E501
        Address("0xb840e64c3aa027210a2ceba09411cf1dd48c56a7"): Account.NONEXISTENT,  # noqa: E501
    },
        },
        {
            "indexes": {'data': [4], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        entry: Account(
                storage={
            1: 0x99f1bfb202fdf527e07fb8eb682a03c713aeaf11,
            65535: 0xfffffffffffffffe,
        },
                nonce=18446744073709551614,
            ),
        max_nonce_minus_1: Account(
                storage={
            2: 0x99f1bfb202fdf527e07fb8eb682a03c713aeaf11,
            65535: 0xffffffffffffffff,
        },
                nonce=18446744073709551615,
            ),
        max_nonce: Account(
                storage={65535: 0xffffffffffffffff},
                nonce=18446744073709551615,
            ),
        Address("0x99f1bfb202fdf527e07fb8eb682a03c713aeaf11"): Account(storage={1: 1}, code=bytes.fromhex("6001600155")),  # noqa: E501
        Address("0x3689dbe15f5217cda3865b4158da57c7a3f9ad88"): Account.NONEXISTENT,  # noqa: E501
        Address("0xd77662c5102179c42abbcafccc90ab351e7a1e4b"): Account.NONEXISTENT,  # noqa: E501
        Address("0xb840e64c3aa027210a2ceba09411cf1dd48c56a7"): Account.NONEXISTENT,  # noqa: E501
    },
        },
        {
            "indexes": {'data': [5], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        entry: Account(
                storage={1: 0, 65535: 0xfffffffffffffffe},
                nonce=18446744073709551614,
            ),
        max_nonce_minus_1: Account(
                storage={65535: 0xfffffffffffffffe},
                nonce=18446744073709551614,
            ),
        max_nonce: Account(
                storage={2: 0, 65535: 0xffffffffffffffff},
                nonce=18446744073709551615,
            ),
        Address("0x3689dbe15f5217cda3865b4158da57c7a3f9ad88"): Account.NONEXISTENT,  # noqa: E501
        Address("0xd77662c5102179c42abbcafccc90ab351e7a1e4b"): Account.NONEXISTENT,  # noqa: E501
        Address("0xb840e64c3aa027210a2ceba09411cf1dd48c56a7"): Account.NONEXISTENT,  # noqa: E501
    },
        },
        {
            "indexes": {'data': [18, 19, 20, 21], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        entry: Account(
                storage={1: 0, 2: 0, 65535: 0xffffffffffffffff},
                nonce=18446744073709551615,
            ),
        max_nonce_minus_1: Account(
                storage={65535: 0xfffffffffffffffe},
                nonce=18446744073709551614,
            ),
        max_nonce: Account(
                storage={65535: 0xffffffffffffffff},
                nonce=18446744073709551615,
            ),
        Address("0x4e060b3a192fd2a082a00259be2f021ad996d71c"): Account.NONEXISTENT,  # noqa: E501
        Address("0xaa17fc42ef60f987cd7bc803ec28bcc9f0ed1c31"): Account.NONEXISTENT,  # noqa: E501
        Address("0x76e76dcfbbe7db1a0a9ab7d6b12e3a309188018a"): Account.NONEXISTENT,  # noqa: E501
    },
        },
        {
            "indexes": {'data': [22], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        entry: Account(
                storage={
            1: 0x1cfc908bb573719841cad6a8bc34e7c1ce5ee020,
            65535: 0xffffffffffffffff,
        },
                nonce=18446744073709551615,
            ),
        max_nonce_minus_1: Account(
                storage={
            2: 0x1cfc908bb573719841cad6a8bc34e7c1ce5ee020,
            65535: 0xffffffffffffffff,
        },
                nonce=18446744073709551615,
            ),
        max_nonce: Account(
                storage={65535: 0xffffffffffffffff},
                nonce=18446744073709551615,
            ),
        Address("0x1cfc908bb573719841cad6a8bc34e7c1ce5ee020"): Account(storage={1: 1}, code=bytes.fromhex("6001600155")),  # noqa: E501
        Address("0x4e060b3a192fd2a082a00259be2f021ad996d71c"): Account.NONEXISTENT,  # noqa: E501
        Address("0xaa17fc42ef60f987cd7bc803ec28bcc9f0ed1c31"): Account.NONEXISTENT,  # noqa: E501
        Address("0x76e76dcfbbe7db1a0a9ab7d6b12e3a309188018a"): Account.NONEXISTENT,  # noqa: E501
    },
        },
        {
            "indexes": {'data': [23], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        entry: Account(
                storage={1: 0, 65535: 0xffffffffffffffff},
                nonce=18446744073709551615,
            ),
        max_nonce_minus_1: Account(
                storage={65535: 0xfffffffffffffffe},
                nonce=18446744073709551614,
            ),
        max_nonce: Account(
                storage={2: 0, 65535: 0xffffffffffffffff},
                nonce=18446744073709551615,
            ),
        Address("0x4e060b3a192fd2a082a00259be2f021ad996d71c"): Account.NONEXISTENT,  # noqa: E501
        Address("0xaa17fc42ef60f987cd7bc803ec28bcc9f0ed1c31"): Account.NONEXISTENT,  # noqa: E501
        Address("0x76e76dcfbbe7db1a0a9ab7d6b12e3a309188018a"): Account.NONEXISTENT,  # noqa: E501
    },
        },
        {
            "indexes": {'data': [12, 13, 14, 15], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        entry: Account(
                storage={
            1: 0x9f07a698496a643301174853c4f7f1eaab166be,
            2: 0x9f07a698496a643301174853c4f7f1eaab166be,
            65535: 0xffffffffffffffff,
        },
                nonce=18446744073709551615,
            ),
        max_nonce_minus_1: Account(
                storage={65535: 0xfffffffffffffffe},
                nonce=18446744073709551614,
            ),
        max_nonce: Account(
                storage={65535: 0xffffffffffffffff},
                nonce=18446744073709551615,
            ),
        Address("0x09f07a698496a643301174853c4f7f1eaab166be"): Account(storage={1: 1}, code=bytes.fromhex("6001600155")),  # noqa: E501
        Address("0x4e060b3a192fd2a082a00259be2f021ad996d71c"): Account.NONEXISTENT,  # noqa: E501
        Address("0xaa17fc42ef60f987cd7bc803ec28bcc9f0ed1c31"): Account.NONEXISTENT,  # noqa: E501
        Address("0x76e76dcfbbe7db1a0a9ab7d6b12e3a309188018a"): Account.NONEXISTENT,  # noqa: E501
    },
        },
        {
            "indexes": {'data': [16], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        entry: Account(
                storage={
            1: 0x1cfc908bb573719841cad6a8bc34e7c1ce5ee020,
            65535: 0xfffffffffffffffe,
        },
                nonce=18446744073709551614,
            ),
        max_nonce_minus_1: Account(
                storage={
            2: 0x1cfc908bb573719841cad6a8bc34e7c1ce5ee020,
            65535: 0xffffffffffffffff,
        },
                nonce=18446744073709551615,
            ),
        max_nonce: Account(
                storage={65535: 0xffffffffffffffff},
                nonce=18446744073709551615,
            ),
        Address("0x1cfc908bb573719841cad6a8bc34e7c1ce5ee020"): Account(storage={1: 1}, code=bytes.fromhex("6001600155")),  # noqa: E501
        Address("0x4e060b3a192fd2a082a00259be2f021ad996d71c"): Account.NONEXISTENT,  # noqa: E501
        Address("0xaa17fc42ef60f987cd7bc803ec28bcc9f0ed1c31"): Account.NONEXISTENT,  # noqa: E501
        Address("0x76e76dcfbbe7db1a0a9ab7d6b12e3a309188018a"): Account.NONEXISTENT,  # noqa: E501
    },
        },
        {
            "indexes": {'data': [17], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=1),
        entry: Account(
                storage={1: 0, 65535: 0xfffffffffffffffe},
                nonce=18446744073709551614,
            ),
        max_nonce_minus_1: Account(
                storage={65535: 0xfffffffffffffffe},
                nonce=18446744073709551614,
            ),
        max_nonce: Account(
                storage={2: 0, 65535: 0xffffffffffffffff},
                nonce=18446744073709551615,
            ),
        Address("0x4e060b3a192fd2a082a00259be2f021ad996d71c"): Account.NONEXISTENT,  # noqa: E501
        Address("0xaa17fc42ef60f987cd7bc803ec28bcc9f0ed1c31"): Account.NONEXISTENT,  # noqa: E501
        Address("0x76e76dcfbbe7db1a0a9ab7d6b12e3a309188018a"): Account.NONEXISTENT,  # noqa: E501
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=entry,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
