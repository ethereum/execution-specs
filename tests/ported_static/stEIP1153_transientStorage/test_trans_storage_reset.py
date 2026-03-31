"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/Cancun/stEIP1153_transientStorage/transStorageResetFiller.yml
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
    [
        "state_tests/Cancun/stEIP1153_transientStorage/transStorageResetFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="reverter-call-call-stop",
        ),
        pytest.param(
            1,
            0,
            0,
            id="reverter-call-call-revert",
        ),
        pytest.param(
            2,
            0,
            0,
            id="reverter-call-call-invalid",
        ),
        pytest.param(
            3,
            0,
            0,
            id="reverter-delegate-call-stop",
        ),
        pytest.param(
            4,
            0,
            0,
            id="reverter-delegate-call-revert",
        ),
        pytest.param(
            5,
            0,
            0,
            id="reverter-delegate-call-invalid",
        ),
        pytest.param(
            6,
            0,
            0,
            id="reverter-code-call-stop",
        ),
        pytest.param(
            7,
            0,
            0,
            id="reverter-code-call-revert",
        ),
        pytest.param(
            8,
            0,
            0,
            id="reverter-code-call-invalid",
        ),
        pytest.param(
            9,
            0,
            0,
            id="reverter-delegate-delegate-stop",
        ),
        pytest.param(
            10,
            0,
            0,
            id="reverter-delegate-delegate-revert",
        ),
        pytest.param(
            11,
            0,
            0,
            id="reverter-delegate-delegate-invalid",
        ),
        pytest.param(
            12,
            0,
            0,
            id="reverter-delegate-code-stop",
        ),
        pytest.param(
            13,
            0,
            0,
            id="reverter-delegate-code-revert",
        ),
        pytest.param(
            14,
            0,
            0,
            id="reverter-delegate-code-invalid",
        ),
        pytest.param(
            15,
            0,
            0,
            id="reverter-code-delegate-stop",
        ),
        pytest.param(
            16,
            0,
            0,
            id="reverter-code-delegate-revert",
        ),
        pytest.param(
            17,
            0,
            0,
            id="reverter-code-delegate-invalid",
        ),
        pytest.param(
            18,
            0,
            0,
            id="reverter-code-code-stop",
        ),
        pytest.param(
            19,
            0,
            0,
            id="reverter-code-code-revert",
        ),
        pytest.param(
            20,
            0,
            0,
            id="reverter-code-code-invalid",
        ),
        pytest.param(
            21,
            0,
            0,
            id="reverter-call-nop-stop",
        ),
        pytest.param(
            22,
            0,
            0,
            id="reverter-call-nop-revert",
        ),
        pytest.param(
            23,
            0,
            0,
            id="reverter-call-nop-invalid",
        ),
        pytest.param(
            24,
            0,
            0,
            id="reverter-delegate-nop-stop",
        ),
        pytest.param(
            25,
            0,
            0,
            id="reverter-delegate-nop-revert",
        ),
        pytest.param(
            26,
            0,
            0,
            id="reverter-delegate-nop-invalid",
        ),
        pytest.param(
            27,
            0,
            0,
            id="reverter-code-nop-stop",
        ),
        pytest.param(
            28,
            0,
            0,
            id="reverter-code-nop-revert",
        ),
        pytest.param(
            29,
            0,
            0,
            id="reverter-code-nop-invalid",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_trans_storage_reset(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x48DC5A9F099CAAAA557742CA3A990A94BE45B9969126A1BC74E5E8BE5A2B5B47
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: yul
    # {
    #     // These two functions use transient storage.
    #     // Once the relevant opcodes are added to Yul, simply remove
    #     // them (from all contracts) and remove the _temp suffices.
    #     function tload_temp(loc) -> val {
    #       val := verbatim_1i_1o(hex"5C", loc)
    #     }
    #
    #     function tstore_temp(loc, val) {
    #       verbatim_2i_0o(hex"5D", loc, val)
    #     }
    #
    #     let reverter := calldataload(0)
    #     let dead     := calldataload(32)
    #     mstore(0, reverter)
    #     mstore(32, dead)
    #
    #     let callType := byte(0x1E, calldataload(64))
    #     let failType := byte(0x1F, calldataload(64))
    #
    #     let callRes := 0x7E57
    #
    #     switch callType
    #     // We cannot use caller() because if we were delegatecall()ed or
    #     // callcode()ed caller() is still 0xCCC...CCC
    #     case 0xF1 { callRes := call        (gas(), reverter, 0, 0,64, 0,0) }
    #     case 0xF2 { callRes := callcode    (gas(), reverter, 0, 0,64, 0,0) }
    #     case 0xF4 { callRes := delegatecall(gas(), reverter,    0,64, 0,0) }
    #
    #     // Don't call anything, just set Trans[0] here.
    # ... (13 more lines)
    dead = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=Op.PUSH0)
        + Op.CALLDATALOAD(offset=0x20)
        + Op.MSTORE(offset=Op.PUSH0, value=Op.DUP2)
        + Op.PUSH1[0x20]
        + Op.MSTORE
        + Op.BYTE(0x1E, Op.CALLDATALOAD(offset=0x40))
        + Op.BYTE(0x1F, Op.CALLDATALOAD(offset=0x40))
        + Op.SWAP2
        + Op.PUSH2[0x7E57]
        + Op.SWAP2
        + Op.SWAP1
        + Op.JUMPI(pc=0x91, condition=Op.EQ(0xF1, Op.DUP2))
        + Op.JUMPI(pc=0x80, condition=Op.EQ(0xF2, Op.DUP2))
        + Op.JUMPI(pc=0x70, condition=Op.EQ(0xF4, Op.DUP2))
        + Op.POP
        + Op.JUMPI(pc=0x60, condition=Op.ISZERO)
        + Op.JUMPDEST
        + Op.PUSH1[0x10]
        + Op.SSTORE
        + Op.JUMPI(pc=0x5E, condition=Op.ISZERO(Op.DUP1))
        + Op.JUMPI(pc=0x5A, condition=Op.EQ(0xFD, Op.DUP1))
        + Op.JUMPI(pc=0x58, condition=Op.EQ(0xFE, Op.DUP1))
        + Op.PUSH1[0xFF]
        + Op.JUMPI(pc=0x55, condition=Op.EQ)
        + Op.STOP
        + Op.JUMPDEST
        + Op.SELFDESTRUCT(address=Op.PUSH0)
        + Op.JUMPDEST
        + Op.INVALID
        + Op.JUMPDEST
        + Op.REVERT(offset=Op.DUP1, size=Op.PUSH0)
        + Op.JUMPDEST
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x6C]
        + Op.PUSH4[0xBAD0BEEF]
        + Op.PUSH0
        + Op.JUMP(pc=0xA2)
        + Op.JUMPDEST
        + Op.JUMP(pc=0x37)
        + Op.JUMPDEST
        + Op.PUSH0
        + Op.DUP1
        + Op.SWAP4
        + Op.POP
        + Op.DUP1
        + Op.SWAP3
        + Op.POP
        + Op.PUSH1[0x40]
        + Op.SWAP2
        + Op.GAS
        + Op.DELEGATECALL
        + Op.JUMP(pc=0x37)
        + Op.JUMPDEST
        + Op.PUSH0
        + Op.DUP1 * 2
        + Op.SWAP5
        + Op.POP
        + Op.DUP1
        + Op.SWAP4
        + Op.POP
        + Op.PUSH1[0x40]
        + Op.SWAP3
        + Op.GAS
        + Op.CALLCODE
        + Op.JUMP(pc=0x37)
        + Op.JUMPDEST
        + Op.PUSH0
        + Op.DUP1 * 2
        + Op.SWAP5
        + Op.POP
        + Op.DUP1
        + Op.SWAP4
        + Op.POP
        + Op.PUSH1[0x40]
        + Op.SWAP3
        + Op.GAS
        + Op.CALL
        + Op.JUMP(pc=0x37)
        + Op.JUMPDEST
        + Op.TSTORE
        + Op.JUMP,
        storage={16: 24743},
        nonce=1,
        address=Address(0xD1F046B080A87137C61A14BB81C2B6BBCEC17084),  # noqa: E501
    )
    # Source: yul
    # {
    #     function tload_temp(loc) -> val {
    #       val := verbatim_1i_1o(hex"5C", loc)
    #     }
    #
    #     function tstore_temp(loc, val) {
    #       verbatim_2i_0o(hex"5D", loc, val)
    #     }
    #
    #     let reverter := calldataload(0)
    #     let dead     := calldataload(32)
    #     mstore(0, reverter)
    #     mstore(32, dead)
    #
    #     // The type of call to use here
    #     let callType := byte(0x1D, calldataload(64))
    #
    #
    #     // Because we use DELEGATECALL in some cases, we cannot rely on caller()  # noqa: E501
    #     // (in a DELEGATECALL the caller is the one who called the contract that  # noqa: E501
    #     // has the storage.
    #
    #     // First invocation, called by  0xCCCCC...CCCC
    #     if iszero(tload_temp(0)) {
    #       tstore_temp(0, 0x60A7)
    #       mstore(64, calldataload(64))
    #
    #       let callRes := 0
    #
    #       // We only send half the gas because the call may spend all
    # ... (22 more lines)
    reverter = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=Op.PUSH0)
        + Op.CALLDATALOAD(offset=0x20)
        + Op.SWAP1
        + Op.PUSH0
        + Op.MSTORE
        + Op.MSTORE(offset=0x20, value=Op.DUP1)
        + Op.BYTE(0x1D, Op.CALLDATALOAD(offset=0x40))
        + Op.SWAP1
        + Op.PUSH1[0x19]
        + Op.PUSH0
        + Op.JUMP(pc=0xA8)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x39, condition=Op.ISZERO)
        + Op.PUSH2[0x60A7]
        + Op.PUSH1[0x27]
        + Op.PUSH0
        + Op.JUMP(pc=0xA8)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x2D, condition=Op.EQ)
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x37]
        + Op.PUSH2[0xBEEF]
        + Op.PUSH0
        + Op.JUMP(pc=0xAC)
        + Op.JUMPDEST
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x43]
        + Op.PUSH2[0x60A7]
        + Op.PUSH0
        + Op.JUMP(pc=0xAC)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x40))
        + Op.PUSH0
        + Op.SWAP2
        + Op.DIV(Op.GAS, 0x2)
        + Op.SWAP1
        + Op.JUMPI(pc=0x96, condition=Op.EQ(0xF1, Op.DUP1))
        + Op.JUMPI(pc=0x84, condition=Op.EQ(0xF2, Op.DUP1))
        + Op.PUSH1[0xF4]
        + Op.JUMPI(pc=0x74, condition=Op.EQ)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.DUP3)
        + Op.PUSH1[0x70]
        + Op.PUSH0
        + Op.JUMP(pc=0xA8)
        + Op.JUMPDEST
        + Op.PUSH0
        + Op.SSTORE
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH0
        + Op.DUP1
        + Op.SWAP4
        + Op.POP
        + Op.DUP1
        + Op.SWAP3
        + Op.PUSH1[0x60]
        + Op.SWAP3
        + Op.DELEGATECALL
        + Op.PUSH0
        + Op.DUP1
        + Op.JUMP(pc=0x65)
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH0
        + Op.DUP1 * 2
        + Op.SWAP5
        + Op.POP
        + Op.DUP1
        + Op.SWAP4
        + Op.PUSH1[0x60]
        + Op.SWAP4
        + Op.CALLCODE
        + Op.PUSH0
        + Op.DUP1
        + Op.JUMP(pc=0x65)
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH0
        + Op.DUP1 * 2
        + Op.SWAP5
        + Op.POP
        + Op.DUP1
        + Op.SWAP4
        + Op.PUSH1[0x60]
        + Op.SWAP4
        + Op.CALL
        + Op.PUSH0
        + Op.DUP1
        + Op.JUMP(pc=0x65)
        + Op.JUMPDEST
        + Op.TLOAD
        + Op.SWAP1
        + Op.JUMP
        + Op.JUMPDEST
        + Op.TSTORE
        + Op.JUMP,
        storage={1: 24743},
        nonce=1,
        address=Address(0x9F075370EF41D4CD90151E731E33836E6F521669),  # noqa: E501
    )
    # Source: yul
    # {
    #   let reverter := calldataload(4)
    #   let dead     := calldataload(36)
    #   let param := calldataload(68)
    #   sstore(0, reverter)
    #   mstore(0, reverter)
    #   mstore(32, dead)
    #   mstore(64, param)
    #   sstore(1, call(gas(), reverter, 0, 0, 96, 0, 0))
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH0
        + Op.DUP1
        + Op.PUSH1[0x60]
        + Op.DUP2
        + Op.DUP1
        + Op.CALLDATALOAD(offset=0x4)
        + Op.CALLDATALOAD(offset=0x24)
        + Op.CALLDATALOAD(offset=0x44)
        + Op.SWAP1
        + Op.SSTORE(key=Op.DUP5, value=Op.DUP3)
        + Op.MSTORE(offset=Op.DUP5, value=Op.DUP3)
        + Op.PUSH1[0x20]
        + Op.MSTORE
        + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.GAS
        + Op.SSTORE(key=0x1, value=Op.CALL)
        + Op.STOP,
        nonce=1,
        address=Address(0x1679C7439EF325A99A6AFC54A8F7894C3DA35B16),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                ),
                reverter: Account(storage={0: 48879, 1: 1}),
                dead: Account(storage={16: 1}),
            },
        },
        {
            "indexes": {"data": [3, 6, 9, 12, 15, 18], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                ),
                reverter: Account(storage={0: 48879, 1: 1, 16: 1}),
            },
        },
        {
            "indexes": {"data": [24, 27], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                ),
                reverter: Account(storage={0: 0xBAD0BEEF, 1: 1, 16: 32343}),
            },
        },
        {
            "indexes": {
                "data": [
                    1,
                    2,
                    4,
                    5,
                    7,
                    8,
                    10,
                    11,
                    13,
                    14,
                    16,
                    17,
                    19,
                    20,
                    22,
                    23,
                    25,
                    26,
                    28,
                    29,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                ),
                reverter: Account(storage={0: 24743, 1: 0}),
                dead: Account(storage={16: 24743}),
            },
        },
        {
            "indexes": {"data": [21], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                ),
                reverter: Account(storage={0: 24743, 1: 1}),
                dead: Account(storage={16: 32343}),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF1F100),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF1F1FD),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF1F1FE),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF4F100),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF4F1FD),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF4F1FE),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF2F100),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF2F1FD),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF2F1FE),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF4F400),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF4F4FD),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF4F4FE),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF4F200),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF4F2FD),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF4F2FE),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF2F400),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF2F4FD),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF2F4FE),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF2F200),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF2F2FD),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF2F2FE),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF10000),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF100FD),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF100FE),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF40000),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF400FD),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF400FE),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF20000),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF200FD),
        Bytes("d6c2107a")
        + Hash(reverter, left_padding=True)
        + Hash(dead, left_padding=True)
        + Hash(0xF200FE),
    ]
    tx_gas = [16777216]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
