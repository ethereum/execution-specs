"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP1559/baseFeeDiffPlacesFiller.yml
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
    "693c613900000000000000000000000000000000000000000000000000000000000000f1",
    "",
    "",
    "693c613900000000000000000000000000000000000000000000000000000000000000f4",
    "693c613900000000000000000000000000000000000000000000000000000000000000fa",
    "693c6139000000000000000000000000000000000000000000000000000000000000f1f1",
    "693c6139000000000000000000000000000000000000000000000000000000000000f2f1",
    "693c6139000000000000000000000000000000000000000000000000000000000000f4f1",
    "693c6139000000000000000000000000000000000000000000000000000000000000faf1",
    "693c6139000000000000000000000000000000000000000000000000000000000000f1f2",
    "693c6139000000000000000000000000000000000000000000000000000000000000f2f2",
    "693c6139000000000000000000000000000000000000000000000000000000000000f4f2",
    "693c6139000000000000000000000000000000000000000000000000000000000000faf2",
    "693c6139000000000000000000000000000000000000000000000000000000000000f1f4",
    "693c6139000000000000000000000000000000000000000000000000000000000000f2f4",
    "693c6139000000000000000000000000000000000000000000000000000000000000f4f4",
    "693c6139000000000000000000000000000000000000000000000000000000000000faf4",
    "693c6139000000000000000000000000000000000000000000000000000000000000f1fa",
    "693c6139000000000000000000000000000000000000000000000000000000000000f2fa",
    "693c6139000000000000000000000000000000000000000000000000000000000000f4fa",
    "693c6139000000000000000000000000000000000000000000000000000000000000fafa",
    "693c613900000000000000000000000000000000000000000000000000000000000000fd",
    "693c613900000000000000000000000000000000000000000000000000000000000000fe",
    "693c613900000000000000000000000000000000000000000000000000000000000000ff",
    "693c613900000000000000000000000000000000000000000000000000000000000000f0",
    "693c613900000000000000000000000000000000000000000000000000000000000000f5",
    "693c6139000000000000000000000000000000000000000000000000000000000000f0f1",
    "693c6139000000000000000000000000000000000000000000000000000000000000f5f1",
    "693c6139000000000000000000000000000000000000000000000000000000000000f0f2",
    "693c6139000000000000000000000000000000000000000000000000000000000000f5f2",
    "693c6139000000000000000000000000000000000000000000000000000000000000f0f4",
    "693c6139000000000000000000000000000000000000000000000000000000000000f5f4",
    "693c6139000000000000000000000000000000000000000000000000000000000000f0fa",
    "693c6139000000000000000000000000000000000000000000000000000000000000f5fa",
    "693c613900000000000000000000000000000000000000000000000000000060baccfa57",
]

