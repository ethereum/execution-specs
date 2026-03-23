"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stBadOpcode/operationDiffGasFiller.yml
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "048071d300000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000f400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
    "048071d300000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000005100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000005200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000005300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
    "048071d3000000000000000000000000000000000000000000000000000000000000003b00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
]

TX_GAS = [16777216]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stBadOpcode/operationDiffGasFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(3, 0, 0, id="case0"),
        pytest.param(2, 0, 0, id="case1"),
        pytest.param(1, 0, 0, id="case2"),
        pytest.param(0, 0, 0, id="case3"),
        pytest.param(4, 0, 0, id="case4"),
        pytest.param(10, 0, 0, id="case5"),
        pytest.param(6, 0, 0, id="case6"),
        pytest.param(8, 0, 0, id="case7"),
        pytest.param(7, 0, 0, id="case8"),
        pytest.param(9, 0, 0, id="case9"),
        pytest.param(5, 0, 0, id="case10"),
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
    """Ori Pomerantz   qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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

    # Source: Yul
    # {
    #    mstore(0, 0xDEADBEEF)
    #    return(0, 0x100)
    # }
    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0xDEADBEEF)
            + Op.RETURN(offset=0x0, size=0x100)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x000000000000000000000000000000000000ca11"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    let useless := keccak256(0,0xBEEF)
    # }
    callee_1 = pre.deploy_contract(
        code=Op.SHA3(offset=0x0, size=0xBEEF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0de20"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   let addr := 0xCA11
    #   extcodecopy(addr, 0, 0, extcodesize(addr))
    # }
    callee_2 = pre.deploy_contract(
        code=(
            Op.PUSH2[0xCA11]
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.EXTCODESIZE(address=Op.DUP3)
            + Op.SWAP3
            + Op.EXTCODECOPY
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0de3b"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    let useless := mload(0xBEEF)
    # }
    callee_3 = pre.deploy_contract(
        code=Op.MLOAD(offset=0xBEEF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0de51"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    mstore(0xBEEF, 0xFF)
    # }
    callee_4 = pre.deploy_contract(
        code=Op.MSTORE(offset=0xBEEF, value=0xFF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0de52"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    mstore8(0xBEEF, 0xFF)
    # }
    callee_5 = pre.deploy_contract(
        code=Op.MSTORE8(offset=0xBEEF, value=0xFF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0de53"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    sstore(0,create(0, 0, 0x200))
    # }
    callee_6 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CREATE(value=Op.DUP1, offset=0x0, size=0x200),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0def0"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    let retval := call(gas(), 0xCA11, 0, 0, 0x100, 0, 0x100)
    # }
    callee_7 = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=Op.GAS,
                address=0xCA11,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=Op.DUP2,
                ret_offset=0x0,
                ret_size=0x100,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0def1"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    let retval := callcode(gas(), 0xCA11, 0, 0, 0x100, 0, 0x100)
    # }
    callee_8 = pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=Op.GAS,
                address=0xCA11,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=Op.DUP2,
                ret_offset=0x0,
                ret_size=0x100,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0def2"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    let retval := delegatecall(gas(), 0xCA11, 0, 0x100, 0, 0x100)
    # }
    callee_9 = pre.deploy_contract(
        code=(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=0xCA11,
                args_offset=Op.DUP2,
                args_size=Op.DUP2,
                ret_offset=0x0,
                ret_size=0x100,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0def4"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    sstore(0,create2(0, 0, 0x200, 0x5A17))
    # }
    callee_10 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CREATE2(
                    value=Op.DUP1,
                    offset=0x0,
                    size=0x200,
                    salt=0x5A17,
                ),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0def5"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    let retval := staticcall(gas(), 0xCA11, 0, 0x100, 0, 0x100)
    # }
    callee_11 = pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=Op.GAS,
                address=0xCA11,
                args_offset=Op.DUP2,
                args_size=Op.DUP2,
                ret_offset=0x0,
                ret_size=0x100,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0defa"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)
    # Source: Yul
    # {
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
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x44)
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
            + Op.JUMP(pc=0x11)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("63deadbeef6000526101006000f3")
                ),
                callee_1: Account(code=bytes.fromhex("61beef60002000")),
                callee_2: Account(
                    code=bytes.fromhex("61ca11600080823b923c00")
                ),
                callee_3: Account(code=bytes.fromhex("61beef5100")),
                callee_4: Account(code=bytes.fromhex("60ff61beef5200")),
                callee_5: Account(code=bytes.fromhex("60ff61beef5300")),
                callee_6: Account(
                    code=bytes.fromhex("610200600080f060005500")
                ),
                callee_7: Account(
                    code=bytes.fromhex("610100600081818061ca115af100")
                ),
                callee_8: Account(
                    code=bytes.fromhex("610100600081818061ca115af200")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6101006000818161ca115af400")
                ),
                callee_10: Account(
                    code=bytes.fromhex("615a17610200600080f560005500")
                ),
                callee_11: Account(
                    code=bytes.fromhex("6101006000818161ca115afa00")
                ),
                contract: Account(
                    storage={0: 2700},
                    code=bytes.fromhex(
                        "60443560243562c0de00600435016000805b14601c575003600055005b60008381808080808789f1930192601156"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("63deadbeef6000526101006000f3")
                ),
                callee_1: Account(code=bytes.fromhex("61beef60002000")),
                callee_2: Account(
                    code=bytes.fromhex("61ca11600080823b923c00")
                ),
                callee_3: Account(code=bytes.fromhex("61beef5100")),
                callee_4: Account(code=bytes.fromhex("60ff61beef5200")),
                callee_5: Account(code=bytes.fromhex("60ff61beef5300")),
                callee_6: Account(
                    code=bytes.fromhex("610200600080f060005500")
                ),
                callee_7: Account(
                    code=bytes.fromhex("610100600081818061ca115af100")
                ),
                callee_8: Account(
                    code=bytes.fromhex("610100600081818061ca115af200")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6101006000818161ca115af400")
                ),
                callee_10: Account(
                    code=bytes.fromhex("615a17610200600080f560005500")
                ),
                callee_11: Account(
                    code=bytes.fromhex("6101006000818161ca115afa00")
                ),
                contract: Account(
                    storage={0: 2700},
                    code=bytes.fromhex(
                        "60443560243562c0de00600435016000805b14601c575003600055005b60008381808080808789f1930192601156"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("63deadbeef6000526101006000f3")
                ),
                callee_1: Account(code=bytes.fromhex("61beef60002000")),
                callee_2: Account(
                    code=bytes.fromhex("61ca11600080823b923c00")
                ),
                callee_3: Account(code=bytes.fromhex("61beef5100")),
                callee_4: Account(code=bytes.fromhex("60ff61beef5200")),
                callee_5: Account(code=bytes.fromhex("60ff61beef5300")),
                callee_6: Account(
                    code=bytes.fromhex("610200600080f060005500")
                ),
                callee_7: Account(
                    code=bytes.fromhex("610100600081818061ca115af100")
                ),
                callee_8: Account(
                    code=bytes.fromhex("610100600081818061ca115af200")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6101006000818161ca115af400")
                ),
                callee_10: Account(
                    storage={0: 0x1C1BD7A2F25CA2F4577AD12388656BC147F96DAB},
                    code=bytes.fromhex("615a17610200600080f560005500"),
                ),
                callee_11: Account(
                    code=bytes.fromhex("6101006000818161ca115afa00")
                ),
                contract: Account(
                    storage={0: 54300},
                    code=bytes.fromhex(
                        "60443560243562c0de00600435016000805b14601c575003600055005b60008381808080808789f1930192601156"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("63deadbeef6000526101006000f3")
                ),
                callee_1: Account(code=bytes.fromhex("61beef60002000")),
                callee_2: Account(
                    code=bytes.fromhex("61ca11600080823b923c00")
                ),
                callee_3: Account(code=bytes.fromhex("61beef5100")),
                callee_4: Account(code=bytes.fromhex("60ff61beef5200")),
                callee_5: Account(code=bytes.fromhex("60ff61beef5300")),
                callee_6: Account(
                    storage={0: 0xB44F2C88D3D4283CD1E54E418C4FF7E6A6C73202},
                    code=bytes.fromhex("610200600080f060005500"),
                ),
                callee_7: Account(
                    code=bytes.fromhex("610100600081818061ca115af100")
                ),
                callee_8: Account(
                    code=bytes.fromhex("610100600081818061ca115af200")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6101006000818161ca115af400")
                ),
                callee_10: Account(
                    code=bytes.fromhex("615a17610200600080f560005500")
                ),
                callee_11: Account(
                    code=bytes.fromhex("6101006000818161ca115afa00")
                ),
                contract: Account(
                    storage={0: 54200},
                    code=bytes.fromhex(
                        "60443560243562c0de00600435016000805b14601c575003600055005b60008381808080808789f1930192601156"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("63deadbeef6000526101006000f3")
                ),
                callee_1: Account(code=bytes.fromhex("61beef60002000")),
                callee_2: Account(
                    code=bytes.fromhex("61ca11600080823b923c00")
                ),
                callee_3: Account(code=bytes.fromhex("61beef5100")),
                callee_4: Account(code=bytes.fromhex("60ff61beef5200")),
                callee_5: Account(code=bytes.fromhex("60ff61beef5300")),
                callee_6: Account(
                    code=bytes.fromhex("610200600080f060005500")
                ),
                callee_7: Account(
                    code=bytes.fromhex("610100600081818061ca115af100")
                ),
                callee_8: Account(
                    code=bytes.fromhex("610100600081818061ca115af200")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6101006000818161ca115af400")
                ),
                callee_10: Account(
                    code=bytes.fromhex("615a17610200600080f560005500")
                ),
                callee_11: Account(
                    code=bytes.fromhex("6101006000818161ca115afa00")
                ),
                contract: Account(
                    storage={0: 2700},
                    code=bytes.fromhex(
                        "60443560243562c0de00600435016000805b14601c575003600055005b60008381808080808789f1930192601156"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("63deadbeef6000526101006000f3")
                ),
                callee_1: Account(code=bytes.fromhex("61beef60002000")),
                callee_2: Account(
                    code=bytes.fromhex("61ca11600080823b923c00")
                ),
                callee_3: Account(code=bytes.fromhex("61beef5100")),
                callee_4: Account(code=bytes.fromhex("60ff61beef5200")),
                callee_5: Account(code=bytes.fromhex("60ff61beef5300")),
                callee_6: Account(
                    code=bytes.fromhex("610200600080f060005500")
                ),
                callee_7: Account(
                    code=bytes.fromhex("610100600081818061ca115af100")
                ),
                callee_8: Account(
                    code=bytes.fromhex("610100600081818061ca115af200")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6101006000818161ca115af400")
                ),
                callee_10: Account(
                    code=bytes.fromhex("615a17610200600080f560005500")
                ),
                callee_11: Account(
                    code=bytes.fromhex("6101006000818161ca115afa00")
                ),
                contract: Account(
                    storage={0: 2800},
                    code=bytes.fromhex(
                        "60443560243562c0de00600435016000805b14601c575003600055005b60008381808080808789f1930192601156"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("63deadbeef6000526101006000f3")
                ),
                callee_1: Account(code=bytes.fromhex("61beef60002000")),
                callee_2: Account(
                    code=bytes.fromhex("61ca11600080823b923c00")
                ),
                callee_3: Account(code=bytes.fromhex("61beef5100")),
                callee_4: Account(code=bytes.fromhex("60ff61beef5200")),
                callee_5: Account(code=bytes.fromhex("60ff61beef5300")),
                callee_6: Account(
                    code=bytes.fromhex("610200600080f060005500")
                ),
                callee_7: Account(
                    code=bytes.fromhex("610100600081818061ca115af100")
                ),
                callee_8: Account(
                    code=bytes.fromhex("610100600081818061ca115af200")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6101006000818161ca115af400")
                ),
                callee_10: Account(
                    code=bytes.fromhex("615a17610200600080f560005500")
                ),
                callee_11: Account(
                    code=bytes.fromhex("6101006000818161ca115afa00")
                ),
                contract: Account(
                    storage={0: 9200},
                    code=bytes.fromhex(
                        "60443560243562c0de00600435016000805b14601c575003600055005b60008381808080808789f1930192601156"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("63deadbeef6000526101006000f3")
                ),
                callee_1: Account(code=bytes.fromhex("61beef60002000")),
                callee_2: Account(
                    code=bytes.fromhex("61ca11600080823b923c00")
                ),
                callee_3: Account(code=bytes.fromhex("61beef5100")),
                callee_4: Account(code=bytes.fromhex("60ff61beef5200")),
                callee_5: Account(code=bytes.fromhex("60ff61beef5300")),
                callee_6: Account(
                    code=bytes.fromhex("610200600080f060005500")
                ),
                callee_7: Account(
                    code=bytes.fromhex("610100600081818061ca115af100")
                ),
                callee_8: Account(
                    code=bytes.fromhex("610100600081818061ca115af200")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6101006000818161ca115af400")
                ),
                callee_10: Account(
                    code=bytes.fromhex("615a17610200600080f560005500")
                ),
                callee_11: Account(
                    code=bytes.fromhex("6101006000818161ca115afa00")
                ),
                contract: Account(
                    storage={0: 9200},
                    code=bytes.fromhex(
                        "60443560243562c0de00600435016000805b14601c575003600055005b60008381808080808789f1930192601156"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("63deadbeef6000526101006000f3")
                ),
                callee_1: Account(code=bytes.fromhex("61beef60002000")),
                callee_2: Account(
                    code=bytes.fromhex("61ca11600080823b923c00")
                ),
                callee_3: Account(code=bytes.fromhex("61beef5100")),
                callee_4: Account(code=bytes.fromhex("60ff61beef5200")),
                callee_5: Account(code=bytes.fromhex("60ff61beef5300")),
                callee_6: Account(
                    code=bytes.fromhex("610200600080f060005500")
                ),
                callee_7: Account(
                    code=bytes.fromhex("610100600081818061ca115af100")
                ),
                callee_8: Account(
                    code=bytes.fromhex("610100600081818061ca115af200")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6101006000818161ca115af400")
                ),
                callee_10: Account(
                    code=bytes.fromhex("615a17610200600080f560005500")
                ),
                callee_11: Account(
                    code=bytes.fromhex("6101006000818161ca115afa00")
                ),
                contract: Account(
                    storage={0: 9200},
                    code=bytes.fromhex(
                        "60443560243562c0de00600435016000805b14601c575003600055005b60008381808080808789f1930192601156"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("63deadbeef6000526101006000f3")
                ),
                callee_1: Account(code=bytes.fromhex("61beef60002000")),
                callee_2: Account(
                    code=bytes.fromhex("61ca11600080823b923c00")
                ),
                callee_3: Account(code=bytes.fromhex("61beef5100")),
                callee_4: Account(code=bytes.fromhex("60ff61beef5200")),
                callee_5: Account(code=bytes.fromhex("60ff61beef5300")),
                callee_6: Account(
                    code=bytes.fromhex("610200600080f060005500")
                ),
                callee_7: Account(
                    code=bytes.fromhex("610100600081818061ca115af100")
                ),
                callee_8: Account(
                    code=bytes.fromhex("610100600081818061ca115af200")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6101006000818161ca115af400")
                ),
                callee_10: Account(
                    code=bytes.fromhex("615a17610200600080f560005500")
                ),
                callee_11: Account(
                    code=bytes.fromhex("6101006000818161ca115afa00")
                ),
                contract: Account(
                    storage={0: 18400},
                    code=bytes.fromhex(
                        "60443560243562c0de00600435016000805b14601c575003600055005b60008381808080808789f1930192601156"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("63deadbeef6000526101006000f3")
                ),
                callee_1: Account(code=bytes.fromhex("61beef60002000")),
                callee_2: Account(
                    code=bytes.fromhex("61ca11600080823b923c00")
                ),
                callee_3: Account(code=bytes.fromhex("61beef5100")),
                callee_4: Account(code=bytes.fromhex("60ff61beef5200")),
                callee_5: Account(code=bytes.fromhex("60ff61beef5300")),
                callee_6: Account(
                    code=bytes.fromhex("610200600080f060005500")
                ),
                callee_7: Account(
                    code=bytes.fromhex("610100600081818061ca115af100")
                ),
                callee_8: Account(
                    code=bytes.fromhex("610100600081818061ca115af200")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6101006000818161ca115af400")
                ),
                callee_10: Account(
                    code=bytes.fromhex("615a17610200600080f560005500")
                ),
                callee_11: Account(
                    code=bytes.fromhex("6101006000818161ca115afa00")
                ),
                contract: Account(
                    storage={0: 2700},
                    code=bytes.fromhex(
                        "60443560243562c0de00600435016000805b14601c575003600055005b60008381808080808789f1930192601156"  # noqa: E501
                    ),
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=1,
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
