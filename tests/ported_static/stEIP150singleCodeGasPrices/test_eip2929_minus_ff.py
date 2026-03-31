"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP150singleCodeGasPrices/eip2929-ffFiller.yml
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
    ["state_tests/stEIP150singleCodeGasPrices/eip2929-ffFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="simple",
        ),
        pytest.param(
            1,
            0,
            0,
            id="balance",
        ),
        pytest.param(
            2,
            0,
            0,
            id="extcodesize",
        ),
        pytest.param(
            3,
            0,
            0,
            id="extcodecopy",
        ),
        pytest.param(
            4,
            0,
            0,
            id="extcodehash",
        ),
        pytest.param(
            5,
            0,
            0,
            id="call",
        ),
        pytest.param(
            6,
            0,
            0,
            id="callcode",
        ),
        pytest.param(
            7,
            0,
            0,
            id="delegatecall",
        ),
        pytest.param(
            8,
            0,
            0,
            id="staticcall",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_eip2929_minus_ff(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x000000000000000000000000000000000000DE57)
    contract_1 = Address(0x000000000000000000000000000000000000CA11)
    contract_2 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: raw
    # 0x00
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.STOP,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000DE57),  # noqa: E501
    )
    # Source: lll
    # {
    #      (selfdestruct 0xDE57)
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=0xDE57) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000CA11),  # noqa: E501
    )
    # Source: lll
    # {
    #    (def 'operation $4)
    #
    #    (def 'measurementCost 0x08)
    #
    #    ; Make sure not to be overwritten by extcodecopy
    #    (def 'gasB4     0x100)
    #    (def 'gasAfter  0x120)
    #
    #    ; Write something so the storage won't be new
    #    [gasB4] 0xFF
    #    [gasAfter] 0xFF
    #
    #    (def 'NOP 0)
    #    (def 'dest 0xDE57)   ; destination address
    #
    #    ; Read so access to that account later won't trigger EIP2929 costs
    #    (balance 0xca11)
    #
    #    ; If we need to add the destination address to the active set,
    #    ; do so.
    #    (if (= operation 0x31) (balance dest) NOP)
    #    (if (= operation 0x3B) (extcodesize dest) NOP)
    #    (if (= operation 0x3C) (extcodecopy dest 0 0 1) NOP)
    #    (if (= operation 0x3F) (extcodehash dest) NOP)
    #    (if (= operation 0xF1) (call 0x10000 dest 0 0 0 0 0) NOP)
    #    (if (= operation 0xF2) (callcode 0x10000 dest 0 0 0 0 0) NOP)
    #    (if (= operation 0xF4) (delegatecall 0x10000 dest 0 0 0 0) NOP)
    #    (if (= operation 0xFA) (staticcall 0x10000 dest 0 0 0 0) NOP)
    #
    # ... (18 more lines)
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x100, value=0xFF)
        + Op.MSTORE(offset=0x120, value=0xFF)
        + Op.POP(Op.BALANCE(address=0xCA11))
        + Op.JUMPI(
            pc=Op.PUSH2[0x21],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x31),
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=Op.PUSH2[0x26])
        + Op.JUMPDEST
        + Op.BALANCE(address=0xDE57)
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=Op.PUSH2[0x38],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x3B),
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=Op.PUSH2[0x3D])
        + Op.JUMPDEST
        + Op.EXTCODESIZE(address=0xDE57)
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=Op.PUSH2[0x50],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x3C),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x5B])
        + Op.JUMPDEST
        + Op.EXTCODECOPY(address=0xDE57, dest_offset=0x0, offset=0x0, size=0x1)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x6C],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x3F),
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=Op.PUSH2[0x71])
        + Op.JUMPDEST
        + Op.EXTCODEHASH(address=0xDE57)
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=Op.PUSH2[0x83],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF1),
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=Op.PUSH2[0x96])
        + Op.JUMPDEST
        + Op.CALL(
            gas=0x10000,
            address=0xDE57,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=Op.PUSH2[0xA8],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF2),
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=Op.PUSH2[0xBB])
        + Op.JUMPDEST
        + Op.CALLCODE(
            gas=0x10000,
            address=0xDE57,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=Op.PUSH2[0xCD],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF4),
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=Op.PUSH2[0xDE])
        + Op.JUMPDEST
        + Op.DELEGATECALL(
            gas=0x10000,
            address=0xDE57,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=Op.PUSH2[0xF0],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xFA),
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x101)
        + Op.JUMPDEST
        + Op.STATICCALL(
            gas=0x10000,
            address=0xDE57,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.JUMPDEST
        + Op.POP
        + Op.MSTORE(offset=0x100, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x1000000,
                address=0xCA11,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x120, value=Op.GAS)
        + Op.SSTORE(
            key=0x0,
            value=Op.SUB(
                Op.SUB(Op.MLOAD(offset=0x100), Op.MLOAD(offset=0x120)), 0x8
            ),
        )
        + Op.MSTORE(offset=0x100, value=Op.GAS)
        + Op.POP(Op.BALANCE(address=0xDE57))
        + Op.MSTORE(offset=0x120, value=Op.GAS)
        + Op.SSTORE(
            key=0x1,
            value=Op.SUB(
                Op.SUB(Op.MLOAD(offset=0x100), Op.MLOAD(offset=0x120)), 0x8
            ),
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_2: Account(storage={0: 7726, 1: 105})},
        },
        {
            "indexes": {
                "data": [1, 2, 3, 4, 5, 6, 7, 8],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_2: Account(storage={0: 5126, 1: 105})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x31),
        Bytes("693c6139") + Hash(0x3B),
        Bytes("693c6139") + Hash(0x3C),
        Bytes("693c6139") + Hash(0x3F),
        Bytes("693c6139") + Hash(0xF1),
        Bytes("693c6139") + Hash(0xF2),
        Bytes("693c6139") + Hash(0xF4),
        Bytes("693c6139") + Hash(0xFA),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_2,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