TX_GAS = [4503599627370496]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP1559/baseFeeDiffPlacesFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(10, 0, 0, id="case0"),
        pytest.param(11, 0, 0, id="case1"),
        pytest.param(12, 0, 0, id="case2"),
        pytest.param(13, 0, 0, id="case3"),
        pytest.param(14, 0, 0, id="case4"),
        pytest.param(15, 0, 0, id="case5"),
        pytest.param(16, 0, 0, id="case6"),
        pytest.param(17, 0, 0, id="case7"),
        pytest.param(18, 0, 0, id="case8"),
        pytest.param(19, 0, 0, id="case9"),
        pytest.param(20, 0, 0, id="case10"),
        pytest.param(21, 0, 0, id="case11"),
        pytest.param(22, 0, 0, id="case12"),
        pytest.param(23, 0, 0, id="case13"),
        pytest.param(24, 0, 0, id="case14"),
        pytest.param(25, 0, 0, id="case15"),
        pytest.param(26, 0, 0, id="case16"),
        pytest.param(27, 0, 0, id="case17"),
        pytest.param(28, 0, 0, id="case18"),
        pytest.param(29, 0, 0, id="case19"),
        pytest.param(30, 0, 0, id="case20"),
        pytest.param(31, 0, 0, id="case21"),
        pytest.param(32, 0, 0, id="case22"),
        pytest.param(33, 0, 0, id="case23"),
        pytest.param(34, 0, 0, id="case24"),
        pytest.param(3, 0, 0, id="case25"),
        pytest.param(4, 0, 0, id="case26"),
        pytest.param(5, 0, 0, id="case27"),
        pytest.param(6, 0, 0, id="case28"),
        pytest.param(7, 0, 0, id="case29"),
        pytest.param(8, 0, 0, id="case30"),
        pytest.param(9, 0, 0, id="case31"),
        pytest.param(0, 0, 0, id="case32"),
        pytest.param(0, 0, 0, id="case33"),
        pytest.param(0, 0, 0, id="case34"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_base_fee_diff_places(
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
        gas_limit=4503599627370496,
    )

    # Source: Yul
    # {
    #    // basefee is still not supported in Yul 0.8.5
    #
    #
    #     mstore(0, verbatim_0i_1o(hex"48"))
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
    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.MSTORE(offset=0x40, value=Op.MLOAD(offset=0x0))
            + Op.RETURN(offset=0x3F, size=0x21)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x000000000000000000000000000000000000c0de"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   // basefee is still not supported in Yul 0.8.5
    #
    #
    #   mstore(0, verbatim_0i_1o(hex"48"))
    #
    #
    #   return(0, 0x20)     // return the result as our return value
    # }
    callee_1 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.RETURN(offset=0x0, size=0x20)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x000000000000000000000000000000000000ca11"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.INVALID
        ),
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        address=Address("0x0000000000000000000000000000000000060006"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    // basefee is still not supported in Yul 0.8.5
    #
    #
    #     mstore(0, verbatim_0i_1o(hex"48"))
    #
    #
    #
    #    // Here the result is is mload(0).
    #    return(0x00, 0x20)
    # }
    callee_3 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.RETURN(offset=0x0, size=0x20)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x000000000000000000000000000000000020c0de"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    // basefee is still not supported in Yul 0.8.5
    #
    #
    #     mstore(0, verbatim_0i_1o(hex"48"))
    #
    #
    #    sstore(0,mload(0))
    #    revert(0,0x20)
    # }
    callee_4 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.REVERT(offset=0x0, size=0x20)
        ),
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        address=Address("0x000000000000000000000000000000000060bacc"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    let addr := 0x20C0DE
    #    let length := extcodesize(addr)
    #
    #    // Read the code from 0x20C0DE
    #    extcodecopy(addr, 0, 0, length)
    #
    #    // Return this memory as the code for the contract
    #    return(0, length)
    # }
    callee_5 = pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH3[0x20C0DE]
            + Op.DUP2
            + Op.EXTCODESIZE(address=Op.DUP2)
            + Op.SWAP3
            + Op.DUP4
            + Op.SWAP3
            + Op.EXTCODECOPY
            + Op.PUSH1[0x0]
            + Op.RETURN
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x00000000000000000000000000000000c0dec0de"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   if iszero(call(gas(), 0xca11, 0, 0, 0, 0, 0x20))
    #      { revert(0,0x20) }
    #
    #   return(0, 0x20)     // return the result as our return value
    # }
    callee_6 = pre.deploy_contract(
        code=(
            Op.JUMPI(
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
                    ),
                ),
            )
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.REVERT(offset=0x0, size=0x20)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x00000000000000000000000000000000ca1100f1"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   if iszero(callcode(gas(), 0xca11, 0, 0, 0, 0, 0x20))
    #      { revert(0,0x20) }
    #
    #   return(0, 0x20)     // return the result as our return value
    # }
    callee_7 = pre.deploy_contract(
        code=(
            Op.JUMPI(
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
                    ),
                ),
            )
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.REVERT(offset=0x0, size=0x20)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x00000000000000000000000000000000ca1100f2"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   if iszero(delegatecall(gas(), 0xca11, 0, 0, 0, 0x20))
    #      { revert(0,0x20) }
    #
    #   return(0, 0x20)     // return the result as our return value
    # }
    callee_8 = pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x14,
                condition=Op.ISZERO(
                    Op.DELEGATECALL(
                        gas=Op.GAS,
                        address=0xCA11,
                        args_offset=Op.DUP1,
                        args_size=Op.DUP1,
                        ret_offset=0x0,
                        ret_size=0x20,
                    ),
                ),
            )
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.REVERT(offset=0x0, size=0x20)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x00000000000000000000000000000000ca1100f4"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   if iszero(staticcall(gas(), 0xca11, 0, 0, 0, 0x20))
    #      { revert(0,0x20) }
    #
    #   return(0, 0x20)     // return the result as our return value
    # }
    callee_9 = pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x14,
                condition=Op.ISZERO(
                    Op.STATICCALL(
                        gas=Op.GAS,
                        address=0xCA11,
                        args_offset=Op.DUP1,
                        args_size=Op.DUP1,
                        ret_offset=0x0,
                        ret_size=0x20,
                    ),
                ),
            )
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.REVERT(offset=0x0, size=0x20)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x00000000000000000000000000000000ca1100fa"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    selfdestruct(0)
    # }
    callee_10 = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0x0),
        balance=0xDE0B6B3A7640000,
        address=Address("0x00000000000000000000000000000000deaddead"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    let depth := calldataload(0)
    #
    #    if eq(depth,0) {
    #        // basefee is still not supported in Yul 0.8.5
    #
    #
    #     mstore(0, verbatim_0i_1o(hex"48"))
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
    callee_11 = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x0)
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
                    ),
                ),
            )
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.REVERT(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.RETURN(offset=0x0, size=0x20)
        ),
        balance=0xDE0B6B3A7640000,
        address=Address("0x00000000000000000000000000000060baccfa57"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635C9ADC5DEA00000, nonce=1)
    # Source: Yul
    # {
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
    #       // basefee is still not supported in Yul 0.8.5
    #
    #
    #   mstore(0, verbatim_0i_1o(hex"48"))
    #
    #
    #    }
    #
    #    // One level of call stack
    #    case 0xF1 {  // call a contract to run this code
    #       res := call(gas(), 0xca11, 0, 0, 0, 0, 0x20) // call template code
    #    }
    #    case 0xF2 {  // callcode a contract to run this code
    # ... (290 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x60A7)
            + Op.PUSH1[0x1]
            + Op.DUP1
            + Op.CALLDATALOAD(offset=0x4)
            + Op.EXTCODESIZE(address=0xC0DEC0DE)
            + Op.PUSH1[0x20]
            + Op.EXTCODESIZE(address=0xC0DE)
            + Op.JUMPI(pc=0x58A, condition=Op.ISZERO(Op.DUP4))
            + Op.JUMPI(pc=0x574, condition=Op.EQ(0xF1, Op.DUP4))
            + Op.JUMPI(pc=0x55E, condition=Op.EQ(0xF2, Op.DUP4))
            + Op.JUMPI(pc=0x549, condition=Op.EQ(0xF4, Op.DUP4))
            + Op.JUMPI(pc=0x534, condition=Op.EQ(0xFA, Op.DUP4))
            + Op.JUMPI(pc=0x51C, condition=Op.EQ(0xF1F1, Op.DUP4))
            + Op.JUMPI(pc=0x504, condition=Op.EQ(0xF2F1, Op.DUP4))
            + Op.JUMPI(pc=0x4ED, condition=Op.EQ(0xF4F1, Op.DUP4))
            + Op.JUMPI(pc=0x4D6, condition=Op.EQ(0xFAF1, Op.DUP4))
            + Op.JUMPI(pc=0x4BE, condition=Op.EQ(0xF1F2, Op.DUP4))
            + Op.JUMPI(pc=0x4A6, condition=Op.EQ(0xF2F2, Op.DUP4))
            + Op.JUMPI(pc=0x48F, condition=Op.EQ(0xF4F2, Op.DUP4))
            + Op.JUMPI(pc=0x478, condition=Op.EQ(0xFAF2, Op.DUP4))
            + Op.JUMPI(pc=0x460, condition=Op.EQ(0xF1F4, Op.DUP4))
            + Op.JUMPI(pc=0x448, condition=Op.EQ(0xF2F4, Op.DUP4))
            + Op.JUMPI(pc=0x431, condition=Op.EQ(0xF4F4, Op.DUP4))
            + Op.JUMPI(pc=0x41A, condition=Op.EQ(0xFAF4, Op.DUP4))
            + Op.JUMPI(pc=0x402, condition=Op.EQ(0xF1FA, Op.DUP4))
            + Op.JUMPI(pc=0x3EA, condition=Op.EQ(0xF2FA, Op.DUP4))
            + Op.JUMPI(pc=0x3D3, condition=Op.EQ(0xF4FA, Op.DUP4))
            + Op.JUMPI(pc=0x3BC, condition=Op.EQ(0xFAFA, Op.DUP4))
            + Op.JUMPI(pc=0x384, condition=Op.EQ(0xFD, Op.DUP4))
            + Op.JUMPI(pc=0x34A, condition=Op.EQ(0xFE, Op.DUP4))
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
            + Op.POP
            + Op.POP
            + Op.PUSH5[0x60BACCFA57]
            + Op.JUMPI(pc=0x16E, condition=Op.EQ)
            + Op.MSTORE(offset=0x0, value=0xBAD0BAD0BAD0)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x168, condition=Op.ISZERO)
            + Op.JUMPI(pc=0x168, condition=Op.ISZERO)
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
                address=0xC0DE,
                dest_offset=Op.DUP3,
                offset=0x0,
                size=Op.DUP2,
            )
            + Op.PUSH8[0xDE0B6B3A7640000]
            + Op.CREATE2
            + Op.SWAP1
            + Op.EXTCODECOPY(
                address=Op.DUP5,
                dest_offset=0x0,
                offset=0x1,
                size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.SWAP4
            + Op.SWAP5
            + Op.POP
            + Op.SWAP2
            + Op.POP
            + Op.POP
            + Op.EXTCODECOPY(
                address=0xC0DE,
                dest_offset=Op.DUP3,
                offset=0x0,
                size=Op.DUP2,
            )
            + Op.PUSH8[0xDE0B6B3A7640000]
            + Op.CREATE
            + Op.SWAP1
            + Op.EXTCODECOPY(
                address=Op.DUP5,
                dest_offset=0x0,
                offset=0x1,
                size=0x20,
            )
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x0, value=Op.BASEFEE)
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
                ),
            )
            + Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.JUMPI(
                pc=0x156,
                condition=Op.EQ(Op.SLOAD(key=0x0), Op.MLOAD(offset=0x0)),
            )
            + Op.MSTORE(offset=0x0, value=0xBADBADBAD)
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x0, value=Op.BASEFEE)
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
                ),
            )
            + Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.JUMPI(
                pc=0x156,
                condition=Op.EQ(Op.SLOAD(key=0x0), Op.MLOAD(offset=0x0)),
            )
            + Op.MSTORE(offset=0x0, value=0xBADBADBAD)
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x0, value=Op.BASEFEE)
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
                ),
            )
            + Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.JUMPI(
                pc=0x156,
                condition=Op.EQ(Op.SLOAD(key=0x0), Op.MLOAD(offset=0x0)),
            )
            + Op.MSTORE(offset=0x0, value=0xBADBADBAD)
            + Op.JUMP(pc=0x156)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
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
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.MSTORE(offset=0x0, value=Op.BASEFEE)
            + Op.JUMP(pc=0x156)
        ),
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 12, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 13, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 14, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 15, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 16, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 17, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 18, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 19, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 20, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 21, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 22, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 23, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 24, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                Address("0x553e6c30af61e7a3576f31311ea8a620f80d047e"): Account(
                    code=bytes.fromhex(
                        "00000000000000000000000000000000000000000000000000000000000000000a"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 25, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                Address("0x13210e82db5c3add4875aab56c49f5e8cad571cd"): Account(
                    code=bytes.fromhex(
                        "00000000000000000000000000000000000000000000000000000000000000000a"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 26, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                Address("0x553e6c30af61e7a3576f31311ea8a620f80d047e"): Account(
                    code=bytes.fromhex("4860005260206000f3")
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 27, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                Address("0x4a8389cafc02d5d6fa57dcb401181e07aa72979b"): Account(
                    code=bytes.fromhex("4860005260206000f3")
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 28, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                Address("0x553e6c30af61e7a3576f31311ea8a620f80d047e"): Account(
                    code=bytes.fromhex("4860005260206000f3")
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 29, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                Address("0x4a8389cafc02d5d6fa57dcb401181e07aa72979b"): Account(
                    code=bytes.fromhex("4860005260206000f3")
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 30, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                Address("0x553e6c30af61e7a3576f31311ea8a620f80d047e"): Account(
                    code=bytes.fromhex("4860005260206000f3")
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 31, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                Address("0x4a8389cafc02d5d6fa57dcb401181e07aa72979b"): Account(
                    code=bytes.fromhex("4860005260206000f3")
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 32, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                Address("0x553e6c30af61e7a3576f31311ea8a620f80d047e"): Account(
                    code=bytes.fromhex("4860005260206000f3")
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 33, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                Address("0x4a8389cafc02d5d6fa57dcb401181e07aa72979b"): Account(
                    code=bytes.fromhex("4860005260206000f3")
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 34, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("486000526000516040526021603ff3")
                ),
                callee_1: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("48600052600051600055fe"),
                ),
                callee_3: Account(code=bytes.fromhex("4860005260206000f3")),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex("4860005260005160005560206000fd"),
                ),
                callee_5: Account(
                    code=bytes.fromhex("60006220c0de81813b9283923c6000f3")
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af11560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6020600080808061ca115af21560155760206000f35b60206000fd"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115af41560145760206000f35b60206000fd"
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "60206000808061ca115afa1560145760206000f35b60206000fd"
                    )
                ),
                callee_10: Account(code=bytes.fromhex("6000ff")),
                callee_11: Account(
                    code=bytes.fromhex(
                        "6000358015602d5760019003600052602060008181806460baccfa575af11560275760206000f35b60206000fd5b4860005260206000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 10},
                    code=bytes.fromhex(
                        "6160a760005260018060043563c0dec0de3b602061c0de3b831561058a578360f114610574578360f21461055e578360f414610549578360fa14610534578361f1f11461051c578361f2f114610504578361f4f1146104ed578361faf1146104d6578361f1f2146104be578361f2f2146104a6578361f4f21461048f578361faf214610478578361f1f414610460578361f2f414610448578361f4f414610431578361faf41461041a578361f1fa14610402578361f2fa146103ea578361f4fa146103d3578361fafa146103bc578360fd14610384578360fe1461034a578360ff14610311578360f0146102eb578360f5146102c157508261f0f114610297578261f5f11461026b578261f0f214610248578261f5f214610223578261f0f414610201578261f5f4146101dd578261f0fa146101b4578261f5fa146101895750506460baccfa571461016e5765bad0bad0bad06000525b15610168571561016857600051600055005b60206000fd5b506103ff600052602060008181806460baccfa575af1610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f5602060008080845afa610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f0602060008080845afa610156565b9150615a17935080925060008263c0dec0de3c6000f5602060008080845af4610156565b819450809350600091925063c0dec0de3c6000f0602060008080845af4610156565b9150615a17935080925060008263c0dec0de3c6000f560206000808080855af2610156565b819450809350600091925063c0dec0de3c6000f060206000808080855af2610156565b9150615a17935080925060008263c0dec0de3c670de0b6b3a7640000f560206000808080855af1610156565b819450809350600091925063c0dec0de3c670de0b6b3a7640000f060206000808080855af1610156565b92509050615a179293508160008261c0de3c670de0b6b3a7640000f590602060016000843c610156565b9394509150508160008261c0de3c670de0b6b3a7640000f090602060016000843c610156565b505050504860005260005160005560008080808063deaddead5af150486000526000516000541461015657640badbadbad600052610156565b5050505048600052600051600055600080808080620600066161a8f150486000526000516000541461015657640badbadbad600052610156565b50505050486000526000516000556000808080806260bacc5af150486000526000516000541461015657640badbadbad600052610156565b505050505060206000808063ca1100fa5afa610156565b505050505060206000808063ca1100fa5af4610156565b50505050506020600080808063ca1100fa5af2610156565b50505050506020600080808063ca1100fa5af1610156565b505050505060206000808063ca1100f45afa610156565b505050505060206000808063ca1100f45af4610156565b50505050506020600080808063ca1100f45af2610156565b50505050506020600080808063ca1100f45af1610156565b505050505060206000808063ca1100f25afa610156565b505050505060206000808063ca1100f25af4610156565b50505050506020600080808063ca1100f25af2610156565b50505050506020600080808063ca1100f25af1610156565b505050505060206000808063ca1100f15afa610156565b505050505060206000808063ca1100f15af4610156565b50505050506020600080808063ca1100f15af2610156565b50505050506020600080808063ca1100f15af1610156565b505050505060206000808061ca115afa610156565b505050505060206000808061ca115af4610156565b50505050506020600080808061ca115af2610156565b50505050506020600080808061ca115af1610156565b505050504860005261015656"  # noqa: E501
                    ),
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        gas_price=2000,
        nonce=1,
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
