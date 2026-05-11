"""
Test_create2_oog_from_call_refunds.

Ported from:
state_tests/stCreate2/Create2OOGFromCallRefundsFiller.yml
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
    ["state_tests/stCreate2/Create2OOGFromCallRefundsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="SStore_Refund_NoOoG",
        ),
        pytest.param(
            1,
            0,
            0,
            id="SStore_Refund_OoG",
        ),
        pytest.param(
            2,
            0,
            0,
            id="SStore_Refund_OoG",
        ),
        pytest.param(
            3,
            0,
            0,
            id="SStore_Call_Refund_NoOoG",
        ),
        pytest.param(
            4,
            0,
            0,
            id="SStore_Refund_OoG",
        ),
        pytest.param(
            5,
            0,
            0,
            id="SStore_Refund_OoG",
        ),
        pytest.param(
            6,
            0,
            0,
            id="SStore_DelegateCall_Refund_NoOoG",
        ),
        pytest.param(
            7,
            0,
            0,
            id="SStore_Refund_OoG",
        ),
        pytest.param(
            8,
            0,
            0,
            id="SStore_Refund_OoG",
        ),
        pytest.param(
            9,
            0,
            0,
            id="SStore_CallCode_Refund_NoOoG",
        ),
        pytest.param(
            10,
            0,
            0,
            id="SStore_Refund_OoG",
        ),
        pytest.param(
            11,
            0,
            0,
            id="SStore_Refund_OoG",
        ),
        pytest.param(
            12,
            0,
            0,
            id="SelfDestruct_Refund_NoOoG",
        ),
        pytest.param(
            13,
            0,
            0,
            id="SelfDestruct_Refund_OoG",
        ),
        pytest.param(
            14,
            0,
            0,
            id="SelfDestruct_Refund_OoG",
        ),
        pytest.param(
            15,
            0,
            0,
            id="LogOp_NoOoG",
        ),
        pytest.param(
            16,
            0,
            0,
            id="LogOp_OoG",
        ),
        pytest.param(
            17,
            0,
            0,
            id="LogOp_OoG",
        ),
        pytest.param(
            18,
            0,
            0,
            id="SStore_Create_Refund_NoOoG",
        ),
        pytest.param(
            19,
            0,
            0,
            id="SStore_Create_Refund_OoG",
        ),
        pytest.param(
            20,
            0,
            0,
            id="SStore_Create_Refund_OoG",
        ),
        pytest.param(
            21,
            0,
            0,
            id="SStore_Create2_Refund_NoOoG",
        ),
        pytest.param(
            22,
            0,
            0,
            id="SStore_Create2_Refund_OoG",
        ),
        pytest.param(
            23,
            0,
            0,
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
    """Test_create2_oog_from_call_refunds."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA)
    contract_1 = Address(0x000000000000000000000000000000000000001A)
    contract_2 = Address(0x000000000000000000000000000000000000001B)
    contract_3 = Address(0x000000000000000000000000000000000000001C)
    contract_4 = Address(0x000000000000000000000000000000000000002A)
    contract_5 = Address(0x000000000000000000000000000000000000002B)
    contract_6 = Address(0x000000000000000000000000000000000000002C)
    contract_7 = Address(0x000000000000000000000000000000000000003A)
    contract_8 = Address(0x000000000000000000000000000000000000003B)
    contract_9 = Address(0x000000000000000000000000000000000000003C)
    contract_10 = Address(0x000000000000000000000000000000000000004A)
    contract_11 = Address(0x000000000000000000000000000000000000004B)
    contract_12 = Address(0x000000000000000000000000000000000000004C)
    contract_13 = Address(0x000000000000000000000000000000000000005A)
    contract_14 = Address(0x000000000000000000000000000000000000005B)
    contract_15 = Address(0x000000000000000000000000000000000000005C)
    contract_16 = Address(0x000000000000000000000000000000000000006A)
    contract_17 = Address(0x000000000000000000000000000000000000006B)
    contract_18 = Address(0x000000000000000000000000000000000000006C)
    contract_19 = Address(0x000000000000000000000000000000000000007A)
    contract_20 = Address(0x000000000000000000000000000000000000007B)
    contract_21 = Address(0x000000000000000000000000000000000000007C)
    contract_22 = Address(0x000000000000000000000000000000000000008A)
    contract_23 = Address(0x000000000000000000000000000000000000008B)
    contract_24 = Address(0x000000000000000000000000000000000000008C)
    contract_25 = Address(0x00000000000000000000000000000000000C0DEA)
    contract_26 = Address(0x00000000000000000000000000000000000C0DED)
    contract_27 = Address(0x00000000000000000000000000000000000C0DE0)
    contract_28 = Address(0x00000000000000000000000000000000000C0DE1)
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

    pre[sender] = Account(balance=0x3D0900, nonce=1)
    # Source: yul
    # berlin
    # {
    #   let init_addr := calldataload(4)
    #   let init_length := extcodesize(init_addr)
    #   extcodecopy(init_addr, 0, 0, init_length)
    #   let created_addr := create2(0, 0, init_length, 0)
    #   if eq(created_addr, 0) {
    #     /* This invalid will deplete the remaining gas to make refund check deterministic */  # noqa: E501
    #     invalid()
    #   }
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.DUP1 * 2
        + Op.CALLDATALOAD(offset=0x4)
        + Op.DUP2
        + Op.EXTCODESIZE(address=Op.DUP2)
        + Op.SWAP3
        + Op.DUP4
        + Op.SWAP3
        + Op.EXTCODECOPY
        + Op.DUP2
        + Op.JUMPI(pc=0x16, condition=Op.EQ(Op.CREATE2, Op.DUP1))
        + Op.STOP
        + Op.JUMPDEST
        + Op.INVALID,
        nonce=1,
        address=Address(0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   return(0, 1)
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x1]
        + Op.PUSH1[0x0]
        + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)
        + Op.SSTORE(key=Op.DUP3, value=Op.DUP1)
        + Op.RETURN,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000001A),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   return(0, 5000)
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.SSTORE(key=0x1, value=0x0)
        + Op.RETURN(offset=0x0, size=0x1388),
        nonce=0,
        address=Address(0x000000000000000000000000000000000000001B),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   sstore(1, 0)
    #   invalid()
    # }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x1]
        + Op.PUSH1[0x0]
        + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)
        + Op.SWAP1
        + Op.SSTORE
        + Op.INVALID,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000001C),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   // Simple SSTORE to zero to get a refund
    #   sstore(1, 0)
    # }
    contract_25 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 1},
        nonce=1,
        address=Address(0x00000000000000000000000000000000000C0DEA),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   selfdestruct(origin())
    # }
    contract_26 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=Op.ORIGIN),
        storage={1: 1},
        nonce=1,
        address=Address(0x00000000000000000000000000000000000C0DED),  # noqa: E501
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
    contract_27 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0xFF)
        + Op.LOG0(offset=0x0, size=0x20)
        + Op.LOG1(offset=0x0, size=0x20, topic_1=0xFA)
        + Op.LOG2(offset=0x0, size=0x20, topic_1=0xFA, topic_2=0xFB)
        + Op.LOG3(
            offset=0x0, size=0x20, topic_1=0xFA, topic_2=0xFB, topic_3=0xFC
        )
        + Op.LOG4(
            offset=0x0,
            size=0x20,
            topic_1=0xFA,
            topic_2=0xFB,
            topic_3=0xFC,
            topic_4=0xFD,
        )
        + Op.STOP,
        storage={1: 1},
        nonce=1,
        address=Address(0x00000000000000000000000000000000000C0DE0),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(0, 0)
    #   return(0, 1)
    # }
    contract_28 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.SSTORE(key=Op.DUP1, value=Op.DUP1)
        + Op.PUSH1[0x1]
        + Op.SWAP1
        + Op.RETURN,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000C0DE1),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 1)
    #   let noOpt := msize()
    # }
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.CALL(
            gas=Op.GAS,
            address=contract_25,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.RETURN(offset=0x0, size=0x1),
        nonce=0,
        address=Address(0x000000000000000000000000000000000000002A),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 5000)
    # }
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.CALL(
            gas=Op.GAS,
            address=contract_25,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.RETURN(offset=0x0, size=0x1388),
        nonce=0,
        address=Address(0x000000000000000000000000000000000000002B),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(delegatecall(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0))  # noqa: E501
    #   invalid()
    # }
    contract_9 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=contract_25,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.INVALID,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000003C),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))  # noqa: E501
    #   invalid()
    # }
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=contract_25,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.INVALID,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000002C),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(delegatecall(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 1)
    #   let noOpt := msize()
    # }
    contract_7 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.DELEGATECALL(
            gas=Op.GAS,
            address=contract_25,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.RETURN(offset=0x0, size=0x1),
        nonce=0,
        address=Address(0x000000000000000000000000000000000000003A),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(callcode(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 5000)
    # }
    contract_11 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.CALLCODE(
            gas=Op.GAS,
            address=contract_25,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.RETURN(offset=0x0, size=0x1388),
        nonce=0,
        address=Address(0x000000000000000000000000000000000000004B),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(delegatecall(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 5000)
    # }
    contract_8 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.DELEGATECALL(
            gas=Op.GAS,
            address=contract_25,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.RETURN(offset=0x0, size=0x1388),
        nonce=0,
        address=Address(0x000000000000000000000000000000000000003B),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(callcode(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 1)
    #   let noOpt := msize()
    # }
    contract_10 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.CALLCODE(
            gas=Op.GAS,
            address=contract_25,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.RETURN(offset=0x0, size=0x1),
        nonce=0,
        address=Address(0x000000000000000000000000000000000000004A),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   sstore(1, 1)
    #   pop(callcode(gas(), 0x00000000000000000000000000000000000c0deA, 0, 0, 0, 0, 0))  # noqa: E501
    #   invalid()
    # }
    contract_12 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.POP(
            Op.CALLCODE(
                gas=Op.GAS,
                address=contract_25,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.INVALID,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000004C),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deD, 0, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 5000)
    # }
    contract_14 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.CALL(
            gas=Op.GAS,
            address=contract_26,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.RETURN(offset=0x0, size=0x1388),
        nonce=0,
        address=Address(0x000000000000000000000000000000000000005B),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deD, 0, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 1)
    #   let noOpt := msize()
    # }
    contract_13 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.CALL(
            gas=Op.GAS,
            address=contract_26,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.RETURN(offset=0x0, size=0x1),
        nonce=0,
        address=Address(0x000000000000000000000000000000000000005A),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0deD, 0, 0, 0, 0, 0))  # noqa: E501
    #   invalid()
    # }
    contract_15 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=contract_26,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.INVALID,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000005C),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0de0, 0, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 1)
    #   let noOpt := msize()
    # }
    contract_16 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.CALL(
            gas=Op.GAS,
            address=contract_27,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.RETURN(offset=0x0, size=0x1),
        nonce=0,
        address=Address(0x000000000000000000000000000000000000006A),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0de0, 0, 0, 0, 0, 0))  # noqa: E501
    #   return(0, 5000)
    # }
    contract_17 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.CALL(
            gas=Op.GAS,
            address=contract_27,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.RETURN(offset=0x0, size=0x1388),
        nonce=0,
        address=Address(0x000000000000000000000000000000000000006B),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore(0, 1)
    #   pop(call(gas(), 0x00000000000000000000000000000000000c0de0, 0, 0, 0, 0, 0))  # noqa: E501
    #   invalid()
    # }
    contract_18 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=contract_27,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.INVALID,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000006C),  # noqa: E501
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
    contract_23 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
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
            Op.CREATE2(value=Op.DUP1, offset=Op.DUP2, size=Op.DUP2, salt=0x0)
        )
        + Op.ADD
        + Op.RETURN,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000008B),  # noqa: E501
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
    contract_22 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x1]
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
        + Op.POP(
            Op.CREATE2(value=Op.DUP1, offset=Op.DUP2, size=Op.DUP2, salt=0x0)
        )
        + Op.ADD
        + Op.RETURN,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000008A),  # noqa: E501
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
    contract_24 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
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
        + Op.INVALID,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000008C),  # noqa: E501
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
    contract_20 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
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
        + Op.RETURN,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000007B),  # noqa: E501
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
    contract_21 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
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
        + Op.INVALID,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000007C),  # noqa: E501
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
    contract_19 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x1]
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
        + Op.RETURN,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000007A),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=2),
                Address(0xCFB6834F84B9E726F5F8AEF446D585B732ABDD99): Account(
                    storage={0: 1}, code=bytes.fromhex("00"), nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=2),
                Address(0xD615C5EAFF84F487CFF253B50DC18517FC8385B0): Account(
                    storage={0: 1}, code=bytes.fromhex("00"), nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [6], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=2),
                Address(0x0D44B2AD06C5C9F9A86C9EDF8D13FB7D44FE756C): Account(
                    storage={0: 1}, code=bytes.fromhex("00"), nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [9], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=2),
                Address(0x858EC13538276B49D5ECE2A408C8331CCB79AD89): Account(
                    storage={0: 1}, code=bytes.fromhex("00"), nonce=1
                ),
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
                sender: Account(balance=0, nonce=2),
                Address(
                    0x95E88628C53B5C0E40FF6DE65A3CF8CDC3B477F7
                ): Account.NONEXISTENT,
                Address(
                    0x66E1CC2616A273450621C8CC5E91D8CFD92494FA
                ): Account.NONEXISTENT,
                Address(
                    0x6175BA9976476425B1CDA8E1DA479768FB429542
                ): Account.NONEXISTENT,
                Address(
                    0x8DFF0E448F1E078E9B8A7FCF0BF6C291F167AAEF
                ): Account.NONEXISTENT,
                Address(
                    0xA2C4270800A5DBEEA48464E5F2420EFB1747725A
                ): Account.NONEXISTENT,
                Address(
                    0x4D80F1150EE236ADFAAB47C70DF90E757CEF1141
                ): Account.NONEXISTENT,
                Address(
                    0x0566DC8DABC80FAD3ED9AB2B4309EBFD98894F44
                ): Account.NONEXISTENT,
                Address(
                    0x55305CC46BDAF1E755A05A771D55CFEC3FEDEF90
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [12], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=2),
                Address(0xD83E541AA11C5AE1E9C847AA1728D5BC47D32FAF): Account(
                    storage={0: 1}, code=bytes.fromhex("00"), nonce=1
                ),
                contract_26: Account(balance=0, nonce=1),
            },
        },
        {
            "indexes": {"data": [13, 14], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(balance=0, nonce=2),
                Address(
                    0x8F6E6C741AC95C1A9109850EA1A3FFC722DC3BF8
                ): Account.NONEXISTENT,
                Address(
                    0x1F5D187BB3A48DBB2C011D0A6E731AC8131799AD
                ): Account.NONEXISTENT,
                contract_26: Account(
                    storage={1: 1}, code=bytes.fromhex("32ff"), nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [15], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=2),
                Address(0x2A2141ED764598D4C5A8B6E036987928D5EC6BEA): Account(
                    storage={0: 1}, code=bytes.fromhex("00"), nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [16, 17], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(balance=0, nonce=2),
                Address(
                    0x74B39291DFC237C0D42FD15457754778F51C6DE8
                ): Account.NONEXISTENT,
                Address(
                    0x3399C78929EAB89C673A8986FF7CA9CCC49DB454
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [18], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=2),
                Address(0xDEB7D920F2653A8EDDCFFCA0A77F56FCD788C00A): Account(
                    storage={0: 1}, code=bytes.fromhex("00"), nonce=2
                ),
                Address(0x8109D28DE74BFAC2F298EC019548B8C346E51310): Account(
                    storage={}, code=bytes.fromhex("00"), nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [19, 20], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(balance=0, nonce=2),
                Address(
                    0xF922B2F70110C83F8EC7DF512B41BAC5627E8E59
                ): Account.NONEXISTENT,
                Address(
                    0x2CA788D22E21134AB1909266ED3B6C352E2A07CB
                ): Account.NONEXISTENT,
                Address(
                    0x398426E736801FE712DF1EF078A3B6CA3C6F063B
                ): Account.NONEXISTENT,
                Address(
                    0xB520686759CED3BC9D8898E02EE41623032FF47F
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [21], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=2),
                Address(0x5A2664B55822AA3C6D9D90FEC18B4C87CDE07D04): Account(
                    storage={0: 1}, code=bytes.fromhex("00"), nonce=2
                ),
                Address(0x442ED1B502544D146E46B5D9849A476AEBD3B8DB): Account(
                    storage={}, code=bytes.fromhex("00"), nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [22, 23], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(balance=0, nonce=2),
                Address(
                    0xDD2C53BFCAF5C1D698A2B21C0908F15F7FBFD635
                ): Account.NONEXISTENT,
                Address(
                    0x2D556BDBCC37C7A021879A21ABE25D1850D4FD36
                ): Account.NONEXISTENT,
                Address(
                    0xA99DA4EA490335C986D52B0CC9E3F78B286AC5FC
                ): Account.NONEXISTENT,
                Address(
                    0xB4AB8AB0D363765586925E35C715E342E4AE3C63
                ): Account.NONEXISTENT,
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("693c6139") + Hash(contract_1, left_padding=True),
        Bytes("693c6139") + Hash(contract_2, left_padding=True),
        Bytes("693c6139") + Hash(contract_3, left_padding=True),
        Bytes("693c6139") + Hash(contract_4, left_padding=True),
        Bytes("693c6139") + Hash(contract_5, left_padding=True),
        Bytes("693c6139") + Hash(contract_6, left_padding=True),
        Bytes("693c6139") + Hash(contract_7, left_padding=True),
        Bytes("693c6139") + Hash(contract_8, left_padding=True),
        Bytes("693c6139") + Hash(contract_9, left_padding=True),
        Bytes("693c6139") + Hash(contract_10, left_padding=True),
        Bytes("693c6139") + Hash(contract_11, left_padding=True),
        Bytes("693c6139") + Hash(contract_12, left_padding=True),
        Bytes("693c6139") + Hash(contract_13, left_padding=True),
        Bytes("693c6139") + Hash(contract_14, left_padding=True),
        Bytes("693c6139") + Hash(contract_15, left_padding=True),
        Bytes("693c6139") + Hash(contract_16, left_padding=True),
        Bytes("693c6139") + Hash(contract_17, left_padding=True),
        Bytes("693c6139") + Hash(contract_18, left_padding=True),
        Bytes("693c6139") + Hash(contract_19, left_padding=True),
        Bytes("693c6139") + Hash(contract_20, left_padding=True),
        Bytes("693c6139") + Hash(contract_21, left_padding=True),
        Bytes("693c6139") + Hash(contract_22, left_padding=True),
        Bytes("693c6139") + Hash(contract_23, left_padding=True),
        Bytes("693c6139") + Hash(contract_24, left_padding=True),
    ]
    tx_gas = [400000]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
