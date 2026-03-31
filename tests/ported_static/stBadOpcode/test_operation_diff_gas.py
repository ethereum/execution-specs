"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
state_tests/stBadOpcode/operationDiffGasFiller.yml
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
    ["state_tests/stBadOpcode/operationDiffGasFiller.yml"],
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
def test_operation_diff_gas(
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
    contract_2 = Address(0x0000000000000000000000000000000000C0DEF1)
    contract_3 = Address(0x0000000000000000000000000000000000C0DEF2)
    contract_4 = Address(0x0000000000000000000000000000000000C0DEF4)
    contract_5 = Address(0x0000000000000000000000000000000000C0DEFA)
    contract_6 = Address(0x000000000000000000000000000000000000CA11)
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
    #    sstore(0,create(0, 0, 0x200))
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0, value=Op.CREATE(value=Op.DUP1, offset=0x0, size=0x200)
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DEF0),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    sstore(0,create2(0, 0, 0x200, 0x5A17))
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CREATE2(
                value=Op.DUP1, offset=0x0, size=0x200, salt=0x5A17
            ),
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DEF5),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    let retval := call(gas(), 0xCA11, 0, 0, 0x100, 0, 0x100)
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
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
    contract_3 = pre.deploy_contract(  # noqa: F841
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
    contract_4 = pre.deploy_contract(  # noqa: F841
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
    contract_5 = pre.deploy_contract(  # noqa: F841
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
    #    mstore(0, 0xDEADBEEF)
    #    return(0, 0x100)
    # }
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0xDEADBEEF)
        + Op.RETURN(offset=0x0, size=0x100),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x000000000000000000000000000000000000CA11),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    let useless := mload(0xBEEF)
    # }
    contract_7 = pre.deploy_contract(  # noqa: F841
        code=Op.MLOAD(offset=0xBEEF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DE51),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    mstore(0xBEEF, 0xFF)
    # }
    contract_8 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0xBEEF, value=0xFF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DE52),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    mstore8(0xBEEF, 0xFF)
    # }
    contract_9 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0xBEEF, value=0xFF) + Op.STOP,
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
    #   // Run the operation with gasAmt, gasAmt+gasDiff, gasAmt+2*gasDiff, etc.  # noqa: E501
    #   let gasAmt := calldataload(0x24)
    #   let gasDiff := calldataload(0x44)
    #   let addr := add(0xC0DE00, calldataload(0x04))
    #   let result := 0
    #
    #   for { } eq(result, 0) { } {     // Until the operation is successful
    #      result := call(gasAmt, addr, 0, 0, 0, 0, 0)
    #      gasAmt := add(gasAmt, gasDiff)
    #   }
    #   sstore(0, sub(gasAmt, gasDiff))
    # }
    contract_12 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x44)
        + Op.CALLDATALOAD(offset=0x24)
        + Op.ADD(Op.CALLDATALOAD(offset=0x4), 0xC0DE00)
        + Op.PUSH1[0x0]
        + Op.DUP1
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x1C, condition=Op.EQ)
        + Op.POP
        + Op.SSTORE(key=0x0, value=Op.SUB)
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.DUP4
        + Op.CALL(
            gas=Op.DUP10,
            address=Op.DUP8,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=Op.DUP2,
        )
        + Op.SWAP4
        + Op.ADD
        + Op.SWAP3
        + Op.JUMP(pc=0x11),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_12: Account(storage={0: 54200})},
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_12: Account(storage={0: 54300})},
        },
        {
            "indexes": {"data": [2, 3, 4, 5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_12: Account(storage={0: 2700})},
        },
        {
            "indexes": {"data": [8, 6, 7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_12: Account(storage={0: 9200})},
        },
        {
            "indexes": {"data": [10], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_12: Account(storage={0: 2800})},
        },
        {
            "indexes": {"data": [9], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_12: Account(storage={0: 18400})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("048071d3") + Hash(0xF0) + Hash(0x0) + Hash(0x64),
        Bytes("048071d3") + Hash(0xF5) + Hash(0x0) + Hash(0x64),
        Bytes("048071d3") + Hash(0xF1) + Hash(0x0) + Hash(0x64),
        Bytes("048071d3") + Hash(0xF2) + Hash(0x0) + Hash(0x64),
        Bytes("048071d3") + Hash(0xF4) + Hash(0x0) + Hash(0x64),
        Bytes("048071d3") + Hash(0xFA) + Hash(0x0) + Hash(0x64),
        Bytes("048071d3") + Hash(0x51) + Hash(0x0) + Hash(0x64),
        Bytes("048071d3") + Hash(0x52) + Hash(0x0) + Hash(0x64),
        Bytes("048071d3") + Hash(0x53) + Hash(0x0) + Hash(0x64),
        Bytes("048071d3") + Hash(0x20) + Hash(0x0) + Hash(0x64),
        Bytes("048071d3") + Hash(0x3B) + Hash(0x0) + Hash(0x64),
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
