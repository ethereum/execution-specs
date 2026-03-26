"""
test_create2_oog_from_call_refunds

Ported from:
state_tests/stCreate2/Create2OOGFromCallRefundsFiller.yml
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
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stCreate2/Create2OOGFromCallRefundsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="SStore_Refund_NoOoG",
        ),
        pytest.param(
            1, 0, 0,
            id="SStore_Refund_OoG",
        ),
        pytest.param(
            2, 0, 0,
            id="SStore_Refund_OoG",
        ),
        pytest.param(
            3, 0, 0,
            id="SStore_Call_Refund_NoOoG",
        ),
        pytest.param(
            4, 0, 0,
            id="SStore_Refund_OoG",
        ),
        pytest.param(
            5, 0, 0,
            id="SStore_Refund_OoG",
        ),
        pytest.param(
            6, 0, 0,
            id="SStore_DelegateCall_Refund_NoOoG",
        ),
        pytest.param(
            7, 0, 0,
            id="SStore_Refund_OoG",
        ),
        pytest.param(
            8, 0, 0,
            id="SStore_Refund_OoG",
        ),
        pytest.param(
            9, 0, 0,
            id="SStore_CallCode_Refund_NoOoG",
        ),
        pytest.param(
            10, 0, 0,
            id="SStore_Refund_OoG",
        ),
        pytest.param(
            11, 0, 0,
            id="SStore_Refund_OoG",
        ),
        pytest.param(
            12, 0, 0,
            id="SelfDestruct_Refund_NoOoG",
        ),
        pytest.param(
            13, 0, 0,
            id="SelfDestruct_Refund_OoG",
        ),
        pytest.param(
            14, 0, 0,
            id="SelfDestruct_Refund_OoG",
        ),
        pytest.param(
            15, 0, 0,
            id="LogOp_NoOoG",
        ),
        pytest.param(
            16, 0, 0,
            id="LogOp_OoG",
        ),
        pytest.param(
            17, 0, 0,
            id="LogOp_OoG",
        ),
        pytest.param(
            18, 0, 0,
            id="SStore_Create_Refund_NoOoG",
        ),
        pytest.param(
            19, 0, 0,
            id="SStore_Create_Refund_OoG",
        ),
        pytest.param(
            20, 0, 0,
            id="SStore_Create_Refund_OoG",
        ),
        pytest.param(
            21, 0, 0,
            id="SStore_Create2_Refund_NoOoG",
        ),
        pytest.param(
            22, 0, 0,
            id="SStore_Create2_Refund_OoG",
        ),
        pytest.param(
            23, 0, 0,
            id="SStore_Create2_Refund_OoG",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2_oog_from_call_refunds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_create2_oog_from_call_refunds"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    contract_1 = Address("0x000000000000000000000000000000000000001a")
    contract_2 = Address("0x000000000000000000000000000000000000001b")
    contract_3 = Address("0x000000000000000000000000000000000000001c")
    contract_4 = Address("0x000000000000000000000000000000000000002a")
    contract_5 = Address("0x000000000000000000000000000000000000002b")
    contract_6 = Address("0x000000000000000000000000000000000000002c")
    contract_7 = Address("0x000000000000000000000000000000000000003a")
    contract_8 = Address("0x000000000000000000000000000000000000003b")
    contract_9 = Address("0x000000000000000000000000000000000000003c")
    contract_10 = Address("0x000000000000000000000000000000000000004a")
    contract_11 = Address("0x000000000000000000000000000000000000004b")
    contract_12 = Address("0x000000000000000000000000000000000000004c")
    contract_13 = Address("0x000000000000000000000000000000000000005a")
    contract_14 = Address("0x000000000000000000000000000000000000005b")
    contract_15 = Address("0x000000000000000000000000000000000000005c")
    contract_16 = Address("0x000000000000000000000000000000000000006a")
    contract_17 = Address("0x000000000000000000000000000000000000006b")
    contract_18 = Address("0x000000000000000000000000000000000000006c")
    contract_19 = Address("0x000000000000000000000000000000000000007a")
    contract_20 = Address("0x000000000000000000000000000000000000007b")
    contract_21 = Address("0x000000000000000000000000000000000000007c")
    contract_22 = Address("0x000000000000000000000000000000000000008a")
    contract_23 = Address("0x000000000000000000000000000000000000008b")
    contract_24 = Address("0x000000000000000000000000000000000000008c")
    contract_25 = Address("0x00000000000000000000000000000000000c0dea")
    contract_26 = Address("0x00000000000000000000000000000000000c0ded")
    contract_27 = Address("0x00000000000000000000000000000000000c0de0")
    contract_28 = Address("0x00000000000000000000000000000000000c0de1")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=4294967296,
    )

    pre[sender] = Account(balance=0x3d0900, nonce=1)
    # Source: yul
    # berlin
    # {
    #   let init_addr := calldataload(4)
    #   let init_length := extcodesize(init_addr)
    #   extcodecopy(init_addr, 0, 0, init_length)
    #   let created_addr := create2(0, 0, init_length, 0)
    #   if eq(created_addr, 0) {
    #     /* This invalid will deplete the remaining gas to make refund check deterministic */
    #     invalid()
    #   }
    # }
    contract_0 = pre.deploy_contract(
        code=Op.PUSH1[0x0] + Op.DUP1 * 2 + Op.CALLDATALOAD(offset=0x4) + Op.DUP2
        + Op.EXTCODESIZE(address=Op.DUP2) + Op.SWAP3 + Op.DUP4 + Op.SWAP3
        + Op.EXTCODECOPY + Op.DUP2
        + Op.JUMPI(pc=0x16, condition=Op.EQ(Op.CREATE2, Op.DUP1)) + Op.STOP
        + Op.JUMPDEST + Op.INVALID,
        nonce=1,
        address=Address("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   return(0, 1)
    # }
    contract_1 = pre.deploy_contract(
        code=Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)  # noqa: E501
        + Op.SSTORE(key=Op.DUP3, value=Op.DUP1) + Op.RETURN,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000001a"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   return(0, 5000)
    # }
    contract_2 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1) + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.SSTORE(key=0x1, value=0x0) + Op.RETURN(offset=0x0, size=0x1388),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000001b"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   invalid()
    # }
    contract_3 = pre.deploy_contract(
        code=Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)  # noqa: E501
        + Op.SWAP1 + Op.SSTORE + Op.INVALID,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000001c"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))
    #   return(0, 1)
    #   let noOpt := msize()
    # }
    contract_4 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.CALL(gas=Op.GAS, address=0xc0dea, value=Op.DUP1, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0)
        + Op.RETURN(offset=0x0, size=0x1),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000002a"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))
    #   return(0, 5000)
    # }
    contract_5 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.CALL(gas=Op.GAS, address=0xc0dea, value=Op.DUP1, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0)
        + Op.RETURN(offset=0x0, size=0x1388),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000002b"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))
    #   invalid()
    # }
    contract_6 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.POP(Op.CALL(gas=Op.GAS, address=0xc0dea, value=Op.DUP1, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.INVALID,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000002c"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(delegatecall(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0))
    #   return(0, 1)
    #   let noOpt := msize()
    # }
    contract_7 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1) + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.DELEGATECALL(gas=Op.GAS, address=0xc0dea, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0)
        + Op.RETURN(offset=0x0, size=0x1),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000003a"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(delegatecall(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0))
    #   return(0, 5000)
    # }
    contract_8 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1) + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.DELEGATECALL(gas=Op.GAS, address=0xc0dea, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0)
        + Op.RETURN(offset=0x0, size=0x1388),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000003b"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(delegatecall(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0))
    #   invalid()
    # }
    contract_9 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1) + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=0xc0dea, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.INVALID,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000003c"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(callcode(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))
    #   return(0, 1)
    #   let noOpt := msize()
    # }
    contract_10 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1) + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.CALLCODE(gas=Op.GAS, address=0xc0dea, value=Op.DUP1, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0)
        + Op.RETURN(offset=0x0, size=0x1),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000004a"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(callcode(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))
    #   return(0, 5000)
    # }
    contract_11 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1) + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.CALLCODE(gas=Op.GAS, address=0xc0dea, value=Op.DUP1, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0)
        + Op.RETURN(offset=0x0, size=0x1388),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000004b"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(callcode(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))
    #   invalid()
    # }
    contract_12 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1) + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.POP(Op.CALLCODE(gas=Op.GAS, address=0xc0dea, value=Op.DUP1, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.INVALID,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000004c"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deD, 0, 0, 0, 0, 0))
    #   return(0, 1)
    #   let noOpt := msize()
    # }
    contract_13 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.CALL(gas=Op.GAS, address=0xc0ded, value=Op.DUP1, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0)
        + Op.RETURN(offset=0x0, size=0x1),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000005a"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deD, 0, 0, 0, 0, 0))
    #   return(0, 5000)
    # }
    contract_14 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.CALL(gas=Op.GAS, address=0xc0ded, value=Op.DUP1, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0)
        + Op.RETURN(offset=0x0, size=0x1388),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000005b"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deD, 0, 0, 0, 0, 0))
    #   invalid()
    # }
    contract_15 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.POP(Op.CALL(gas=Op.GAS, address=0xc0ded, value=Op.DUP1, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.INVALID,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000005c"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0de0, 0, 0, 0, 0, 0))
    #   return(0, 1)
    #   let noOpt := msize()
    # }
    contract_16 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.CALL(gas=Op.GAS, address=0xc0de0, value=Op.DUP1, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0)
        + Op.RETURN(offset=0x0, size=0x1),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000006a"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0de0, 0, 0, 0, 0, 0))
    #   return(0, 5000)
    # }
    contract_17 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.CALL(gas=Op.GAS, address=0xc0de0, value=Op.DUP1, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0)
        + Op.RETURN(offset=0x0, size=0x1388),
        nonce=0,
        address=Address("0x000000000000000000000000000000000000006b"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0de0, 0, 0, 0, 0, 0))
    #   invalid()
    # }
    contract_18 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.POP(Op.CALL(gas=Op.GAS, address=0xc0de0, value=Op.DUP1, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0))
        + Op.INVALID,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000006c"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   let initcodeaddr := 0x00000000000000000000000000000000000c0de1
    #   let initcodelength := extcodesize(initcodeaddr)
    #   extcodecopy(initcodeaddr, 0, 0, initcodelength)
    #   pop(create(0, 0, initcodelength))
    #   return(add(initcodelength, 1), 1)
    #   let noOptimization := msize()
    # }
    contract_19 = pre.deploy_contract(
        code=Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)  # noqa: E501
        + Op.SSTORE(key=Op.DUP3, value=Op.DUP1) + Op.DUP2 + Op.SWAP1
        + Op.PUSH3[0xc0de1] + Op.EXTCODESIZE(address=Op.DUP1) + Op.SWAP2
        + Op.DUP3 + Op.SWAP2 + Op.DUP2 + Op.SWAP1 + Op.EXTCODECOPY
        + Op.POP(Op.CREATE(value=Op.DUP1, offset=0x0, size=Op.DUP1)) + Op.ADD
        + Op.RETURN,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000007a"),  # noqa: E501
    )
    # Source: yul
    # berlin
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
    contract_20 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1) + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.SSTORE(key=0x1, value=0x0) + Op.PUSH2[0x1388] + Op.PUSH1[0x1]
        + Op.PUSH1[0x0] + Op.PUSH3[0xc0de1] + Op.DUP2
        + Op.EXTCODESIZE(address=Op.DUP2) + Op.SWAP3 + Op.DUP4 + Op.SWAP3
        + Op.EXTCODECOPY
        + Op.POP(Op.CREATE(value=Op.DUP1, offset=0x0, size=Op.DUP1)) + Op.ADD
        + Op.RETURN,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000007b"),  # noqa: E501
    )
    # Source: yul
    # berlin
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
    contract_21 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1) + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.SSTORE(key=0x1, value=0x0) + Op.PUSH1[0x0] + Op.PUSH3[0xc0de1]
        + Op.DUP2 + Op.EXTCODESIZE(address=Op.DUP2) + Op.SWAP3 + Op.DUP4
        + Op.SWAP3 + Op.EXTCODECOPY + Op.PUSH1[0x0] + Op.DUP1 + Op.POP(Op.CREATE)
        + Op.INVALID,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000007c"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   let initcodeaddr := 0x00000000000000000000000000000000000c0de1
    #   let initcodelength := extcodesize(initcodeaddr)
    #   extcodecopy(initcodeaddr, 0, 0, initcodelength)
    #   pop(create2(0, 0, initcodelength, 0))
    #   return(add(initcodelength, 1), 1)
    #   let noOpt := msize()
    # }
    contract_22 = pre.deploy_contract(
        code=Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)  # noqa: E501
        + Op.SSTORE(key=Op.DUP3, value=Op.DUP1) + Op.DUP2 + Op.SWAP1
        + Op.PUSH3[0xc0de1] + Op.EXTCODESIZE(address=Op.DUP1) + Op.SWAP2
        + Op.DUP3 + Op.SWAP2 + Op.DUP2 + Op.SWAP1 + Op.EXTCODECOPY
        + Op.POP(Op.CREATE2(value=Op.DUP1, offset=Op.DUP2, size=Op.DUP2, salt=0x0))
        + Op.ADD + Op.RETURN,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000008a"),  # noqa: E501
    )
    # Source: yul
    # berlin
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
    contract_23 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1) + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.SSTORE(key=0x1, value=0x0) + Op.PUSH2[0x1388] + Op.PUSH1[0x1]
        + Op.PUSH1[0x0] + Op.PUSH3[0xc0de1] + Op.DUP2
        + Op.EXTCODESIZE(address=Op.DUP2) + Op.SWAP3 + Op.DUP4 + Op.SWAP3
        + Op.EXTCODECOPY
        + Op.POP(Op.CREATE2(value=Op.DUP1, offset=Op.DUP2, size=Op.DUP2, salt=0x0))
        + Op.ADD + Op.RETURN,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000008b"),  # noqa: E501
    )
    # Source: yul
    # berlin
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
    contract_24 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1) + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.SSTORE(key=0x1, value=0x0) + Op.PUSH1[0x0] + Op.DUP1
        + Op.PUSH3[0xc0de1] + Op.DUP2 + Op.EXTCODESIZE(address=Op.DUP2)
        + Op.SWAP3 + Op.DUP4 + Op.SWAP3 + Op.EXTCODECOPY + Op.DUP2 + Op.DUP1
        + Op.POP(Op.CREATE2) + Op.INVALID,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000008c"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   // Simple SSTORE to zero to get a refund
    #   sstore(1, 0)
    # }
    contract_25 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 1},
        nonce=1,
        address=Address("0x00000000000000000000000000000000000c0dea"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   selfdestruct(origin())
    # }
    contract_26 = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=Op.ORIGIN),
        storage={1: 1},
        nonce=1,
        address=Address("0x00000000000000000000000000000000000c0ded"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   mstore(0, 0xff)
    #   log0(0, 32)
    #   log1(0, 32, 0xfa)
    #   log2(0, 32, 0xfa, 0xfb)
    #   log3(0, 32, 0xfa, 0xfb, 0xfc)
    #   log4(0, 32, 0xfa, 0xfb, 0xfc, 0xfd)
    # }
    contract_27 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xff) + Op.LOG0(offset=0x0, size=0x20)
        + Op.LOG1(offset=0x0, size=0x20, topic_1=0xfa)
        + Op.LOG2(offset=0x0, size=0x20, topic_1=0xfa, topic_2=0xfb)
        + Op.LOG3(offset=0x0, size=0x20, topic_1=0xfa, topic_2=0xfb, topic_3=0xfc)
        + Op.LOG4(offset=0x0, size=0x20, topic_1=0xfa, topic_2=0xfb, topic_3=0xfc, topic_4=0xfd)
        + Op.STOP,
        storage={1: 1},
        nonce=1,
        address=Address("0x00000000000000000000000000000000000c0de0"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(0, 0)
    #   return(0, 1)
    # }
    contract_28 = pre.deploy_contract(
        code=Op.PUSH1[0x0] + Op.SSTORE(key=Op.DUP1, value=Op.DUP1) + Op.PUSH1[0x1]  # noqa: E501
        + Op.SWAP1 + Op.RETURN,
        nonce=1,
        address=Address("0x00000000000000000000000000000000000c0de1"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=2),
        Address("0xcfb6834f84b9e726f5f8aef446d585b732abdd99"): Account(storage={0: 1}, code=bytes.fromhex("00"), nonce=1),  # noqa: E501
    },
        },
        {
            "indexes": {'data': [3], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=2),
        Address("0xd615c5eaff84f487cff253b50dc18517fc8385b0"): Account(storage={0: 1}, code=bytes.fromhex("00"), nonce=1),  # noqa: E501
    },
        },
        {
            "indexes": {'data': [6], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=2),
        Address("0x0d44b2ad06c5c9f9a86c9edf8d13fb7d44fe756c"): Account(storage={0: 1}, code=bytes.fromhex("00"), nonce=1),  # noqa: E501
    },
        },
        {
            "indexes": {'data': [9], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=2),
        Address("0x858ec13538276b49d5ece2a408c8331ccb79ad89"): Account(storage={0: 1}, code=bytes.fromhex("00"), nonce=1),  # noqa: E501
    },
        },
        {
            "indexes": {'data': [1, 2, 4, 5, 7, 8, 10, 11], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(balance=0, nonce=2),
        Address("0x95e88628c53b5c0e40ff6de65a3cf8cdc3b477f7"): Account.NONEXISTENT,  # noqa: E501
        Address("0x66e1cc2616a273450621c8cc5e91d8cfd92494fa"): Account.NONEXISTENT,  # noqa: E501
        Address("0x6175ba9976476425b1cda8e1da479768fb429542"): Account.NONEXISTENT,  # noqa: E501
        Address("0x8dff0e448f1e078e9b8a7fcf0bf6c291f167aaef"): Account.NONEXISTENT,  # noqa: E501
        Address("0xa2c4270800a5dbeea48464e5f2420efb1747725a"): Account.NONEXISTENT,  # noqa: E501
        Address("0x4d80f1150ee236adfaab47c70df90e757cef1141"): Account.NONEXISTENT,  # noqa: E501
        Address("0x0566dc8dabc80fad3ed9ab2b4309ebfd98894f44"): Account.NONEXISTENT,  # noqa: E501
        Address("0x55305cc46bdaf1e755a05a771d55cfec3fedef90"): Account.NONEXISTENT,  # noqa: E501
    },
        },
        {
            "indexes": {'data': [12], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=2),
        Address("0xd83e541aa11c5ae1e9c847aa1728d5bc47d32faf"): Account(storage={0: 1}, code=bytes.fromhex("00"), nonce=1),  # noqa: E501
        contract_26: Account(balance=0, nonce=1),
    },
        },
        {
            "indexes": {'data': [13, 14], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(balance=0, nonce=2),
        Address("0x8f6e6c741ac95c1a9109850ea1a3ffc722dc3bf8"): Account.NONEXISTENT,  # noqa: E501
        Address("0x1f5d187bb3a48dbb2c011d0a6e731ac8131799ad"): Account.NONEXISTENT,  # noqa: E501
        contract_26: Account(storage={1: 1}, code=bytes.fromhex("32ff"), nonce=1),  # noqa: E501
    },
        },
        {
            "indexes": {'data': [15], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=2),
        Address("0x2a2141ed764598d4c5a8b6e036987928d5ec6bea"): Account(storage={0: 1}, code=bytes.fromhex("00"), nonce=1),  # noqa: E501
    },
        },
        {
            "indexes": {'data': [16, 17], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(balance=0, nonce=2),
        Address("0x74b39291dfc237c0d42fd15457754778f51c6de8"): Account.NONEXISTENT,  # noqa: E501
        Address("0x3399c78929eab89c673a8986ff7ca9ccc49db454"): Account.NONEXISTENT,  # noqa: E501
    },
        },
        {
            "indexes": {'data': [18], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=2),
        Address("0xdeb7d920f2653a8eddcffca0a77f56fcd788c00a"): Account(storage={0: 1}, code=bytes.fromhex("00"), nonce=2),  # noqa: E501
        Address("0x8109d28de74bfac2f298ec019548b8c346e51310"): Account(storage={}, code=bytes.fromhex("00"), nonce=1),  # noqa: E501
    },
        },
        {
            "indexes": {'data': [19, 20], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(balance=0, nonce=2),
        Address("0xf922b2f70110c83f8ec7df512b41bac5627e8e59"): Account.NONEXISTENT,  # noqa: E501
        Address("0x2ca788d22e21134ab1909266ed3b6c352e2a07cb"): Account.NONEXISTENT,  # noqa: E501
        Address("0x398426e736801fe712df1ef078a3b6ca3c6f063b"): Account.NONEXISTENT,  # noqa: E501
        Address("0xb520686759ced3bc9d8898e02ee41623032ff47f"): Account.NONEXISTENT,  # noqa: E501
    },
        },
        {
            "indexes": {'data': [21], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(nonce=2),
        Address("0x5a2664b55822aa3c6d9d90fec18b4c87cde07d04"): Account(storage={0: 1}, code=bytes.fromhex("00"), nonce=2),  # noqa: E501
        Address("0x442ed1b502544d146e46b5d9849a476aebd3b8db"): Account(storage={}, code=bytes.fromhex("00"), nonce=1),  # noqa: E501
    },
        },
        {
            "indexes": {'data': [22, 23], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        sender: Account(balance=0, nonce=2),
        Address("0xdd2c53bfcaf5c1d698a2b21c0908f15f7fbfd635"): Account.NONEXISTENT,  # noqa: E501
        Address("0x2d556bdbcc37c7a021879a21abe25d1850d4fd36"): Account.NONEXISTENT,  # noqa: E501
        Address("0xa99da4ea490335c986d52b0cc9e3f78b286ac5fc"): Account.NONEXISTENT,  # noqa: E501
        Address("0xb4ab8ab0d363765586925e35c715e342e4ae3c63"): Account.NONEXISTENT,  # noqa: E501
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=1,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
