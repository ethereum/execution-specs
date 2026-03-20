"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stCreateTest/CreateOOGFromCallRefundsFiller.yml
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
    "693c6139000000000000000000000000000000000000000000000000000000000000001a",
    "693c6139000000000000000000000000000000000000000000000000000000000000001b",
    "693c6139000000000000000000000000000000000000000000000000000000000000001c",
    "693c6139000000000000000000000000000000000000000000000000000000000000002a",
    "693c6139000000000000000000000000000000000000000000000000000000000000002b",
    "693c6139000000000000000000000000000000000000000000000000000000000000002c",
    "693c6139000000000000000000000000000000000000000000000000000000000000003a",
    "693c6139000000000000000000000000000000000000000000000000000000000000003b",
    "693c6139000000000000000000000000000000000000000000000000000000000000003c",
    "693c6139000000000000000000000000000000000000000000000000000000000000004a",
    "693c6139000000000000000000000000000000000000000000000000000000000000004b",
    "693c6139000000000000000000000000000000000000000000000000000000000000004c",
    "693c6139000000000000000000000000000000000000000000000000000000000000005a",
    "693c6139000000000000000000000000000000000000000000000000000000000000005b",
    "693c6139000000000000000000000000000000000000000000000000000000000000005c",
    "693c6139000000000000000000000000000000000000000000000000000000000000006a",
    "693c6139000000000000000000000000000000000000000000000000000000000000006b",
    "693c6139000000000000000000000000000000000000000000000000000000000000006c",
    "693c6139000000000000000000000000000000000000000000000000000000000000007a",
    "693c6139000000000000000000000000000000000000000000000000000000000000007b",
    "693c6139000000000000000000000000000000000000000000000000000000000000007c",
    "693c6139000000000000000000000000000000000000000000000000000000000000008a",
    "693c6139000000000000000000000000000000000000000000000000000000000000008b",
    "693c6139000000000000000000000000000000000000000000000000000000000000008c",
]

