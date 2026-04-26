"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
state_tests/stEIP1559/gasPriceDiffPlacesOsakaFiller.yml
"""

import pytest
from execution_testing import (
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP1559/gasPriceDiffPlacesOsakaFiller.yml"],
)
@pytest.mark.valid_from("Osaka")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="normal",
        ),
        pytest.param(
            1,
            0,
            0,
            id="normal",
        ),
        pytest.param(
            2,
            0,
            0,
            id="normal",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4",
        ),
        pytest.param(
            5,
            0,
            0,
            id="d5",
        ),
        pytest.param(
            6,
            0,
            0,
            id="d6",
        ),
        pytest.param(
            7,
            0,
            0,
            id="d7",
        ),
        pytest.param(
            8,
            0,
            0,
            id="d8",
        ),
        pytest.param(
            9,
            0,
            0,
            id="d9",
        ),
        pytest.param(
            10,
            0,
            0,
            id="d10",
        ),
        pytest.param(
            11,
            0,
            0,
            id="d11",
        ),
        pytest.param(
            12,
            0,
            0,
            id="d12",
        ),
        pytest.param(
            13,
            0,
            0,
            id="d13",
        ),
        pytest.param(
            14,
            0,
            0,
            id="d14",
        ),
        pytest.param(
            15,
            0,
            0,
            id="d15",
        ),
        pytest.param(
            16,
            0,
            0,
            id="d16",
        ),
        pytest.param(
            17,
            0,
            0,
            id="d17",
        ),
        pytest.param(
            18,
            0,
            0,
            id="d18",
        ),
        pytest.param(
            19,
            0,
            0,
            id="d19",
        ),
        pytest.param(
            20,
            0,
            0,
            id="d20",
        ),
        pytest.param(
            21,
            0,
            0,
            id="d21",
        ),
        pytest.param(
            22,
            0,
            0,
            id="d22",
        ),
        pytest.param(
            23,
            0,
            0,
            id="d23",
        ),
        pytest.param(
            24,
            0,
            0,
            id="d24",
        ),
        pytest.param(
            25,
            0,
            0,
            id="d25",
        ),
        pytest.param(
            26,
            0,
            0,
            id="d26",
        ),
        pytest.param(
            27,
            0,
            0,
            id="d27",
        ),
        pytest.param(
            28,
            0,
            0,
            id="d28",
        ),
        pytest.param(
            29,
            0,
            0,
            id="d29",
        ),
        pytest.param(
            30,
            0,
            0,
            id="d30",
        ),
        pytest.param(
            31,
            0,
            0,
            id="d31",
        ),
        pytest.param(
            32,
            0,
            0,
            id="d32",
        ),
        pytest.param(
            33,
            0,
            0,
            id="d33",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_gas_price_diff_places(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x000000000000000000000000000000000000C0DE)
    contract_1 = Address(0x000000000000000000000000000000000020C0DE)
    contract_2 = Address(0x00000000000000000000000000000000C0DEC0DE)
    contract_3 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
    contract_4 = Address(0x000000000000000000000000000000000000CA11)
    contract_5 = Address(0x00000000000000000000000000000000CA1100F1)
    contract_6 = Address(0x00000000000000000000000000000000CA1100F2)
    contract_7 = Address(0x00000000000000000000000000000000CA1100F4)
    contract_8 = Address(0x00000000000000000000000000000000CA1100FA)
    contract_9 = Address(0x0000000000000000000000000000000000060006)
    contract_10 = Address(0x000000000000000000000000000000000060BACC)
    contract_11 = Address(0x00000000000000000000000000000000DEADDEAD)
    contract_12 = Address(0x00000000000000000000000000000060BACCFA57)
    sender = pre.fund_eoa(amount=0x3635C9ADC5DEA00000, nonce=1)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4503599627370496,
    )

    # Source: yul
    # berlin {
    #    mstore(0, gasprice())
    #
    #
    #
    #    // Here the result is is mload(0). We want to run it, but
    #    // prefix it with a zero so we'll be safe from being considered
    #    // an invalid program.
    #    //
    #    // If we use this as a constructor the result will be
    #    // the code of the created contract, but we can live
    #    // with that. We won't call it.
    #    mstore(0x40, mload(0x00))
    #    return(0x3F, 0x21)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GASPRICE)
        + Op.MSTORE(offset=0x40, value=Op.MLOAD(offset=0x0))
        + Op.RETURN(offset=0x3F, size=0x21),
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x000000000000000000000000000000000000C0DE),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    mstore(0, gasprice())
    #
    #
    #
    #    // Here the result is is mload(0).
    #    return(0x00, 0x20)
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GASPRICE)
        + Op.RETURN(offset=0x0, size=0x20),
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x000000000000000000000000000000000020C0DE),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #   mstore(0, gasprice())
    #
    #
    #   return(0, 0x20)     // return the result as our return value
    # }
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GASPRICE)
        + Op.RETURN(offset=0x0, size=0x20),
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x000000000000000000000000000000000000CA11),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    mstore(0, gasprice())
    #
    #
    #    sstore(0,mload(0))
    #    invalid()
    # }
    contract_9 = pre.deploy_contract(  # noqa: F841
        code=Op.GASPRICE
        + Op.PUSH1[0x0]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
        + Op.SSTORE
        + Op.INVALID,
        storage={0: 24743},
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000060006),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    mstore(0, gasprice())
    #
    #
    #    sstore(0,mload(0))
    #    revert(0,0x20)
    # }
    contract_10 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GASPRICE)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.REVERT(offset=0x0, size=0x20),
        storage={0: 24743},
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x000000000000000000000000000000000060BACC),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    selfdestruct(0)
    # }
    contract_11 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=0x0),
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x00000000000000000000000000000000DEADDEAD),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    let addr := 0x20C0DE
    #    let length := extcodesize(addr)
    #
    #    // Read the code from 0x20C0DE
    #    extcodecopy(addr, 0, 0, length)
    #
    #    // Return this memory as the code for the contract
    #    return(0, length)
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.PUSH3[0x20C0DE]
        + Op.DUP2
        + Op.EXTCODESIZE(address=Op.DUP2)
        + Op.SWAP3
        + Op.DUP4
        + Op.SWAP3
        + Op.EXTCODECOPY
        + Op.PUSH1[0x0]
        + Op.RETURN,
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x00000000000000000000000000000000C0DEC0DE),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #   if iszero(callcode(gas(), 0xca11, 0, 0, 0, 0, 0x20))
    #      { revert(0,0x20) }
    #
    #   return(0, 0x20)     // return the result as our return value
    # }
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0x15,
            condition=Op.ISZERO(
                Op.CALLCODE(
                    gas=Op.GAS,
                    address=0xCA11,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=0x0,
                    ret_size=0x20,
                )
            ),
        )
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.REVERT(offset=0x0, size=0x20),
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x00000000000000000000000000000000CA1100F2),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #   if iszero(call(gas(), 0xca11, 0, 0, 0, 0, 0x20))
    #      { revert(0,0x20) }
    #
    #   return(0, 0x20)     // return the result as our return value
    # }
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0x15,
            condition=Op.ISZERO(
                Op.CALL(
                    gas=Op.GAS,
                    address=0xCA11,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=0x0,
                    ret_size=0x20,
                )
            ),
        )
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.REVERT(offset=0x0, size=0x20),
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x00000000000000000000000000000000CA1100F1),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #   if iszero(staticcall(gas(), 0xca11, 0, 0, 0, 0x20))
    #      { revert(0,0x20) }
    #
    #   return(0, 0x20)     // return the result as our return value
    # }
    contract_8 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0x14,
            condition=Op.ISZERO(
                Op.STATICCALL(
                    gas=Op.GAS,
                    address=0xCA11,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=0x0,
                    ret_size=0x20,
                )
            ),
        )
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.REVERT(offset=0x0, size=0x20),
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x00000000000000000000000000000000CA1100FA),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #   if iszero(delegatecall(gas(), 0xca11, 0, 0, 0, 0x20))
    #      { revert(0,0x20) }
    #
    #   return(0, 0x20)     // return the result as our return value
    # }
    contract_7 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0x14,
            condition=Op.ISZERO(
                Op.DELEGATECALL(
                    gas=Op.GAS,
                    address=0xCA11,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=0x0,
                    ret_size=0x20,
                )
            ),
        )
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.REVERT(offset=0x0, size=0x20),
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x00000000000000000000000000000000CA1100F4),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    let action := calldataload(4)
    #    let res := 1   // If the result of a call is revert, revert here too
    #    let addr := 1  // If the result of CREATE[2] is zero, it reverted
    #
    #    // For when we need code in our memory
    #    let codeBuffer := 0x20
    #    // When running the template in the constructor
    #    let codeLength := extcodesize(0xC0DE)
    #    // When running the template in the created code
    #    let codeLength2 := extcodesize(0xC0DEC0DE)
    #
    #    // Goat should be overwritten
    #    mstore(0, 0x60A7)
    #
    #    switch action
    #    case 0 {  // run the code snippet as normal code
    #       mstore(0, gasprice())
    #
    #
    #    }
    #
    #    // One level of call stack
    #    case 0xF1 {  // call a contract to run this code
    #       res := call(gas(), 0xca11, 0, 0, 0, 0, 0x20) // call template code
    #    }
    #    case 0xF2 {  // callcode a contract to run this code
    #       res := callcode(gas(), 0xca11, 0, 0, 0, 0, 0x20)
    #    }
    #    case 0xF4 {  // delegate call a contract to run this code
    # ... (269 more lines)
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x60A7)
        + Op.PUSH1[0x1]
        + Op.DUP1
        + Op.CALLDATALOAD(offset=0x4)
        + Op.EXTCODESIZE(address=0xC0DEC0DE)
        + Op.PUSH1[0x20]
        + Op.EXTCODESIZE(address=0xC0DE)
        + Op.JUMPI(pc=0x581, condition=Op.ISZERO(Op.DUP4))
        + Op.JUMPI(pc=0x56B, condition=Op.EQ(0xF1, Op.DUP4))
        + Op.JUMPI(pc=0x555, condition=Op.EQ(0xF2, Op.DUP4))
        + Op.JUMPI(pc=0x540, condition=Op.EQ(0xF4, Op.DUP4))
        + Op.JUMPI(pc=0x52B, condition=Op.EQ(0xFA, Op.DUP4))
        + Op.JUMPI(pc=0x513, condition=Op.EQ(0xF1F1, Op.DUP4))
        + Op.JUMPI(pc=0x4FB, condition=Op.EQ(0xF2F1, Op.DUP4))
        + Op.JUMPI(pc=0x4E4, condition=Op.EQ(0xF4F1, Op.DUP4))
        + Op.JUMPI(pc=0x4CD, condition=Op.EQ(0xFAF1, Op.DUP4))
        + Op.JUMPI(pc=0x4B5, condition=Op.EQ(0xF1F2, Op.DUP4))
        + Op.JUMPI(pc=0x49D, condition=Op.EQ(0xF2F2, Op.DUP4))
        + Op.JUMPI(pc=0x486, condition=Op.EQ(0xF4F2, Op.DUP4))
        + Op.JUMPI(pc=0x46F, condition=Op.EQ(0xFAF2, Op.DUP4))
        + Op.JUMPI(pc=0x457, condition=Op.EQ(0xF1F4, Op.DUP4))
        + Op.JUMPI(pc=0x43F, condition=Op.EQ(0xF2F4, Op.DUP4))
        + Op.JUMPI(pc=0x428, condition=Op.EQ(0xF4F4, Op.DUP4))
        + Op.JUMPI(pc=0x411, condition=Op.EQ(0xFAF4, Op.DUP4))
        + Op.JUMPI(pc=0x3F9, condition=Op.EQ(0xF1FA, Op.DUP4))
        + Op.JUMPI(pc=0x3E1, condition=Op.EQ(0xF2FA, Op.DUP4))
        + Op.JUMPI(pc=0x3CA, condition=Op.EQ(0xF4FA, Op.DUP4))
        + Op.JUMPI(pc=0x3B3, condition=Op.EQ(0xFAFA, Op.DUP4))
        + Op.JUMPI(pc=0x37E, condition=Op.EQ(0xFD, Op.DUP4))
        + Op.JUMPI(pc=0x347, condition=Op.EQ(0xFE, Op.DUP4))
        + Op.JUMPI(pc=0x311, condition=Op.EQ(0xFF, Op.DUP4))
        + Op.JUMPI(pc=0x2EB, condition=Op.EQ(0xF0, Op.DUP4))
        + Op.JUMPI(pc=0x2C1, condition=Op.EQ(0xF5, Op.DUP4))
        + Op.POP
        + Op.JUMPI(pc=0x297, condition=Op.EQ(0xF0F1, Op.DUP3))
        + Op.JUMPI(pc=0x26B, condition=Op.EQ(0xF5F1, Op.DUP3))
        + Op.JUMPI(pc=0x248, condition=Op.EQ(0xF0F2, Op.DUP3))
        + Op.JUMPI(pc=0x223, condition=Op.EQ(0xF5F2, Op.DUP3))
        + Op.JUMPI(pc=0x201, condition=Op.EQ(0xF0F4, Op.DUP3))
        + Op.JUMPI(pc=0x1DD, condition=Op.EQ(0xF5F4, Op.DUP3))
        + Op.JUMPI(pc=0x1B4, condition=Op.EQ(0xF0FA, Op.DUP3))
        + Op.JUMPI(pc=0x189, condition=Op.EQ(0xF5FA, Op.DUP3))
        + Op.POP * 2
        + Op.PUSH5[0x60BACCFA57]
        + Op.JUMPI(pc=0x16E, condition=Op.EQ)
        + Op.MSTORE(offset=0x0, value=0xBAD0BAD0BAD0)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x168, condition=Op.ISZERO) * 2
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP
        + Op.JUMPDEST
        + Op.REVERT(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.POP
        + Op.MSTORE(offset=0x0, value=0x3FF)
        + Op.CALL(
            gas=Op.GAS,
            address=0x60BACCFA57,
            value=Op.DUP1,
            args_offset=Op.DUP2,
            args_size=Op.DUP2,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.SWAP2
        + Op.POP
        + Op.PUSH2[0x5A17]
        + Op.SWAP4
        + Op.POP
        + Op.DUP1
        + Op.SWAP3
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.DUP3
        + Op.PUSH4[0xC0DEC0DE]
        + Op.EXTCODECOPY
        + Op.PUSH8[0xDE0B6B3A7640000]
        + Op.CREATE2
        + Op.STATICCALL(
            gas=Op.GAS,
            address=Op.DUP5,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.DUP2
        + Op.SWAP5
        + Op.POP
        + Op.DUP1
        + Op.SWAP4
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.SWAP2
        + Op.SWAP3
        + Op.POP
        + Op.PUSH4[0xC0DEC0DE]
        + Op.EXTCODECOPY
        + Op.PUSH8[0xDE0B6B3A7640000]
        + Op.CREATE
        + Op.STATICCALL(
            gas=Op.GAS,
            address=Op.DUP5,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.SWAP2
        + Op.POP
        + Op.PUSH2[0x5A17]
        + Op.SWAP4
        + Op.POP
        + Op.DUP1
        + Op.SWAP3
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.DUP3
        + Op.PUSH4[0xC0DEC0DE]
        + Op.EXTCODECOPY
        + Op.PUSH1[0x0]
        + Op.CREATE2
        + Op.DELEGATECALL(
            gas=Op.GAS,
            address=Op.DUP5,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.DUP2
        + Op.SWAP5
        + Op.POP
        + Op.DUP1
        + Op.SWAP4
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.SWAP2
        + Op.SWAP3
        + Op.POP
        + Op.PUSH4[0xC0DEC0DE]
        + Op.EXTCODECOPY
        + Op.PUSH1[0x0]
        + Op.CREATE
        + Op.DELEGATECALL(
            gas=Op.GAS,
            address=Op.DUP5,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.SWAP2
        + Op.POP
        + Op.PUSH2[0x5A17]
        + Op.SWAP4
        + Op.POP
        + Op.DUP1
        + Op.SWAP3
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.DUP3
        + Op.PUSH4[0xC0DEC0DE]
        + Op.EXTCODECOPY
        + Op.PUSH1[0x0]
        + Op.CREATE2
        + Op.CALLCODE(
            gas=Op.GAS,
            address=Op.DUP6,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.DUP2
        + Op.SWAP5
        + Op.POP
        + Op.DUP1
        + Op.SWAP4
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.SWAP2
        + Op.SWAP3
        + Op.POP
        + Op.PUSH4[0xC0DEC0DE]
        + Op.EXTCODECOPY
        + Op.PUSH1[0x0]
        + Op.CREATE
        + Op.CALLCODE(
            gas=Op.GAS,
            address=Op.DUP6,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.SWAP2
        + Op.POP
        + Op.PUSH2[0x5A17]
        + Op.SWAP4
        + Op.POP
        + Op.DUP1
        + Op.SWAP3
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.DUP3
        + Op.PUSH4[0xC0DEC0DE]
        + Op.EXTCODECOPY
        + Op.PUSH8[0xDE0B6B3A7640000]
        + Op.CREATE2
        + Op.CALL(
            gas=Op.GAS,
            address=Op.DUP6,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.DUP2
        + Op.SWAP5
        + Op.POP
        + Op.DUP1
        + Op.SWAP4
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.SWAP2
        + Op.SWAP3
        + Op.POP
        + Op.PUSH4[0xC0DEC0DE]
        + Op.EXTCODECOPY
        + Op.PUSH8[0xDE0B6B3A7640000]
        + Op.CREATE
        + Op.CALL(
            gas=Op.GAS,
            address=Op.DUP6,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.SWAP3
        + Op.POP
        + Op.SWAP1
        + Op.POP
        + Op.PUSH2[0x5A17]
        + Op.SWAP3
        + Op.SWAP4
        + Op.POP
        + Op.EXTCODECOPY(
            address=0xC0DE, dest_offset=Op.DUP3, offset=0x0, size=Op.DUP2
        )
        + Op.PUSH8[0xDE0B6B3A7640000]
        + Op.CREATE2
        + Op.SWAP1
        + Op.EXTCODECOPY(
            address=Op.DUP5, dest_offset=0x0, offset=0x1, size=0x20
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.SWAP4
        + Op.SWAP5
        + Op.POP
        + Op.SWAP2
        + Op.POP * 2
        + Op.EXTCODECOPY(
            address=0xC0DE, dest_offset=Op.DUP3, offset=0x0, size=Op.DUP2
        )
        + Op.PUSH8[0xDE0B6B3A7640000]
        + Op.CREATE
        + Op.SWAP1
        + Op.EXTCODECOPY(
            address=Op.DUP5, dest_offset=0x0, offset=0x1, size=0x20
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 4
        + Op.MSTORE(offset=0x0, value=Op.GASPRICE)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xDEADDEAD,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.GASPRICE
        + Op.PUSH1[0x0]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
        + Op.SLOAD
        + Op.JUMPI(pc=0x156, condition=Op.EQ)
        + Op.MSTORE(offset=0x0, value=0xBADBADBAD)
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 4
        + Op.MSTORE(offset=0x0, value=Op.GASPRICE)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.POP(
            Op.CALL(
                gas=0x61A8,
                address=0x60006,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.GASPRICE
        + Op.PUSH1[0x0]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
        + Op.SLOAD
        + Op.JUMPI(pc=0x156, condition=Op.EQ)
        + Op.MSTORE(offset=0x0, value=0xBADBADBAD)
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 4
        + Op.MSTORE(offset=0x0, value=Op.GASPRICE)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0x60BACC,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.GASPRICE
        + Op.PUSH1[0x0]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
        + Op.SLOAD
        + Op.JUMPI(pc=0x156, condition=Op.EQ)
        + Op.MSTORE(offset=0x0, value=0xBADBADBAD)
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.STATICCALL(
            gas=Op.GAS,
            address=0xCA1100FA,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.DELEGATECALL(
            gas=Op.GAS,
            address=0xCA1100FA,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.CALLCODE(
            gas=Op.GAS,
            address=0xCA1100FA,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.CALL(
            gas=Op.GAS,
            address=0xCA1100FA,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.STATICCALL(
            gas=Op.GAS,
            address=0xCA1100F4,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.DELEGATECALL(
            gas=Op.GAS,
            address=0xCA1100F4,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.CALLCODE(
            gas=Op.GAS,
            address=0xCA1100F4,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.CALL(
            gas=Op.GAS,
            address=0xCA1100F4,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.STATICCALL(
            gas=Op.GAS,
            address=0xCA1100F2,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.DELEGATECALL(
            gas=Op.GAS,
            address=0xCA1100F2,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.CALLCODE(
            gas=Op.GAS,
            address=0xCA1100F2,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.CALL(
            gas=Op.GAS,
            address=0xCA1100F2,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.STATICCALL(
            gas=Op.GAS,
            address=0xCA1100F1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.DELEGATECALL(
            gas=Op.GAS,
            address=0xCA1100F1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.CALLCODE(
            gas=Op.GAS,
            address=0xCA1100F1,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.CALL(
            gas=Op.GAS,
            address=0xCA1100F1,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.STATICCALL(
            gas=Op.GAS,
            address=0xCA11,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.DELEGATECALL(
            gas=Op.GAS,
            address=0xCA11,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.CALLCODE(
            gas=Op.GAS,
            address=0xCA11,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 5
        + Op.CALL(
            gas=Op.GAS,
            address=0xCA11,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=0x0,
            ret_size=0x20,
        )
        + Op.JUMP(pc=0x156)
        + Op.JUMPDEST
        + Op.POP * 4
        + Op.MSTORE(offset=0x0, value=Op.GASPRICE)
        + Op.JUMP(pc=0x156),
        storage={0: 24743},
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #    let depth := calldataload(0)
    #
    #    if eq(depth,0) {
    #        mstore(0, gasprice())
    #
    #
    #        return(0, 0x20)
    #    }
    #
    #    // Dig deeper
    #    mstore(0, sub(depth,1))
    #
    #    // Call yourself with depth-1
    #    if iszero(call(gas(), 0x60BACCFA57, 0, 0, 0x20, 0, 0x20)) {
    #       // Propagate failure if we failed
    #       revert(0, 0x20)
    #    }
    #
    #    // Propagate success
    #    return (0, 0x20)
    # }
    contract_12 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x0)
        + Op.JUMPI(pc=0x2D, condition=Op.ISZERO(Op.DUP1))
        + Op.PUSH1[0x1]
        + Op.SWAP1
        + Op.MSTORE(offset=0x0, value=Op.SUB)
        + Op.JUMPI(
            pc=0x27,
            condition=Op.ISZERO(
                Op.CALL(
                    gas=Op.GAS,
                    address=0x60BACCFA57,
                    value=Op.DUP1,
                    args_offset=Op.DUP2,
                    args_size=Op.DUP2,
                    ret_offset=0x0,
                    ret_size=0x20,
                )
            ),
        )
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.REVERT(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.GASPRICE)
        + Op.RETURN(offset=0x0, size=0x20),
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x00000000000000000000000000000060BACCFA57),  # noqa: E501
    )

    tx_data = [
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0xF1),
        Bytes("693c6139") + Hash(0xF2),
        Bytes("693c6139") + Hash(0xF4),
        Bytes("693c6139") + Hash(0xFA),
        Bytes("693c6139") + Hash(0xF1F1),
        Bytes("693c6139") + Hash(0xF2F1),
        Bytes("693c6139") + Hash(0xF4F1),
        Bytes("693c6139") + Hash(0xFAF1),
        Bytes("693c6139") + Hash(0xF1F2),
        Bytes("693c6139") + Hash(0xF2F2),
        Bytes("693c6139") + Hash(0xF4F2),
        Bytes("693c6139") + Hash(0xFAF2),
        Bytes("693c6139") + Hash(0xF1F4),
        Bytes("693c6139") + Hash(0xF2F4),
        Bytes("693c6139") + Hash(0xF4F4),
        Bytes("693c6139") + Hash(0xFAF4),
        Bytes("693c6139") + Hash(0xF1FA),
        Bytes("693c6139") + Hash(0xF2FA),
        Bytes("693c6139") + Hash(0xF4FA),
        Bytes("693c6139") + Hash(0xFAFA),
        Bytes("693c6139") + Hash(0xFD),
        Bytes("693c6139") + Hash(0xFE),
        Bytes("693c6139") + Hash(0xFF),
        Bytes("693c6139") + Hash(0xF0),
        Bytes("693c6139") + Hash(0xF5),
        Bytes("693c6139") + Hash(0xF0F1),
        Bytes("693c6139") + Hash(0xF5F1),
        Bytes("693c6139") + Hash(0xF0F2),
        Bytes("693c6139") + Hash(0xF5F2),
        Bytes("693c6139") + Hash(0xF0F4),
        Bytes("693c6139") + Hash(0xF5F4),
        Bytes("693c6139") + Hash(0xF0FA),
        Bytes("693c6139") + Hash(0xF5FA),
    ]
    tx_gas = [1000000]

    tx = Transaction(
        sender=sender,
        to=contract_3,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        gas_price=2000,
    )

    post = {
        contract_3: Account(storage={0: 2000}),
        contract_10: Account(storage={0: 24743}),
        contract_9: Account(storage={0: 24743}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
