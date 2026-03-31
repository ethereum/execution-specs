"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
state_tests/stBadOpcode/measureGasFiller.yml
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
    ["state_tests/stBadOpcode/measureGasFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="CREATE",
        ),
        pytest.param(
            1,
            0,
            0,
            id="CREATE2",
        ),
        pytest.param(
            2,
            0,
            0,
            id="CALL",
        ),
        pytest.param(
            3,
            0,
            0,
            id="CALLCODE",
        ),
        pytest.param(
            4,
            0,
            0,
            id="DELEGATECALL",
        ),
        pytest.param(
            5,
            0,
            0,
            id="STATICCALL",
        ),
        pytest.param(
            6,
            0,
            0,
            id="MLOAD",
        ),
        pytest.param(
            7,
            0,
            0,
            id="MSTORE",
        ),
        pytest.param(
            8,
            0,
            0,
            id="MSTORE8",
        ),
        pytest.param(
            9,
            0,
            0,
            id="SHA3",
        ),
        pytest.param(
            10,
            0,
            0,
            id="EXTCODE",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_measure_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x0000000000000000000000000000000000C0DEF0)
    contract_1 = Address(0x0000000000000000000000000000000000C0DEF5)
    contract_2 = Address(0x000000000000000000000000000000000000CA11)
    contract_3 = Address(0x0000000000000000000000000000000000C0DEF1)
    contract_4 = Address(0x0000000000000000000000000000000000C0DEF2)
    contract_5 = Address(0x0000000000000000000000000000000000C0DEF4)
    contract_6 = Address(0x0000000000000000000000000000000000C0DEFA)
    contract_7 = Address(0x0000000000000000000000000000000000C0DE51)
    contract_8 = Address(0x0000000000000000000000000000000000C0DE52)
    contract_9 = Address(0x0000000000000000000000000000000000C0DE53)
    contract_10 = Address(0x0000000000000000000000000000000000C0DE20)
    contract_11 = Address(0x0000000000000000000000000000000000C0DE3B)
    contract_12 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
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

    # Source: yul
    # berlin {
    #    pop(create(0, 0, 0x200))
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.CREATE(value=Op.DUP1, offset=0x0, size=0x200) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DEF0),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    // SALT needs to be different each time
    #    pop(create2(0, 0, 0x200, add(0x5A17, gas())))
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.CREATE2(
            value=Op.DUP1, offset=0x0, size=0x200, salt=Op.ADD(0x5A17, Op.GAS)
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DEF5),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    stop()
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x000000000000000000000000000000000000CA11),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    let retval := call(gas(), 0xCA11, 0, 0, 0x100, 0, 0x100)
    # }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=Op.GAS,
            address=0xCA11,
            value=Op.DUP1,
            args_offset=Op.DUP2,
            args_size=Op.DUP2,
            ret_offset=0x0,
            ret_size=0x100,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DEF1),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    let retval := callcode(gas(), 0xCA11, 0, 0, 0x100, 0, 0x100)
    # }
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=Op.GAS,
            address=0xCA11,
            value=Op.DUP1,
            args_offset=Op.DUP2,
            args_size=Op.DUP2,
            ret_offset=0x0,
            ret_size=0x100,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DEF2),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    let retval := delegatecall(gas(), 0xCA11, 0, 0x100, 0, 0x100)
    # }
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.DELEGATECALL(
            gas=Op.GAS,
            address=0xCA11,
            args_offset=Op.DUP2,
            args_size=Op.DUP2,
            ret_offset=0x0,
            ret_size=0x100,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DEF4),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    let retval := staticcall(gas(), 0xCA11, 0, 0x100, 0, 0x100)
    # }
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=Op.GAS,
            address=0xCA11,
            args_offset=Op.DUP2,
            args_size=Op.DUP2,
            ret_offset=0x0,
            ret_size=0x100,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DEFA),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    let useless := mload(0xB000)
    # }
    contract_7 = pre.deploy_contract(  # noqa: F841
        code=Op.MLOAD(offset=0xB000) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DE51),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    mstore(0xB000, 0xFF)
    # }
    contract_8 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0xB000, value=0xFF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DE52),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    mstore8(0xB000, 0xFF)
    # }
    contract_9 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0xB000, value=0xFF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DE53),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    let useless := keccak256(0,0xBEEF)
    # }
    contract_10 = pre.deploy_contract(  # noqa: F841
        code=Op.SHA3(offset=0x0, size=0xBEEF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DE20),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #   let addr := 0xCA11
    #   extcodecopy(addr, 0, 0, extcodesize(addr))
    # }
    contract_11 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH2[0xCA11]
        + Op.PUSH1[0x0]
        + Op.DUP1
        + Op.EXTCODESIZE(address=Op.DUP3)
        + Op.SWAP3
        + Op.EXTCODECOPY
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DE3B),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #   // Find the operation's cost in gas
    #   let min :=     0
    #   let max := 60000
    #   let addr := add(0xC0DE00, calldataload(0x04))
    #
    #   for { } gt(sub(max,min), 1) { } { // Until we get the exact figure
    #      let middle := div(add(min,max),2)
    #      let result := call(middle, addr, 0, 0, 0, 0, 0)
    #      if eq(result, 0) { min := middle }
    #      if eq(result, 1) { max := middle }
    #   }
    #   sstore(0, max)
    # }
    contract_12 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH2[0xEA60]
        + Op.ADD(Op.CALLDATALOAD(offset=0x4), 0xC0DE00)
        + Op.PUSH1[0x0]
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x1C, condition=Op.GT(Op.SUB(Op.DUP5, Op.DUP2), 0x1))
        + Op.SSTORE(key=0x0, value=Op.DUP3)
        + Op.STOP
        + Op.JUMPDEST
        + Op.DIV(Op.ADD(Op.DUP3, Op.DUP4), 0x2)
        + Op.CALL(
            gas=Op.DUP7,
            address=Op.DUP8,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.JUMPI(pc=0x44, condition=Op.ISZERO(Op.DUP1))
        + Op.JUMPDEST
        + Op.PUSH1[0x1]
        + Op.JUMPI(pc=0x3D, condition=Op.EQ)
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMP(pc=0xD)
        + Op.JUMPDEST
        + Op.SWAP3
        + Op.POP
        + Op.CODESIZE
        + Op.JUMP(pc=0x38)
        + Op.JUMPDEST
        + Op.SWAP1
        + Op.SWAP2
        + Op.POP
        + Op.DUP2
        + Op.SWAP1
        + Op.JUMP(pc=0x31),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_12: Account(storage={0: 32089})},
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_12: Account(storage={0: 32193})},
        },
        {
            "indexes": {"data": [2, 3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_12: Account(storage={0: 144})},
        },
        {
            "indexes": {"data": [4, 5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_12: Account(storage={0: 141})},
        },
        {
            "indexes": {"data": [6], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_12: Account(storage={0: 8110})},
        },
        {
            "indexes": {"data": [8, 7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_12: Account(storage={0: 8113})},
        },
        {
            "indexes": {"data": [10], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_12: Account(storage={0: 221})},
        },
        {
            "indexes": {"data": [9], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_12: Account(storage={0: 18348})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("693c6139") + Hash(0xF0),
        Bytes("693c6139") + Hash(0xF5),
        Bytes("693c6139") + Hash(0xF1),
        Bytes("693c6139") + Hash(0xF2),
        Bytes("693c6139") + Hash(0xF4),
        Bytes("693c6139") + Hash(0xFA),
        Bytes("693c6139") + Hash(0x51),
        Bytes("693c6139") + Hash(0x52),
        Bytes("693c6139") + Hash(0x53),
        Bytes("693c6139") + Hash(0x20),
        Bytes("693c6139") + Hash(0x3B),
    ]
    tx_gas = [16777216]

    tx = Transaction(
        sender=sender,
        to=contract_12,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