TX_GAS = [400000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCreateTest/CreateOOGFromCallRefundsFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(15, 0, 0, id="case0"),
        pytest.param(17, 0, 0, id="case1"),
        pytest.param(16, 0, 0, id="case2"),
        pytest.param(21, 0, 0, id="case3"),
        pytest.param(23, 0, 0, id="case4"),
        pytest.param(22, 0, 0, id="case5"),
        pytest.param(18, 0, 0, id="case6"),
        pytest.param(20, 0, 0, id="case7"),
        pytest.param(19, 0, 0, id="case8"),
        pytest.param(3, 0, 0, id="case9"),
        pytest.param(6, 0, 0, id="case10"),
        pytest.param(9, 0, 0, id="case11"),
        pytest.param(0, 0, 0, id="case12"),
        pytest.param(2, 0, 0, id="case13"),
        pytest.param(4, 0, 0, id="case14"),
        pytest.param(5, 0, 0, id="case15"),
        pytest.param(7, 0, 0, id="case16"),
        pytest.param(8, 0, 0, id="case17"),
        pytest.param(10, 0, 0, id="case18"),
        pytest.param(11, 0, 0, id="case19"),
        pytest.param(1, 0, 0, id="case20"),
        pytest.param(12, 0, 0, id="case21"),
        pytest.param(14, 0, 0, id="case22"),
        pytest.param(13, 0, 0, id="case23"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_oog_from_call_refunds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
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
        gas_limit=4294967296,
    )

    # Source: Yul
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   return(0, 1)
    # }
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x1]
            + Op.PUSH1[0x0]
            + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)
            + Op.SSTORE(key=Op.DUP3, value=Op.DUP1)
            + Op.RETURN
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000001a"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   return(0, 5000)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.SSTORE(key=0x1, value=0x0)
            + Op.RETURN(offset=0x0, size=0x1388)
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000001b"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   invalid()
    # }
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x1]
            + Op.PUSH1[0x0]
            + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)
            + Op.SWAP1
            + Op.SSTORE
            + Op.INVALID
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000001c"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 1)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.CALL(
                gas=Op.GAS,
                address=0xC0DEA,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.RETURN(offset=0x0, size=0x1)
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000002a"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 5000)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.CALL(
                gas=Op.GAS,
                address=0xC0DEA,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.RETURN(offset=0x0, size=0x1388)
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000002b"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))  # noqa: E501
    #   invalid()
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0xC0DEA,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=0x0,
                ),
            )
            + Op.INVALID
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000002c"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(delegatecall(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 1)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.DELEGATECALL(
                gas=Op.GAS,
                address=0xC0DEA,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.RETURN(offset=0x0, size=0x1)
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000003a"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(delegatecall(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 5000)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.DELEGATECALL(
                gas=Op.GAS,
                address=0xC0DEA,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.RETURN(offset=0x0, size=0x1388)
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000003b"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(delegatecall(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0))  # noqa: E501
    #   invalid()
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=Op.GAS,
                    address=0xC0DEA,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=0x0,
                ),
            )
            + Op.INVALID
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000003c"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(callcode(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 1)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.CALLCODE(
                gas=Op.GAS,
                address=0xC0DEA,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.RETURN(offset=0x0, size=0x1)
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000004a"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(callcode(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 5000)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.CALLCODE(
                gas=Op.GAS,
                address=0xC0DEA,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.RETURN(offset=0x0, size=0x1388)
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000004b"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(callcode(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))  # noqa: E501
    #   invalid()
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.POP(
                Op.CALLCODE(
                    gas=Op.GAS,
                    address=0xC0DEA,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=0x0,
                ),
            )
            + Op.INVALID
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000004c"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deD, 0, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 1)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.CALL(
                gas=Op.GAS,
                address=0xC0DED,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.RETURN(offset=0x0, size=0x1)
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000005a"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deD, 0, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 5000)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.CALL(
                gas=Op.GAS,
                address=0xC0DED,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.RETURN(offset=0x0, size=0x1388)
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000005b"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deD, 0, 0, 0, 0, 0))  # noqa: E501
    #   invalid()
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0xC0DED,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=0x0,
                ),
            )
            + Op.INVALID
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000005c"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0de0, 0, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 1)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.CALL(
                gas=Op.GAS,
                address=0xC0DE0,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.RETURN(offset=0x0, size=0x1)
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000006a"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0de0, 0, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 5000)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.CALL(
                gas=Op.GAS,
                address=0xC0DE0,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.RETURN(offset=0x0, size=0x1388)
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000006b"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0de0, 0, 0, 0, 0, 0))  # noqa: E501
    #   invalid()
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0xC0DE0,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=0x0,
                ),
            )
            + Op.INVALID
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000006c"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   let initcodeaddr := 0x00000000000000000000000000000000000c0de1
    #   let initcodelength := extcodesize(initcodeaddr)
    #   extcodecopy(initcodeaddr, 0, 0, initcodelength)
    #   pop(create(0, 0, initcodelength))
    #   return(add(initcodelength, 1), 1)
    # }
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x1]
            + Op.PUSH1[0x0]
            + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)
            + Op.SSTORE(key=Op.DUP3, value=Op.DUP1)
            + Op.DUP2
            + Op.SWAP1
            + Op.PUSH3[0xC0DE1]
            + Op.EXTCODESIZE(address=Op.DUP1)
            + Op.SWAP2
            + Op.DUP3
            + Op.SWAP2
            + Op.DUP2
            + Op.SWAP1
            + Op.EXTCODECOPY
            + Op.POP(Op.CREATE(value=Op.DUP1, offset=0x0, size=Op.DUP1))
            + Op.ADD
            + Op.RETURN
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000007a"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   let initcodeaddr := 0x00000000000000000000000000000000000c0de1
    #   let initcodelength := extcodesize(initcodeaddr)
    #   extcodecopy(initcodeaddr, 0, 0, initcodelength)
    #   pop(create(0, 0, initcodelength))
    #   return(add(initcodelength, 1), 5000)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.SSTORE(key=0x1, value=0x0)
            + Op.PUSH2[0x1388]
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x0]
            + Op.PUSH3[0xC0DE1]
            + Op.DUP2
            + Op.EXTCODESIZE(address=Op.DUP2)
            + Op.SWAP3
            + Op.DUP4
            + Op.SWAP3
            + Op.EXTCODECOPY
            + Op.POP(Op.CREATE(value=Op.DUP1, offset=0x0, size=Op.DUP1))
            + Op.ADD
            + Op.RETURN
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000007b"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   let initcodeaddr := 0x00000000000000000000000000000000000c0de1
    #   let initcodelength := extcodesize(initcodeaddr)
    #   extcodecopy(initcodeaddr, 0, 0, initcodelength)
    #   pop(create(0, 0, initcodelength))
    #   invalid()
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.SSTORE(key=0x1, value=0x0)
            + Op.PUSH1[0x0]
            + Op.PUSH3[0xC0DE1]
            + Op.DUP2
            + Op.EXTCODESIZE(address=Op.DUP2)
            + Op.SWAP3
            + Op.DUP4
            + Op.SWAP3
            + Op.EXTCODECOPY
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.POP(Op.CREATE)
            + Op.INVALID
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000007c"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   let initcodeaddr := 0x00000000000000000000000000000000000c0de1
    #   //let initcodelength := extcodesize(initcodeaddr)
    #   //extcodecopy(initcodeaddr, 0, 0, initcodelength)
    #
    #   // protection from solc version changing init code
    #   let initcodelength := 15
    #   mstore(0, 0x6001600055600060005560016000f30000000000000000000000000000000000)  # noqa: E501
    #
    #   pop(create2(0, 0, initcodelength, 0))
    #   return(add(initcodelength, 1), 1)
    # }
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x1]
            + Op.PUSH1[0x0]
            + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)
            + Op.SSTORE(key=Op.DUP3, value=Op.DUP1)
            + Op.MSTORE(
                offset=Op.DUP2,
                value=0x6001600055600060005560016000F30000000000000000000000000000000000,  # noqa: E501
            )
            + Op.DUP2
            + Op.SWAP1
            + Op.PUSH1[0xF]
            + Op.SWAP1
            + Op.DUP2
            + Op.DUP2
            + Op.DUP1
            + Op.POP(Op.CREATE2)
            + Op.ADD
            + Op.RETURN
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000008a"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   let initcodeaddr := 0x00000000000000000000000000000000000c0de1
    #   let initcodelength := extcodesize(initcodeaddr)
    #   extcodecopy(initcodeaddr, 0, 0, initcodelength)
    #   pop(create2(0, 0, initcodelength, 0))
    #   return(add(initcodelength, 1), 5000)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.SSTORE(key=0x1, value=0x0)
            + Op.PUSH2[0x1388]
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x0]
            + Op.PUSH3[0xC0DE1]
            + Op.DUP2
            + Op.EXTCODESIZE(address=Op.DUP2)
            + Op.SWAP3
            + Op.DUP4
            + Op.SWAP3
            + Op.EXTCODECOPY
            + Op.POP(
                Op.CREATE2(
                    value=Op.DUP1, offset=Op.DUP2, size=Op.DUP2, salt=0x0
                ),
            )
            + Op.ADD
            + Op.RETURN
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000008b"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   let initcodeaddr := 0x00000000000000000000000000000000000c0de1
    #   let initcodelength := extcodesize(initcodeaddr)
    #   extcodecopy(initcodeaddr, 0, 0, initcodelength)
    #   pop(create2(0, 0, initcodelength, 0))
    #   invalid()
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x1)
            + Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.SSTORE(key=0x1, value=0x0)
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.PUSH3[0xC0DE1]
            + Op.DUP2
            + Op.EXTCODESIZE(address=Op.DUP2)
            + Op.SWAP3
            + Op.DUP4
            + Op.SWAP3
            + Op.EXTCODECOPY
            + Op.DUP2
            + Op.DUP1
            + Op.POP(Op.CREATE2)
            + Op.INVALID
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000008c"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   mstore(0, 0xff)
    #   log0(0, 32)
    #   log1(0, 32, 0xfa)
    #   log2(0, 32, 0xfa, 0xfb)
    #   log3(0, 32, 0xfa, 0xfb, 0xfc)
    #   log4(0, 32, 0xfa, 0xfb, 0xfc, 0xfd)
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0xFF)
            + Op.LOG0(offset=0x0, size=0x20)
            + Op.LOG1(offset=0x0, size=0x20, topic_1=0xFA)
            + Op.LOG2(offset=0x0, size=0x20, topic_1=0xFA, topic_2=0xFB)
            + Op.LOG3(
                offset=0x0,
                size=0x20,
                topic_1=0xFA,
                topic_2=0xFB,
                topic_3=0xFC,
            )
            + Op.LOG4(
                offset=0x0,
                size=0x20,
                topic_1=0xFA,
                topic_2=0xFB,
                topic_3=0xFC,
                topic_4=0xFD,
            )
            + Op.STOP
        ),
        storage={0x1: 0x1},
        address=Address("0x00000000000000000000000000000000000c0de0"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   sstore(0, 1)
    #   sstore(0, 0)
    #   return(0, 1)
    # }
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.SSTORE(key=Op.DUP1, value=Op.DUP1)
            + Op.PUSH1[0x1]
            + Op.SWAP1
            + Op.RETURN
        ),
        address=Address("0x00000000000000000000000000000000000c0de1"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   // Simple SSTORE to zero to get a refund
    #   sstore(1, 0)
    # }
    pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={0x1: 0x1},
        address=Address("0x00000000000000000000000000000000000c0dea"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   selfdestruct(origin())
    # }
    callee_27 = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=Op.ORIGIN),
        storage={0x1: 0x1},
        address=Address("0x00000000000000000000000000000000000c0ded"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3D0900, nonce=1)
    # Source: Yul
    # {
    #   let init_addr := calldataload(4)
    #   let init_length := extcodesize(init_addr)
    #   extcodecopy(init_addr, 0, 0, init_length)
    #   let created_addr := create(0, 0, init_length)
    #   if eq(created_addr, 0) {
    #     /* This invalid will deplete the remaining gas to make refund check deterministic */  # noqa: E501
    #     invalid()
    #   }
    # }
    contract = pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.DUP1
            + Op.CALLDATALOAD(offset=0x4)
            + Op.DUP2
            + Op.EXTCODESIZE(address=Op.DUP2)
            + Op.SWAP3
            + Op.DUP4
            + Op.SWAP3
            + Op.EXTCODECOPY
            + Op.DUP2
            + Op.JUMPI(pc=0x15, condition=Op.EQ(Op.CREATE, Op.DUP1))
            + Op.STOP
            + Op.JUMPDEST
            + Op.INVALID
        ),
        address=Address("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": [0, 9, 3, 6], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x4501f8fa1e67827ebfb1f6d5510c606871c5a599"): Account(
                    storage={0: 1}, nonce=1, code=bytes.fromhex("00")
                ),
                sender: Account(nonce=2),
            },
        },
        {
            "indexes": {
                "data": [1, 2, 4, 5, 7, 8, 10, 11],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {
                Address(
                    "0x4501f8fa1e67827ebfb1f6d5510c606871c5a599"
                ): Account.NONEXISTENT,
                sender: Account(nonce=2, balance=0),
            },
        },
        {
            "indexes": {"data": [12], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                callee_27: Account(nonce=1, balance=0),
                Address("0x4501f8fa1e67827ebfb1f6d5510c606871c5a599"): Account(
                    storage={0: 1}, nonce=1, code=bytes.fromhex("00")
                ),
                sender: Account(nonce=2),
            },
        },
        {
            "indexes": {"data": [13, 14], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                callee_27: Account(
                    storage={1: 1}, nonce=1, code=bytes.fromhex("32FF")
                ),
                Address(
                    "0x4501f8fa1e67827ebfb1f6d5510c606871c5a599"
                ): Account.NONEXISTENT,
                sender: Account(nonce=2, balance=0),
            },
        },
        {
            "indexes": {"data": [15], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x4501f8fa1e67827ebfb1f6d5510c606871c5a599"): Account(
                    storage={0: 1}, nonce=1, code=bytes.fromhex("00")
                ),
                sender: Account(nonce=2),
            },
        },
        {
            "indexes": {"data": [16, 17], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(
                    "0x4501f8fa1e67827ebfb1f6d5510c606871c5a599"
                ): Account.NONEXISTENT,
                sender: Account(nonce=2, balance=0),
            },
        },
        {
            "indexes": {"data": [18], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x4501f8fa1e67827ebfb1f6d5510c606871c5a599"): Account(
                    storage={0: 1}, nonce=2, code=bytes.fromhex("00")
                ),
                Address("0x522c2e1c5da65010908ef9929e327fe8b6cc86da"): Account(
                    storage={}, nonce=1, code=bytes.fromhex("00")
                ),
                sender: Account(nonce=2),
            },
        },
        {
            "indexes": {"data": [19, 20], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(
                    "0x4501f8fa1e67827ebfb1f6d5510c606871c5a599"
                ): Account.NONEXISTENT,
                Address(
                    "0x522c2e1c5da65010908ef9929e327fe8b6cc86da"
                ): Account.NONEXISTENT,
                sender: Account(nonce=2, balance=0),
            },
        },
        {
            "indexes": {"data": [21], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x06019547b6e360abdafeade158a9667cc6106c17"): Account(
                    storage={}, nonce=1, code=bytes.fromhex("00")
                ),
                Address("0x4501f8fa1e67827ebfb1f6d5510c606871c5a599"): Account(
                    storage={0: 1}, nonce=2, code=bytes.fromhex("00")
                ),
                sender: Account(nonce=2),
            },
        },
        {
            "indexes": {"data": [22, 23], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(
                    "0x06019547b6e360abdafeade158a9667cc6106c17"
                ): Account.NONEXISTENT,
                Address(
                    "0x4501f8fa1e67827ebfb1f6d5510c606871c5a599"
                ): Account.NONEXISTENT,
                sender: Account(nonce=2, balance=0),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

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
