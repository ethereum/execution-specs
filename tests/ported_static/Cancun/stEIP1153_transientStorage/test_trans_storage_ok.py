"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/Cancun/stEIP1153_transientStorage
transStorageOKFiller.yml
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
    "ebd141d50000000000000000000000000000000000000000000000000000000000000010",
    "6e3a72040000000000000000000000000000000000000000000000000000000000000010",
    "c1c922f10000000000000000000000000000000000000000000000000000000000000010",
    "ebd141d50000000000000000000000000000000000000000000000000000000000000100",
    "5114e2c8000000000000000000000000000000000000000000000000000000000000000a",
    "5114e2c80000000000000000000000000000000000000000000000000000000000000032",
    "264bb86a0000000000000000000000000000000000000000000000000000000000000006",
    "7074a4860000000000000000000000000000000000000000000000000000000000000006",
    "7f9317bd",
    "c54b5829f2f4f1f2f4f1f2f4f1f2f4f1f2f4f1f2f4f1f2f4f1f2f4f1f2f4f1f2f4f1f1f1",
    "c54b5829f1f1f1f1f2f2f2f2f4f4f4f4f1f1f1f1f2f2f2f2f4f4f4f4f1f1f1f1f2f2f2f2",
    "c54b5829f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1",
    "c54b5829f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1",
    "c54b5829f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2f2",
    "c54b5829f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4f4",
    "5d7935df",
]

TX_GAS = [16777216]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/Cancun/stEIP1153_transientStorage/transStorageOKFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(6, 0, 0, id="case0"),
        pytest.param(4, 0, 0, id="case1"),
        pytest.param(5, 0, 0, id="case2"),
        pytest.param(1, 0, 0, id="case3"),
        pytest.param(10, 0, 0, id="case4"),
        pytest.param(11, 0, 0, id="case5"),
        pytest.param(12, 0, 0, id="case6"),
        pytest.param(13, 0, 0, id="case7"),
        pytest.param(14, 0, 0, id="case8"),
        pytest.param(9, 0, 0, id="case9"),
        pytest.param(7, 0, 0, id="case10"),
        pytest.param(2, 0, 0, id="case11"),
        pytest.param(8, 0, 0, id="case12"),
        pytest.param(15, 0, 0, id="case13"),
        pytest.param(0, 0, 0, id="case14"),
        pytest.param(3, 0, 0, id="case15"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_trans_storage_ok(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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

    # Source: Yul
    # {
    #     function tload_temp(loc) -> val {
    #       val := verbatim_1i_1o(hex"5C", loc)
    #     }
    #
    #     function tstore_temp(loc, val) {
    #       verbatim_2i_0o(hex"5D", loc, val)
    #     }
    #
    #     // There is calldata, so write to Trans[0]
    #     if calldatasize() {
    #        tstore_temp(0, 0x60A7)
    #     }
    #
    #     // Return Trans[0]
    #     // This happens whether we are called with data or not.
    #     mstore(0, tload_temp(0))
    #     return(0,32)
    # }
    callee = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x12, condition=Op.CALLDATASIZE)
            + Op.JUMPDEST
            + Op.PUSH1[0xB]
            + Op.PUSH0
            + Op.JUMP(pc=0x20)
            + Op.JUMPDEST
            + Op.PUSH0
            + Op.MSTORE
            + Op.RETURN(offset=Op.PUSH0, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x1C]
            + Op.PUSH2[0x60A7]
            + Op.PUSH0
            + Op.JUMP(pc=0x24)
            + Op.JUMPDEST
            + Op.JUMP(pc=0x4)
            + Op.JUMPDEST
            + Op.TLOAD
            + Op.SWAP1
            + Op.JUMP
            + Op.JUMPDEST
            + Op.TSTORE
            + Op.JUMP
        ),
        address=Address("0x00000000000000000000000000000000000057a7"),  # noqa: E501
    )
    # Source: Yul
    # {
    #     function tload_temp(loc) -> val {
    #       val := verbatim_1i_1o(hex"5C", loc)
    #     }
    #
    #     function tstore_temp(loc, val) {
    #       verbatim_2i_0o(hex"5D", loc, val)
    #     }
    #
    #     tstore_temp(0, add(tload_temp(0), 1))
    # }
    callee_1 = pre.deploy_contract(
        code=(
            Op.PUSH1[0x10]
            + Op.PUSH1[0x1]
            + Op.PUSH1[0xA]
            + Op.PUSH0
            + Op.JUMP(pc=0x12)
            + Op.JUMPDEST
            + Op.ADD
            + Op.PUSH0
            + Op.JUMP(pc=0x16)
            + Op.JUMPDEST
            + Op.STOP
            + Op.JUMPDEST
            + Op.TLOAD
            + Op.SWAP1
            + Op.JUMP
            + Op.JUMPDEST
            + Op.TSTORE
            + Op.JUMP
        ),
        address=Address("0x000000000000000000000000000000000000add1"),  # noqa: E501
    )
    # Source: Yul
    # {
    #     function tload_temp(loc) -> val {
    #       val := verbatim_1i_1o(hex"5C", loc)
    #     }
    #
    #     function tstore_temp(loc, val) {
    #       verbatim_2i_0o(hex"5D", loc, val)
    #     }
    #
    #     // We are inside the loop
    #     if eq(caller(), address()) {
    #       let counter := tload_temp(0)
    #
    #       // If counter is zero, we're at an end of the loop (a leaf of
    #       // the tree), return.
    #       if eq(counter,0) {
    #         return(0,0)
    #       }
    #
    #       // If counter isn't zero, call yourself with counter-1 twice and
    #       // add one to Trans[1]
    #       tstore_temp(0, sub(counter, 1))
    #       let res := call(gas(), address(), 0, 0,0, 0,0)
    #       if iszero(res) { // If the call failed, fail too
    #          revert(0,0)
    #       }
    #
    #       // We need to repair Trans[0] because it got overwritten in
    #       // the previous call
    #       tstore_temp(0, sub(counter, 1))
    # ... (22 more lines)
    callee_2 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x33, condition=Op.EQ(Op.CALLER, Op.ADDRESS))
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xE, condition=Op.SUB(Op.CALLER, Op.ADDRESS))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x1B]
            + Op.CALLDATALOAD(offset=Op.PUSH0)
            + Op.SSTORE(key=0x1, value=Op.DUP1)
            + Op.PUSH0
            + Op.JUMP(pc=0x8D)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=Op.ADDRESS,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=Op.PUSH0,
                ),
            )
            + Op.PUSH1[0x2E]
            + Op.PUSH1[0x1]
            + Op.JUMP(pc=0x89)
            + Op.JUMPDEST
            + Op.PUSH1[0x3]
            + Op.SSTORE
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x3A]
            + Op.PUSH0
            + Op.JUMP(pc=0x89)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x87, condition=Op.ISZERO(Op.DUP1))
            + Op.PUSH1[0x4A]
            + Op.SUB(Op.DUP3, 0x1)
            + Op.PUSH0
            + Op.JUMP(pc=0x8D)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x83,
                condition=Op.ISZERO(
                    Op.CALL(
                        gas=Op.GAS,
                        address=Op.ADDRESS,
                        value=Op.DUP1,
                        args_offset=Op.DUP1,
                        args_size=Op.DUP1,
                        ret_offset=Op.DUP1,
                        ret_size=Op.PUSH0,
                    ),
                ),
            )
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x61]
            + Op.SWAP2
            + Op.SUB
            + Op.PUSH0
            + Op.JUMP(pc=0x8D)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x83,
                condition=Op.ISZERO(
                    Op.CALL(
                        gas=Op.GAS,
                        address=Op.ADDRESS,
                        value=Op.DUP1,
                        args_offset=Op.DUP1,
                        args_size=Op.DUP1,
                        ret_offset=Op.DUP1,
                        ret_size=Op.PUSH0,
                    ),
                ),
            )
            + Op.PUSH1[0x7F]
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x78]
            + Op.DUP2
            + Op.JUMP(pc=0x89)
            + Op.JUMPDEST
            + Op.ADD
            + Op.PUSH1[0x1]
            + Op.JUMP(pc=0x8D)
            + Op.JUMPDEST
            + Op.JUMP(pc=0x6)
            + Op.JUMPDEST
            + Op.REVERT(offset=Op.DUP1, size=Op.PUSH0)
            + Op.JUMPDEST
            + Op.STOP
            + Op.JUMPDEST
            + Op.TLOAD
            + Op.SWAP1
            + Op.JUMP
            + Op.JUMPDEST
            + Op.TSTORE
            + Op.JUMP
        ),
        address=Address("0x00000000000000000000000000000000264bb86a"),  # noqa: E501
    )
    # Source: Yul
    # {
    #     function tload_temp(loc) -> val {
    #       val := verbatim_1i_1o(hex"5C", loc)
    #     }
    #
    #     function tstore_temp(loc, val) {
    #       verbatim_2i_0o(hex"5D", loc, val)
    #     }
    #
    #     // If we are called by 0xca11bacc, this is part of the loop
    #     if eq(caller(), 0xca11bacc) {
    #       let counter := tload_temp(0)
    #
    #       // If the counter is equal to zero, we're done - return.
    #       if eq(counter,0) {
    #         return(0,0)
    #       }
    #
    #       // If counter isn't zero, add counter to Trans[1] and do recursion
    #       tstore_temp(1, add(tload_temp(1), counter))
    #
    #       // Change the loop variable and call 0xca11bacc, which calls us back.  # noqa: E501
    #       tstore_temp(0, sub(counter, 1))
    #       let res := call(gas(), 0xca11bacc, 0, 0,0, 0,0)
    #       if iszero(res) { // If the call failed, fail too
    #          revert(0,0)
    #       }
    #     }
    #
    #     // If called by a different address from 0xca11bacc, we are the first
    # ... (12 more lines)
    callee_3 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x3F, condition=Op.EQ(Op.CALLER, 0xCA11BACC))
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x16, condition=Op.SUB(Op.CALLER, 0xCA11BACC))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x23]
            + Op.CALLDATALOAD(offset=Op.PUSH0)
            + Op.SSTORE(key=0x1, value=Op.DUP1)
            + Op.PUSH0
            + Op.JUMP(pc=0x7F)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=0xCA11BACC,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=Op.PUSH0,
                ),
            )
            + Op.PUSH1[0x3A]
            + Op.PUSH1[0x1]
            + Op.JUMP(pc=0x7B)
            + Op.JUMPDEST
            + Op.PUSH1[0x3]
            + Op.SSTORE
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x46]
            + Op.PUSH0
            + Op.JUMP(pc=0x7B)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x79, condition=Op.ISZERO(Op.DUP1))
            + Op.PUSH1[0x1]
            + Op.DUP2
            + Op.PUSH1[0x60]
            + Op.PUSH1[0x66]
            + Op.SWAP4
            + Op.PUSH1[0x5A]
            + Op.DUP5
            + Op.JUMP(pc=0x7B)
            + Op.JUMPDEST
            + Op.ADD
            + Op.DUP4
            + Op.JUMP(pc=0x7F)
            + Op.JUMPDEST
            + Op.SUB
            + Op.PUSH0
            + Op.JUMP(pc=0x7F)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xA,
                condition=Op.CALL(
                    gas=Op.GAS,
                    address=0xCA11BACC,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=Op.PUSH0,
                ),
            )
            + Op.REVERT(offset=Op.DUP1, size=Op.PUSH0)
            + Op.JUMPDEST
            + Op.STOP
            + Op.JUMPDEST
            + Op.TLOAD
            + Op.SWAP1
            + Op.JUMP
            + Op.JUMPDEST
            + Op.TSTORE
            + Op.JUMP
        ),
        address=Address("0x000000000000000000000000000000005114e2c8"),  # noqa: E501
    )
    # Source: Yul
    # {
    #     // Set up Trans[0] with a regular call.
    #     sstore(0x10,call(gas(), 0x57A7, 0, 0,1, 0,32))
    #     sstore(0, mload(0))
    #
    #     // Use staticcall to read Trans[0] of 0x0..57A7.
    #     mstore(0,0)
    #     sstore(0x11,staticcall(gas(), 0x57A7, 0,0, 0,32))
    #     sstore(1, mload(0))
    #
    #     // Try to use staticall to write Trans[0]. This should fail.
    #     mstore(0,0)
    #     sstore(0x12,staticcall(gas(), 0x57A7, 0,1, 0,32))
    #     sstore(2, mload(0))
    # }
    callee_4 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x10,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=0x57A7,
                    value=Op.DUP1,
                    args_offset=Op.DUP2,
                    args_size=0x1,
                    ret_offset=Op.PUSH0,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=Op.PUSH0, value=Op.MLOAD(offset=Op.PUSH0))
            + Op.MSTORE(offset=Op.DUP1, value=Op.PUSH0)
            + Op.SSTORE(
                key=0x11,
                value=Op.STATICCALL(
                    gas=Op.GAS,
                    address=0x57A7,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.PUSH0,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=Op.PUSH0))
            + Op.MSTORE(offset=Op.DUP1, value=Op.PUSH0)
            + Op.SSTORE(
                key=0x12,
                value=Op.STATICCALL(
                    gas=Op.GAS,
                    address=0x57A7,
                    args_offset=Op.DUP2,
                    args_size=0x1,
                    ret_offset=Op.PUSH0,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=Op.PUSH0))
            + Op.STOP
        ),
        storage={0x2: 0x60A7, 0x12: 0x60A7},
        address=Address("0x000000000000000000000000000000005d7935df"),  # noqa: E501
    )
    # Source: Yul
    # {
    #     function tload_temp(loc) -> val {
    #       val := verbatim_1i_1o(hex"5C", loc)
    #     }
    #
    #     function tstore_temp(loc, val) {
    #       verbatim_2i_0o(hex"5D", loc, val)
    #     }
    #
    #     // If we are called by ourselves, this is part of the loop.
    #     if eq(caller(), address()) {
    #       let counter := tload_temp(0)
    #
    #       // Loop ended, return
    #       if eq(counter,0) {
    #         return(0,0)
    #       }
    #
    #
    #       // Change the loop variable and call yourself
    #       tstore_temp(1, add(tload_temp(1), counter))
    #       tstore_temp(0, sub(counter, 1))
    #       let res := callcode(gas(), address(), 0, 0,0, 0,0)
    #       if iszero(res) { // If the call failed, fail too
    #          revert(0,0)
    #       }
    #     }
    #
    #     // If called by a different address, we are the first call and need
    #     // to setup Trans[0] before starting the loop.
    # ... (15 more lines)
    callee_5 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x33, condition=Op.EQ(Op.CALLER, Op.ADDRESS))
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xE, condition=Op.SUB(Op.CALLER, Op.ADDRESS))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x1B]
            + Op.CALLDATALOAD(offset=Op.PUSH0)
            + Op.SSTORE(key=0x1, value=Op.DUP1)
            + Op.PUSH0
            + Op.JUMP(pc=0x6F)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=Op.ADDRESS,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=Op.PUSH0,
                ),
            )
            + Op.PUSH1[0x2E]
            + Op.PUSH1[0x1]
            + Op.JUMP(pc=0x6B)
            + Op.JUMPDEST
            + Op.PUSH1[0x3]
            + Op.SSTORE
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x3A]
            + Op.PUSH0
            + Op.JUMP(pc=0x6B)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x69, condition=Op.ISZERO(Op.DUP1))
            + Op.PUSH1[0x1]
            + Op.DUP2
            + Op.PUSH1[0x54]
            + Op.PUSH1[0x5A]
            + Op.SWAP4
            + Op.PUSH1[0x4E]
            + Op.DUP5
            + Op.JUMP(pc=0x6B)
            + Op.JUMPDEST
            + Op.ADD
            + Op.DUP4
            + Op.JUMP(pc=0x6F)
            + Op.JUMPDEST
            + Op.SUB
            + Op.PUSH0
            + Op.JUMP(pc=0x6F)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x6,
                condition=Op.CALLCODE(
                    gas=Op.GAS,
                    address=Op.ADDRESS,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=Op.PUSH0,
                ),
            )
            + Op.REVERT(offset=Op.DUP1, size=Op.PUSH0)
            + Op.JUMPDEST
            + Op.STOP
            + Op.JUMPDEST
            + Op.TLOAD
            + Op.SWAP1
            + Op.JUMP
            + Op.JUMPDEST
            + Op.TSTORE
            + Op.JUMP
        ),
        address=Address("0x000000000000000000000000000000006e3a7204"),  # noqa: E501
    )
    # Source: Yul
    # {
    #     function tload_temp(loc) -> val {
    #       val := verbatim_1i_1o(hex"5C", loc)
    #     }
    #
    #     function tstore_temp(loc, val) {
    #       verbatim_2i_0o(hex"5D", loc, val)
    #     }
    #
    #     // If we are in the loop
    #     if eq(caller(), address()) {
    #       let counter := tload_temp(0)
    #
    #       // If the counter is zero, we're at loop's end, return
    #       if eq(counter,0) {
    #         return(0,0)
    #       }
    #
    #       // If counter isn't zero
    #       // Call yourself with counter-1 twice then add 1 to Trans[1]
    #       // Note that one call is callcode() and the other delegatecall().
    #       // This way the same test checks both of them.
    #
    #       tstore_temp(0, sub(counter, 1))
    #       let res := callcode(gas(), address(), 0, 0,0, 0,0)
    #       if iszero(res) { // If the call failed, fail too
    #          revert(0,0)
    #       }
    #
    #       // We need to repair Trans[0] because it got overwritten in
    # ... (25 more lines)
    callee_6 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x33, condition=Op.EQ(Op.CALLER, Op.ADDRESS))
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xE, condition=Op.SUB(Op.CALLER, Op.ADDRESS))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x1B]
            + Op.CALLDATALOAD(offset=Op.PUSH0)
            + Op.SSTORE(key=0x1, value=Op.DUP1)
            + Op.PUSH0
            + Op.JUMP(pc=0x8C)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=Op.ADDRESS,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=Op.PUSH0,
                ),
            )
            + Op.PUSH1[0x2E]
            + Op.PUSH1[0x1]
            + Op.JUMP(pc=0x88)
            + Op.JUMPDEST
            + Op.PUSH1[0x3]
            + Op.SSTORE
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x3A]
            + Op.PUSH0
            + Op.JUMP(pc=0x88)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x86, condition=Op.ISZERO(Op.DUP1))
            + Op.PUSH1[0x4A]
            + Op.SUB(Op.DUP3, 0x1)
            + Op.PUSH0
            + Op.JUMP(pc=0x8C)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x82,
                condition=Op.ISZERO(
                    Op.CALLCODE(
                        gas=Op.GAS,
                        address=Op.ADDRESS,
                        value=Op.DUP1,
                        args_offset=Op.DUP1,
                        args_size=Op.DUP1,
                        ret_offset=Op.DUP1,
                        ret_size=Op.PUSH0,
                    ),
                ),
            )
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x61]
            + Op.SWAP2
            + Op.SUB
            + Op.PUSH0
            + Op.JUMP(pc=0x8C)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x82,
                condition=Op.ISZERO(
                    Op.DELEGATECALL(
                        gas=Op.GAS,
                        address=Op.ADDRESS,
                        args_offset=Op.DUP1,
                        args_size=Op.DUP1,
                        ret_offset=Op.DUP1,
                        ret_size=Op.PUSH0,
                    ),
                ),
            )
            + Op.PUSH1[0x7E]
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x77]
            + Op.DUP2
            + Op.JUMP(pc=0x88)
            + Op.JUMPDEST
            + Op.ADD
            + Op.PUSH1[0x1]
            + Op.JUMP(pc=0x8C)
            + Op.JUMPDEST
            + Op.JUMP(pc=0x6)
            + Op.JUMPDEST
            + Op.REVERT(offset=Op.DUP1, size=Op.PUSH0)
            + Op.JUMPDEST
            + Op.STOP
            + Op.JUMPDEST
            + Op.TLOAD
            + Op.SWAP1
            + Op.JUMP
            + Op.JUMPDEST
            + Op.TSTORE
            + Op.JUMP
        ),
        address=Address("0x000000000000000000000000000000007074a486"),  # noqa: E501
    )
    # Source: Yul
    # {
    #     function tload_temp(loc) -> val {
    #       val := verbatim_1i_1o(hex"5C", loc)
    #     }
    #
    #     function tstore_temp(loc, val) {
    #       verbatim_2i_0o(hex"5D", loc, val)
    #     }
    #
    #     // The initial value of the counter is zero
    #     sstore(0, tload_temp(0))
    #
    #     // CALLCODE increments our Trans[0]
    #     sstore(0x11, callcode(gas(), 0xadd1, 0, 0,0, 0,0))
    #     sstore(1, tload_temp(0))
    #
    #     // DELEGATECALL increments our Trans[0]
    #     sstore(0x12, delegatecall(gas(), 0xadd1, 0,0, 0,0))
    #     sstore(2, tload_temp(0))
    #
    #     // CALL does not increment our Trans[0], it means a different
    #     // transient storage
    #     sstore(0x13, call(gas(), 0xadd1, 0, 0,0, 0,0))
    #     sstore(3, tload_temp(0))
    # }
    callee_7 = pre.deploy_contract(
        code=(
            Op.PUSH1[0x6]
            + Op.PUSH0
            + Op.JUMP(pc=0x4E)
            + Op.JUMPDEST
            + Op.PUSH0
            + Op.SSTORE
            + Op.SSTORE(
                key=0x11,
                value=Op.CALLCODE(
                    gas=Op.GAS,
                    address=0xADD1,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=Op.PUSH0,
                ),
            )
            + Op.PUSH1[0x1C]
            + Op.PUSH0
            + Op.JUMP(pc=0x4E)
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.SSTORE
            + Op.SSTORE(
                key=0x12,
                value=Op.DELEGATECALL(
                    gas=Op.GAS,
                    address=0xADD1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=Op.PUSH0,
                ),
            )
            + Op.PUSH1[0x32]
            + Op.PUSH0
            + Op.JUMP(pc=0x4E)
            + Op.JUMPDEST
            + Op.PUSH1[0x2]
            + Op.SSTORE
            + Op.SSTORE(
                key=0x13,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=0xADD1,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=Op.PUSH0,
                ),
            )
            + Op.PUSH1[0x49]
            + Op.PUSH0
            + Op.JUMP(pc=0x4E)
            + Op.JUMPDEST
            + Op.PUSH1[0x3]
            + Op.SSTORE
            + Op.STOP
            + Op.JUMPDEST
            + Op.TLOAD
            + Op.SWAP1
            + Op.JUMP
        ),
        storage={0x0: 0x60A7},
        address=Address("0x000000000000000000000000000000007f9317bd"),  # noqa: E501
    )
    # Source: Yul
    # {
    #     function tload_temp(loc) -> val {
    #       val := verbatim_1i_1o(hex"5C", loc)
    #     }
    #
    #     function tstore_temp(loc, val) {
    #       verbatim_2i_0o(hex"5D", loc, val)
    #     }
    #
    #     // If we are called by ourselves, this is part of the loop.
    #     if eq(caller(), address()) {
    #       let counter := tload_temp(0)
    #
    #       // If the counter is equal to zero, we're done - return.
    #       if eq(counter,0) {
    #         return(0,0)
    #       }
    #
    #       // Change the loop variable and call yourself
    #       tstore_temp(1, add(tload_temp(1), counter))
    #       tstore_temp(0, sub(counter, 1))
    #       let res := delegatecall(gas(), address(), 0,0, 0,0)
    #       if iszero(res) { // If the call failed, fail too
    #          revert(0,0)
    #       }
    #     }
    #
    #
    #     // If called by a different address, we are the first call and need
    #     // to setup Trans[0] before starting the loop.
    # ... (15 more lines)
    callee_8 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x33, condition=Op.EQ(Op.CALLER, Op.ADDRESS))
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xE, condition=Op.SUB(Op.CALLER, Op.ADDRESS))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x1B]
            + Op.CALLDATALOAD(offset=Op.PUSH0)
            + Op.SSTORE(key=0x1, value=Op.DUP1)
            + Op.PUSH0
            + Op.JUMP(pc=0x6E)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=Op.ADDRESS,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=Op.PUSH0,
                ),
            )
            + Op.PUSH1[0x2E]
            + Op.PUSH1[0x1]
            + Op.JUMP(pc=0x6A)
            + Op.JUMPDEST
            + Op.PUSH1[0x3]
            + Op.SSTORE
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x3A]
            + Op.PUSH0
            + Op.JUMP(pc=0x6A)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x68, condition=Op.ISZERO(Op.DUP1))
            + Op.PUSH1[0x1]
            + Op.DUP2
            + Op.PUSH1[0x54]
            + Op.PUSH1[0x5A]
            + Op.SWAP4
            + Op.PUSH1[0x4E]
            + Op.DUP5
            + Op.JUMP(pc=0x6A)
            + Op.JUMPDEST
            + Op.ADD
            + Op.DUP4
            + Op.JUMP(pc=0x6E)
            + Op.JUMPDEST
            + Op.SUB
            + Op.PUSH0
            + Op.JUMP(pc=0x6E)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x6,
                condition=Op.DELEGATECALL(
                    gas=Op.GAS,
                    address=Op.ADDRESS,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=Op.PUSH0,
                ),
            )
            + Op.REVERT(offset=Op.DUP1, size=Op.PUSH0)
            + Op.JUMPDEST
            + Op.STOP
            + Op.JUMPDEST
            + Op.TLOAD
            + Op.SWAP1
            + Op.JUMP
            + Op.JUMPDEST
            + Op.TSTORE
            + Op.JUMP
        ),
        address=Address("0x00000000000000000000000000000000c1c922f1"),  # noqa: E501
    )
    # Source: Yul
    # {
    #     function tload_temp(loc) -> val {
    #       val := verbatim_1i_1o(hex"5C", loc)
    #     }
    #
    #     function tstore_temp(loc, val) {
    #       verbatim_2i_0o(hex"5D", loc, val)
    #     }
    #
    #     // If we are at the bottom of the call stack, increment
    #     // the counter and return
    #     if eq(calldatasize(), 0) {
    #        tstore_temp(0, add(tload_temp(0),1))
    #        return(0,0)
    #     }
    #
    #     // If we are at the top of the stack (called by a different contract),  # noqa: E501
    #     // set the counter to one
    #     if iszero(eq(address(), caller())) {
    #        tstore_temp(0, 1)
    #     }
    #
    #     // Read the most significant byte of the input.
    #     // Luckily for us the input is top justified - if the caller provided
    #     // just n bytes (n<20), they will be the top n bytes of calldataload(0).  # noqa: E501
    #     let callType := shr(
    #         248,
    #         calldataload(0)
    #     )
    #
    # ... (32 more lines)
    callee_9 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x81, condition=Op.ISZERO(Op.CALLDATASIZE))
            + Op.JUMPI(pc=0x74, condition=Op.SUB(Op.ADDRESS, Op.CALLER))
            + Op.JUMPDEST
            + Op.SHR(0xF8, Op.CALLDATALOAD(offset=Op.PUSH0))
            + Op.MSTORE(
                offset=Op.PUSH0, value=Op.CALLDATALOAD(offset=Op.PUSH0)
            )
            + Op.SUB(Op.CALLDATASIZE, 0x1)
            + Op.SWAP1
            + Op.PUSH1[0x1]
            + Op.SWAP1
            + Op.JUMPI(pc=0x64, condition=Op.EQ(0xF1, Op.DUP1))
            + Op.JUMPI(pc=0x54, condition=Op.EQ(0xF2, Op.DUP1))
            + Op.PUSH1[0xF4]
            + Op.JUMPI(pc=0x46, condition=Op.EQ)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.JUMPI(pc=0x3B, condition=Op.SUB(Op.ADDRESS, Op.CALLER))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x42]
            + Op.PUSH0
            + Op.JUMP(pc=0x94)
            + Op.JUMPDEST
            + Op.PUSH0
            + Op.SSTORE
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH0
            + Op.SWAP2
            + Op.DUP3
            + Op.SWAP2
            + Op.ADDRESS
            + Op.GAS
            + Op.POP(Op.DELEGATECALL)
            + Op.PUSH0
            + Op.DUP1
            + Op.JUMP(pc=0x31)
            + Op.JUMPDEST
            + Op.POP
            + Op.PUSH0
            + Op.SWAP2
            + Op.DUP3
            + Op.SWAP2
            + Op.DUP3
            + Op.ADDRESS
            + Op.GAS
            + Op.POP(Op.CALLCODE)
            + Op.PUSH0
            + Op.DUP1
            + Op.JUMP(pc=0x31)
            + Op.JUMPDEST
            + Op.POP
            + Op.PUSH0
            + Op.SWAP2
            + Op.DUP3
            + Op.SWAP2
            + Op.DUP3
            + Op.ADDRESS
            + Op.GAS
            + Op.POP(Op.CALL)
            + Op.PUSH0
            + Op.DUP1
            + Op.JUMP(pc=0x31)
            + Op.JUMPDEST
            + Op.PUSH1[0x7D]
            + Op.PUSH1[0x1]
            + Op.PUSH0
            + Op.JUMP(pc=0x98)
            + Op.JUMPDEST
            + Op.JUMP(pc=0xB)
            + Op.JUMPDEST
            + Op.PUSH1[0x92]
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x8C]
            + Op.PUSH0
            + Op.JUMP(pc=0x94)
            + Op.JUMPDEST
            + Op.ADD
            + Op.PUSH0
            + Op.JUMP(pc=0x98)
            + Op.JUMPDEST
            + Op.STOP
            + Op.JUMPDEST
            + Op.TLOAD
            + Op.SWAP1
            + Op.JUMP
            + Op.JUMPDEST
            + Op.TSTORE
            + Op.JUMP
        ),
        address=Address("0x00000000000000000000000000000000c54b5829"),  # noqa: E501
    )
    # Source: Yul
    # {
    #     function tload_temp(loc) -> val {
    #       val := verbatim_1i_1o(hex"5C", loc)
    #     }
    #
    #     function tstore_temp(loc, val) {
    #       verbatim_2i_0o(hex"5D", loc, val)
    #     }
    #
    #     // Write these values to storage (overwriting the 0x60A7's).
    #     // If these values are not zero, there is a problem.
    #     sstore(0, tload_temp(0))
    #     sstore(1, tload_temp(1))
    #     pop(call(gas(), caller(), 0, 0,0, 0,0))
    # }
    callee_10 = pre.deploy_contract(
        code=(
            Op.PUSH1[0x6]
            + Op.PUSH0
            + Op.JUMP(pc=0x1D)
            + Op.JUMPDEST
            + Op.PUSH0
            + Op.SSTORE
            + Op.PUSH1[0x10]
            + Op.PUSH1[0x1]
            + Op.JUMP(pc=0x1D)
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.SSTORE
            + Op.CALL(
                gas=Op.GAS,
                address=Op.CALLER,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=Op.PUSH0,
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.TLOAD
            + Op.SWAP1
            + Op.JUMP
        ),
        storage={0x0: 0x60A7, 0x1: 0x60A7},
        address=Address("0x00000000000000000000000000000000ca11bacc"),  # noqa: E501
    )
    # Source: Yul
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
    #     // If we are called by ourselves, this is part of the loop.
    #     if eq(caller(), address()) {
    #       let counter := tload_temp(0)
    #
    #       // If the counter is equal to zero, we're done - return.
    #       if eq(counter,0) {
    #         return(0,0)
    #       }
    #
    #       // If counter isn't zero, add counter to Trans[1] and do recursion
    #       tstore_temp(1, add(tload_temp(1), counter))
    #
    #       // Change the loop variable and call yourself
    #       tstore_temp(0, sub(counter, 1))
    #       let res := call(gas(), address(), 0, 0,0, 0,0)
    #       if iszero(res) { // If the call failed, fail too
    #          revert(0,0)
    #       }
    # ... (15 more lines)
    callee_11 = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x33, condition=Op.EQ(Op.CALLER, Op.ADDRESS))
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xE, condition=Op.SUB(Op.CALLER, Op.ADDRESS))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x1B]
            + Op.CALLDATALOAD(offset=Op.PUSH0)
            + Op.SSTORE(key=0x1, value=Op.DUP1)
            + Op.PUSH0
            + Op.JUMP(pc=0x6F)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=Op.ADDRESS,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=Op.PUSH0,
                ),
            )
            + Op.PUSH1[0x2E]
            + Op.PUSH1[0x1]
            + Op.JUMP(pc=0x6B)
            + Op.JUMPDEST
            + Op.PUSH1[0x3]
            + Op.SSTORE
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x3A]
            + Op.PUSH0
            + Op.JUMP(pc=0x6B)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x69, condition=Op.ISZERO(Op.DUP1))
            + Op.PUSH1[0x1]
            + Op.DUP2
            + Op.PUSH1[0x54]
            + Op.PUSH1[0x5A]
            + Op.SWAP4
            + Op.PUSH1[0x4E]
            + Op.DUP5
            + Op.JUMP(pc=0x6B)
            + Op.JUMPDEST
            + Op.ADD
            + Op.DUP4
            + Op.JUMP(pc=0x6F)
            + Op.JUMPDEST
            + Op.SUB
            + Op.PUSH0
            + Op.JUMP(pc=0x6F)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x6,
                condition=Op.CALL(
                    gas=Op.GAS,
                    address=Op.ADDRESS,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=Op.PUSH0,
                ),
            )
            + Op.REVERT(offset=Op.DUP1, size=Op.PUSH0)
            + Op.JUMPDEST
            + Op.STOP
            + Op.JUMPDEST
            + Op.TLOAD
            + Op.SWAP1
            + Op.JUMP
            + Op.JUMPDEST
            + Op.TSTORE
            + Op.JUMP
        ),
        address=Address("0x00000000000000000000000000000000ebd141d5"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)
    # Source: Yul
    # {
    #   let func := shr(224, calldataload(0))
    #   let param := calldataload(4)
    #   sstore(0, func)
    #   mstore(0, param)
    #   sstore(1, call(gas(), func, 0, 0,32, 0,0))
    # }
    contract = pre.deploy_contract(
        code=(
            Op.PUSH0
            + Op.DUP1
            + Op.PUSH1[0x20]
            + Op.DUP2
            + Op.DUP1
            + Op.SHR(0xE0, Op.CALLDATALOAD(offset=Op.DUP1))
            + Op.CALLDATALOAD(offset=0x4)
            + Op.SSTORE(key=Op.DUP4, value=Op.DUP2)
            + Op.DUP3
            + Op.MSTORE
            + Op.GAS
            + Op.SSTORE(key=0x1, value=Op.CALL)
            + Op.STOP
        ),
        address=Address("0xdd53b677a6fd4e871a6355f283b1bd7ceb95a95e"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "366012575b600b5f6020565b5f5260205ff35b601c6160a75f6024565b6004565b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60106001600a5f6012565b015f6016565b005b5c90565b5d56"
                    )
                ),
                callee_2: Account(
                    storage={1: 6, 2: 1, 3: 63},
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608d565b5f80808080305af1600255602e60016089565b600355005b603a5f6089565b8015608757604a600182035f608d565b5f80808080305af1156083576001606191035f608d565b5f80808080305af115608357607f60016078816089565b016001608d565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "63ca11bacc3314603f575b63ca11bacc3303601657005b60235f35806001555f607f565b5f8080808063ca11bacc5af1600255603a6001607b565b600355005b60465f607b565b80156079576001816060606693605a84607b565b0183607f565b035f607f565b5f8080808063ca11bacc5af1600a575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    storage={2: 24743, 18: 24743},
                    code=bytes.fromhex(
                        "60205f600181806157a75af16010555f515f555f805260205f80806157a75afa6011555f516001555f805260205f6001816157a75afa6012555f5160025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af26006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608c565b5f80808080305af1600255602e60016088565b600355005b603a5f6088565b8015608657604a600182035f608c565b5f80808080305af2156082576001606191035f608c565b5f808080305af415608257607e60016077816088565b016001608c565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "60065f604e565b5f555f8080808061add15af2601155601c5f604e565b6001555f80808061add15af460125560325f604e565b6002555f8080808061add15af160135560495f604e565b600355005b5c9056"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606e565b5f80808080305af1600255602e6001606a565b600355005b603a5f606a565b80156068576001816054605a93604e84606a565b0183606e565b035f606e565b5f808080305af46006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "36156081573330036074575b5f3560f81c5f355f5260013603906001908060f1146064578060f21460545760f4146046575b5050333003603b57005b60425f6094565b5f55005b5f918291305af4505f806031565b505f91829182305af2505f806031565b505f91829182305af1505f806031565b607d60015f6098565b600b565b60926001608c5f6094565b015f6098565b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    storage={0: 24743, 1: 24743},
                    code=bytes.fromhex(
                        "60065f601d565b5f5560106001601d565b6001555f80808080335af1005b5c9056"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af16006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 0x264BB86A, 1: 1},
                    code=bytes.fromhex(
                        "5f8060208180803560e01c60043581835582525af160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "366012575b600b5f6020565b5f5260205ff35b601c6160a75f6024565b6004565b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60106001600a5f6012565b015f6016565b005b5c90565b5d56"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608d565b5f80808080305af1600255602e60016089565b600355005b603a5f6089565b8015608757604a600182035f608d565b5f80808080305af1156083576001606191035f608d565b5f80808080305af115608357607f60016078816089565b016001608d565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    storage={1: 10, 2: 1, 3: 55},
                    code=bytes.fromhex(
                        "63ca11bacc3314603f575b63ca11bacc3303601657005b60235f35806001555f607f565b5f8080808063ca11bacc5af1600255603a6001607b565b600355005b60465f607b565b80156079576001816060606693605a84607b565b0183607f565b035f607f565b5f8080808063ca11bacc5af1600a575f80fd5b005b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={2: 24743, 18: 24743},
                    code=bytes.fromhex(
                        "60205f600181806157a75af16010555f515f555f805260205f80806157a75afa6011555f516001555f805260205f6001816157a75afa6012555f5160025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af26006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608c565b5f80808080305af1600255602e60016088565b600355005b603a5f6088565b8015608657604a600182035f608c565b5f80808080305af2156082576001606191035f608c565b5f808080305af415608257607e60016077816088565b016001608c565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "60065f604e565b5f555f8080808061add15af2601155601c5f604e565b6001555f80808061add15af460125560325f604e565b6002555f8080808061add15af160135560495f604e565b600355005b5c9056"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606e565b5f80808080305af1600255602e6001606a565b600355005b603a5f606a565b80156068576001816054605a93604e84606a565b0183606e565b035f606e565b5f808080305af46006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "36156081573330036074575b5f3560f81c5f355f5260013603906001908060f1146064578060f21460545760f4146046575b5050333003603b57005b60425f6094565b5f55005b5f918291305af4505f806031565b505f91829182305af2505f806031565b505f91829182305af1505f806031565b607d60015f6098565b600b565b60926001608c5f6094565b015f6098565b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "60065f601d565b5f5560106001601d565b6001555f80808080335af1005b5c9056"  # noqa: E501
                    )
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af16006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 0x5114E2C8, 1: 1},
                    code=bytes.fromhex(
                        "5f8060208180803560e01c60043581835582525af160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "366012575b600b5f6020565b5f5260205ff35b601c6160a75f6024565b6004565b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60106001600a5f6012565b015f6016565b005b5c90565b5d56"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608d565b5f80808080305af1600255602e60016089565b600355005b603a5f6089565b8015608757604a600182035f608d565b5f80808080305af1156083576001606191035f608d565b5f80808080305af115608357607f60016078816089565b016001608d565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    storage={1: 50, 2: 1, 3: 1275},
                    code=bytes.fromhex(
                        "63ca11bacc3314603f575b63ca11bacc3303601657005b60235f35806001555f607f565b5f8080808063ca11bacc5af1600255603a6001607b565b600355005b60465f607b565b80156079576001816060606693605a84607b565b0183607f565b035f607f565b5f8080808063ca11bacc5af1600a575f80fd5b005b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={2: 24743, 18: 24743},
                    code=bytes.fromhex(
                        "60205f600181806157a75af16010555f515f555f805260205f80806157a75afa6011555f516001555f805260205f6001816157a75afa6012555f5160025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af26006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608c565b5f80808080305af1600255602e60016088565b600355005b603a5f6088565b8015608657604a600182035f608c565b5f80808080305af2156082576001606191035f608c565b5f808080305af415608257607e60016077816088565b016001608c565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "60065f604e565b5f555f8080808061add15af2601155601c5f604e565b6001555f80808061add15af460125560325f604e565b6002555f8080808061add15af160135560495f604e565b600355005b5c9056"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606e565b5f80808080305af1600255602e6001606a565b600355005b603a5f606a565b80156068576001816054605a93604e84606a565b0183606e565b035f606e565b5f808080305af46006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "36156081573330036074575b5f3560f81c5f355f5260013603906001908060f1146064578060f21460545760f4146046575b5050333003603b57005b60425f6094565b5f55005b5f918291305af4505f806031565b505f91829182305af2505f806031565b505f91829182305af1505f806031565b607d60015f6098565b600b565b60926001608c5f6094565b015f6098565b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "60065f601d565b5f5560106001601d565b6001555f80808080335af1005b5c9056"  # noqa: E501
                    )
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af16006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 0x5114E2C8, 1: 1},
                    code=bytes.fromhex(
                        "5f8060208180803560e01c60043581835582525af160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "366012575b600b5f6020565b5f5260205ff35b601c6160a75f6024565b6004565b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60106001600a5f6012565b015f6016565b005b5c90565b5d56"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608d565b5f80808080305af1600255602e60016089565b600355005b603a5f6089565b8015608757604a600182035f608d565b5f80808080305af1156083576001606191035f608d565b5f80808080305af115608357607f60016078816089565b016001608d565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "63ca11bacc3314603f575b63ca11bacc3303601657005b60235f35806001555f607f565b5f8080808063ca11bacc5af1600255603a6001607b565b600355005b60465f607b565b80156079576001816060606693605a84607b565b0183607f565b035f607f565b5f8080808063ca11bacc5af1600a575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    storage={2: 24743, 18: 24743},
                    code=bytes.fromhex(
                        "60205f600181806157a75af16010555f515f555f805260205f80806157a75afa6011555f516001555f805260205f6001816157a75afa6012555f5160025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    storage={1: 16, 2: 1, 3: 136},
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af26006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608c565b5f80808080305af1600255602e60016088565b600355005b603a5f6088565b8015608657604a600182035f608c565b5f80808080305af2156082576001606191035f608c565b5f808080305af415608257607e60016077816088565b016001608c565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "60065f604e565b5f555f8080808061add15af2601155601c5f604e565b6001555f80808061add15af460125560325f604e565b6002555f8080808061add15af160135560495f604e565b600355005b5c9056"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606e565b5f80808080305af1600255602e6001606a565b600355005b603a5f606a565b80156068576001816054605a93604e84606a565b0183606e565b035f606e565b5f808080305af46006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "36156081573330036074575b5f3560f81c5f355f5260013603906001908060f1146064578060f21460545760f4146046575b5050333003603b57005b60425f6094565b5f55005b5f918291305af4505f806031565b505f91829182305af2505f806031565b505f91829182305af1505f806031565b607d60015f6098565b600b565b60926001608c5f6094565b015f6098565b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    storage={0: 24743, 1: 24743},
                    code=bytes.fromhex(
                        "60065f601d565b5f5560106001601d565b6001555f80808080335af1005b5c9056"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af16006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 0x6E3A7204, 1: 1},
                    code=bytes.fromhex(
                        "5f8060208180803560e01c60043581835582525af160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "366012575b600b5f6020565b5f5260205ff35b601c6160a75f6024565b6004565b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60106001600a5f6012565b015f6016565b005b5c90565b5d56"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608d565b5f80808080305af1600255602e60016089565b600355005b603a5f6089565b8015608757604a600182035f608d565b5f80808080305af1156083576001606191035f608d565b5f80808080305af115608357607f60016078816089565b016001608d565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "63ca11bacc3314603f575b63ca11bacc3303601657005b60235f35806001555f607f565b5f8080808063ca11bacc5af1600255603a6001607b565b600355005b60465f607b565b80156079576001816060606693605a84607b565b0183607f565b035f607f565b5f8080808063ca11bacc5af1600a575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    storage={2: 24743, 18: 24743},
                    code=bytes.fromhex(
                        "60205f600181806157a75af16010555f515f555f805260205f80806157a75afa6011555f516001555f805260205f6001816157a75afa6012555f5160025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af26006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608c565b5f80808080305af1600255602e60016088565b600355005b603a5f6088565b8015608657604a600182035f608c565b5f80808080305af2156082576001606191035f608c565b5f808080305af415608257607e60016077816088565b016001608c565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "60065f604e565b5f555f8080808061add15af2601155601c5f604e565b6001555f80808061add15af460125560325f604e565b6002555f8080808061add15af160135560495f604e565b600355005b5c9056"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606e565b5f80808080305af1600255602e6001606a565b600355005b603a5f606a565b80156068576001816054605a93604e84606a565b0183606e565b035f606e565b5f808080305af46006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    storage={0: 2},
                    code=bytes.fromhex(
                        "36156081573330036074575b5f3560f81c5f355f5260013603906001908060f1146064578060f21460545760f4146046575b5050333003603b57005b60425f6094565b5f55005b5f918291305af4505f806031565b505f91829182305af2505f806031565b505f91829182305af1505f806031565b607d60015f6098565b600b565b60926001608c5f6094565b015f6098565b005b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_10: Account(
                    storage={0: 24743, 1: 24743},
                    code=bytes.fromhex(
                        "60065f601d565b5f5560106001601d565b6001555f80808080335af1005b5c9056"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af16006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 0xC54B5829, 1: 1},
                    code=bytes.fromhex(
                        "5f8060208180803560e01c60043581835582525af160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "366012575b600b5f6020565b5f5260205ff35b601c6160a75f6024565b6004565b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60106001600a5f6012565b015f6016565b005b5c90565b5d56"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608d565b5f80808080305af1600255602e60016089565b600355005b603a5f6089565b8015608757604a600182035f608d565b5f80808080305af1156083576001606191035f608d565b5f80808080305af115608357607f60016078816089565b016001608d565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "63ca11bacc3314603f575b63ca11bacc3303601657005b60235f35806001555f607f565b5f8080808063ca11bacc5af1600255603a6001607b565b600355005b60465f607b565b80156079576001816060606693605a84607b565b0183607f565b035f607f565b5f8080808063ca11bacc5af1600a575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    storage={2: 24743, 18: 24743},
                    code=bytes.fromhex(
                        "60205f600181806157a75af16010555f515f555f805260205f80806157a75afa6011555f516001555f805260205f6001816157a75afa6012555f5160025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af26006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608c565b5f80808080305af1600255602e60016088565b600355005b603a5f6088565b8015608657604a600182035f608c565b5f80808080305af2156082576001606191035f608c565b5f808080305af415608257607e60016077816088565b016001608c565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "60065f604e565b5f555f8080808061add15af2601155601c5f604e565b6001555f80808061add15af460125560325f604e565b6002555f8080808061add15af160135560495f604e565b600355005b5c9056"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606e565b5f80808080305af1600255602e6001606a565b600355005b603a5f606a565b80156068576001816054605a93604e84606a565b0183606e565b035f606e565b5f808080305af46006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    storage={0: 2},
                    code=bytes.fromhex(
                        "36156081573330036074575b5f3560f81c5f355f5260013603906001908060f1146064578060f21460545760f4146046575b5050333003603b57005b60425f6094565b5f55005b5f918291305af4505f806031565b505f91829182305af2505f806031565b505f91829182305af1505f806031565b607d60015f6098565b600b565b60926001608c5f6094565b015f6098565b005b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_10: Account(
                    storage={0: 24743, 1: 24743},
                    code=bytes.fromhex(
                        "60065f601d565b5f5560106001601d565b6001555f80808080335af1005b5c9056"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af16006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 0xC54B5829, 1: 1},
                    code=bytes.fromhex(
                        "5f8060208180803560e01c60043581835582525af160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 12, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "366012575b600b5f6020565b5f5260205ff35b601c6160a75f6024565b6004565b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60106001600a5f6012565b015f6016565b005b5c90565b5d56"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608d565b5f80808080305af1600255602e60016089565b600355005b603a5f6089565b8015608757604a600182035f608d565b5f80808080305af1156083576001606191035f608d565b5f80808080305af115608357607f60016078816089565b016001608d565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "63ca11bacc3314603f575b63ca11bacc3303601657005b60235f35806001555f607f565b5f8080808063ca11bacc5af1600255603a6001607b565b600355005b60465f607b565b80156079576001816060606693605a84607b565b0183607f565b035f607f565b5f8080808063ca11bacc5af1600a575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    storage={2: 24743, 18: 24743},
                    code=bytes.fromhex(
                        "60205f600181806157a75af16010555f515f555f805260205f80806157a75afa6011555f516001555f805260205f6001816157a75afa6012555f5160025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af26006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608c565b5f80808080305af1600255602e60016088565b600355005b603a5f6088565b8015608657604a600182035f608c565b5f80808080305af2156082576001606191035f608c565b5f808080305af415608257607e60016077816088565b016001608c565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "60065f604e565b5f555f8080808061add15af2601155601c5f604e565b6001555f80808061add15af460125560325f604e565b6002555f8080808061add15af160135560495f604e565b600355005b5c9056"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606e565b5f80808080305af1600255602e6001606a565b600355005b603a5f606a565b80156068576001816054605a93604e84606a565b0183606e565b035f606e565b5f808080305af46006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    storage={0: 2},
                    code=bytes.fromhex(
                        "36156081573330036074575b5f3560f81c5f355f5260013603906001908060f1146064578060f21460545760f4146046575b5050333003603b57005b60425f6094565b5f55005b5f918291305af4505f806031565b505f91829182305af2505f806031565b505f91829182305af1505f806031565b607d60015f6098565b600b565b60926001608c5f6094565b015f6098565b005b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_10: Account(
                    storage={0: 24743, 1: 24743},
                    code=bytes.fromhex(
                        "60065f601d565b5f5560106001601d565b6001555f80808080335af1005b5c9056"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af16006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 0xC54B5829, 1: 1},
                    code=bytes.fromhex(
                        "5f8060208180803560e01c60043581835582525af160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 13, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "366012575b600b5f6020565b5f5260205ff35b601c6160a75f6024565b6004565b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60106001600a5f6012565b015f6016565b005b5c90565b5d56"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608d565b5f80808080305af1600255602e60016089565b600355005b603a5f6089565b8015608757604a600182035f608d565b5f80808080305af1156083576001606191035f608d565b5f80808080305af115608357607f60016078816089565b016001608d565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "63ca11bacc3314603f575b63ca11bacc3303601657005b60235f35806001555f607f565b5f8080808063ca11bacc5af1600255603a6001607b565b600355005b60465f607b565b80156079576001816060606693605a84607b565b0183607f565b035f607f565b5f8080808063ca11bacc5af1600a575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    storage={2: 24743, 18: 24743},
                    code=bytes.fromhex(
                        "60205f600181806157a75af16010555f515f555f805260205f80806157a75afa6011555f516001555f805260205f6001816157a75afa6012555f5160025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af26006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608c565b5f80808080305af1600255602e60016088565b600355005b603a5f6088565b8015608657604a600182035f608c565b5f80808080305af2156082576001606191035f608c565b5f808080305af415608257607e60016077816088565b016001608c565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "60065f604e565b5f555f8080808061add15af2601155601c5f604e565b6001555f80808061add15af460125560325f604e565b6002555f8080808061add15af160135560495f604e565b600355005b5c9056"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606e565b5f80808080305af1600255602e6001606a565b600355005b603a5f606a565b80156068576001816054605a93604e84606a565b0183606e565b035f606e565b5f808080305af46006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    storage={0: 2},
                    code=bytes.fromhex(
                        "36156081573330036074575b5f3560f81c5f355f5260013603906001908060f1146064578060f21460545760f4146046575b5050333003603b57005b60425f6094565b5f55005b5f918291305af4505f806031565b505f91829182305af2505f806031565b505f91829182305af1505f806031565b607d60015f6098565b600b565b60926001608c5f6094565b015f6098565b005b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_10: Account(
                    storage={0: 24743, 1: 24743},
                    code=bytes.fromhex(
                        "60065f601d565b5f5560106001601d565b6001555f80808080335af1005b5c9056"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af16006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 0xC54B5829, 1: 1},
                    code=bytes.fromhex(
                        "5f8060208180803560e01c60043581835582525af160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 14, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "366012575b600b5f6020565b5f5260205ff35b601c6160a75f6024565b6004565b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60106001600a5f6012565b015f6016565b005b5c90565b5d56"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608d565b5f80808080305af1600255602e60016089565b600355005b603a5f6089565b8015608757604a600182035f608d565b5f80808080305af1156083576001606191035f608d565b5f80808080305af115608357607f60016078816089565b016001608d565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "63ca11bacc3314603f575b63ca11bacc3303601657005b60235f35806001555f607f565b5f8080808063ca11bacc5af1600255603a6001607b565b600355005b60465f607b565b80156079576001816060606693605a84607b565b0183607f565b035f607f565b5f8080808063ca11bacc5af1600a575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    storage={2: 24743, 18: 24743},
                    code=bytes.fromhex(
                        "60205f600181806157a75af16010555f515f555f805260205f80806157a75afa6011555f516001555f805260205f6001816157a75afa6012555f5160025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af26006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608c565b5f80808080305af1600255602e60016088565b600355005b603a5f6088565b8015608657604a600182035f608c565b5f80808080305af2156082576001606191035f608c565b5f808080305af415608257607e60016077816088565b016001608c565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "60065f604e565b5f555f8080808061add15af2601155601c5f604e565b6001555f80808061add15af460125560325f604e565b6002555f8080808061add15af160135560495f604e565b600355005b5c9056"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606e565b5f80808080305af1600255602e6001606a565b600355005b603a5f606a565b80156068576001816054605a93604e84606a565b0183606e565b035f606e565b5f808080305af46006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    storage={0: 2},
                    code=bytes.fromhex(
                        "36156081573330036074575b5f3560f81c5f355f5260013603906001908060f1146064578060f21460545760f4146046575b5050333003603b57005b60425f6094565b5f55005b5f918291305af4505f806031565b505f91829182305af2505f806031565b505f91829182305af1505f806031565b607d60015f6098565b600b565b60926001608c5f6094565b015f6098565b005b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_10: Account(
                    storage={0: 24743, 1: 24743},
                    code=bytes.fromhex(
                        "60065f601d565b5f5560106001601d565b6001555f80808080335af1005b5c9056"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af16006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 0xC54B5829, 1: 1},
                    code=bytes.fromhex(
                        "5f8060208180803560e01c60043581835582525af160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "366012575b600b5f6020565b5f5260205ff35b601c6160a75f6024565b6004565b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60106001600a5f6012565b015f6016565b005b5c90565b5d56"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608d565b5f80808080305af1600255602e60016089565b600355005b603a5f6089565b8015608757604a600182035f608d565b5f80808080305af1156083576001606191035f608d565b5f80808080305af115608357607f60016078816089565b016001608d565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "63ca11bacc3314603f575b63ca11bacc3303601657005b60235f35806001555f607f565b5f8080808063ca11bacc5af1600255603a6001607b565b600355005b60465f607b565b80156079576001816060606693605a84607b565b0183607f565b035f607f565b5f8080808063ca11bacc5af1600a575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    storage={2: 24743, 18: 24743},
                    code=bytes.fromhex(
                        "60205f600181806157a75af16010555f515f555f805260205f80806157a75afa6011555f516001555f805260205f6001816157a75afa6012555f5160025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af26006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608c565b5f80808080305af1600255602e60016088565b600355005b603a5f6088565b8015608657604a600182035f608c565b5f80808080305af2156082576001606191035f608c565b5f808080305af415608257607e60016077816088565b016001608c565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "60065f604e565b5f555f8080808061add15af2601155601c5f604e565b6001555f80808061add15af460125560325f604e565b6002555f8080808061add15af160135560495f604e565b600355005b5c9056"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606e565b5f80808080305af1600255602e6001606a565b600355005b603a5f606a565b80156068576001816054605a93604e84606a565b0183606e565b035f606e565b5f808080305af46006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    storage={0: 2},
                    code=bytes.fromhex(
                        "36156081573330036074575b5f3560f81c5f355f5260013603906001908060f1146064578060f21460545760f4146046575b5050333003603b57005b60425f6094565b5f55005b5f918291305af4505f806031565b505f91829182305af2505f806031565b505f91829182305af1505f806031565b607d60015f6098565b600b565b60926001608c5f6094565b015f6098565b005b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_10: Account(
                    storage={0: 24743, 1: 24743},
                    code=bytes.fromhex(
                        "60065f601d565b5f5560106001601d565b6001555f80808080335af1005b5c9056"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af16006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 0xC54B5829, 1: 1},
                    code=bytes.fromhex(
                        "5f8060208180803560e01c60043581835582525af160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "366012575b600b5f6020565b5f5260205ff35b601c6160a75f6024565b6004565b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60106001600a5f6012565b015f6016565b005b5c90565b5d56"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608d565b5f80808080305af1600255602e60016089565b600355005b603a5f6089565b8015608757604a600182035f608d565b5f80808080305af1156083576001606191035f608d565b5f80808080305af115608357607f60016078816089565b016001608d565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "63ca11bacc3314603f575b63ca11bacc3303601657005b60235f35806001555f607f565b5f8080808063ca11bacc5af1600255603a6001607b565b600355005b60465f607b565b80156079576001816060606693605a84607b565b0183607f565b035f607f565b5f8080808063ca11bacc5af1600a575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    storage={2: 24743, 18: 24743},
                    code=bytes.fromhex(
                        "60205f600181806157a75af16010555f515f555f805260205f80806157a75afa6011555f516001555f805260205f6001816157a75afa6012555f5160025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af26006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    storage={1: 6, 2: 1, 3: 63},
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608c565b5f80808080305af1600255602e60016088565b600355005b603a5f6088565b8015608657604a600182035f608c565b5f80808080305af2156082576001606191035f608c565b5f808080305af415608257607e60016077816088565b016001608c565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "60065f604e565b5f555f8080808061add15af2601155601c5f604e565b6001555f80808061add15af460125560325f604e565b6002555f8080808061add15af160135560495f604e565b600355005b5c9056"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606e565b5f80808080305af1600255602e6001606a565b600355005b603a5f606a565b80156068576001816054605a93604e84606a565b0183606e565b035f606e565b5f808080305af46006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "36156081573330036074575b5f3560f81c5f355f5260013603906001908060f1146064578060f21460545760f4146046575b5050333003603b57005b60425f6094565b5f55005b5f918291305af4505f806031565b505f91829182305af2505f806031565b505f91829182305af1505f806031565b607d60015f6098565b600b565b60926001608c5f6094565b015f6098565b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    storage={0: 24743, 1: 24743},
                    code=bytes.fromhex(
                        "60065f601d565b5f5560106001601d565b6001555f80808080335af1005b5c9056"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af16006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 0x7074A486, 1: 1},
                    code=bytes.fromhex(
                        "5f8060208180803560e01c60043581835582525af160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "366012575b600b5f6020565b5f5260205ff35b601c6160a75f6024565b6004565b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60106001600a5f6012565b015f6016565b005b5c90565b5d56"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608d565b5f80808080305af1600255602e60016089565b600355005b603a5f6089565b8015608757604a600182035f608d565b5f80808080305af1156083576001606191035f608d565b5f80808080305af115608357607f60016078816089565b016001608d565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "63ca11bacc3314603f575b63ca11bacc3303601657005b60235f35806001555f607f565b5f8080808063ca11bacc5af1600255603a6001607b565b600355005b60465f607b565b80156079576001816060606693605a84607b565b0183607f565b035f607f565b5f8080808063ca11bacc5af1600a575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    storage={2: 24743, 18: 24743},
                    code=bytes.fromhex(
                        "60205f600181806157a75af16010555f515f555f805260205f80806157a75afa6011555f516001555f805260205f6001816157a75afa6012555f5160025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af26006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608c565b5f80808080305af1600255602e60016088565b600355005b603a5f6088565b8015608657604a600182035f608c565b5f80808080305af2156082576001606191035f608c565b5f808080305af415608257607e60016077816088565b016001608c565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "60065f604e565b5f555f8080808061add15af2601155601c5f604e565b6001555f80808061add15af460125560325f604e565b6002555f8080808061add15af160135560495f604e565b600355005b5c9056"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    storage={1: 16, 2: 1, 3: 136},
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606e565b5f80808080305af1600255602e6001606a565b600355005b603a5f606a565b80156068576001816054605a93604e84606a565b0183606e565b035f606e565b5f808080305af46006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "36156081573330036074575b5f3560f81c5f355f5260013603906001908060f1146064578060f21460545760f4146046575b5050333003603b57005b60425f6094565b5f55005b5f918291305af4505f806031565b505f91829182305af2505f806031565b505f91829182305af1505f806031565b607d60015f6098565b600b565b60926001608c5f6094565b015f6098565b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    storage={0: 24743, 1: 24743},
                    code=bytes.fromhex(
                        "60065f601d565b5f5560106001601d565b6001555f80808080335af1005b5c9056"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af16006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 0xC1C922F1, 1: 1},
                    code=bytes.fromhex(
                        "5f8060208180803560e01c60043581835582525af160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "366012575b600b5f6020565b5f5260205ff35b601c6160a75f6024565b6004565b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60106001600a5f6012565b015f6016565b005b5c90565b5d56"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608d565b5f80808080305af1600255602e60016089565b600355005b603a5f6089565b8015608757604a600182035f608d565b5f80808080305af1156083576001606191035f608d565b5f80808080305af115608357607f60016078816089565b016001608d565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "63ca11bacc3314603f575b63ca11bacc3303601657005b60235f35806001555f607f565b5f8080808063ca11bacc5af1600255603a6001607b565b600355005b60465f607b565b80156079576001816060606693605a84607b565b0183607f565b035f607f565b5f8080808063ca11bacc5af1600a575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    storage={2: 24743, 18: 24743},
                    code=bytes.fromhex(
                        "60205f600181806157a75af16010555f515f555f805260205f80806157a75afa6011555f516001555f805260205f6001816157a75afa6012555f5160025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af26006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608c565b5f80808080305af1600255602e60016088565b600355005b603a5f6088565b8015608657604a600182035f608c565b5f80808080305af2156082576001606191035f608c565b5f808080305af415608257607e60016077816088565b016001608c565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={1: 1, 2: 2, 3: 2, 17: 1, 18: 1, 19: 1},
                    code=bytes.fromhex(
                        "60065f604e565b5f555f8080808061add15af2601155601c5f604e565b6001555f80808061add15af460125560325f604e565b6002555f8080808061add15af160135560495f604e565b600355005b5c9056"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606e565b5f80808080305af1600255602e6001606a565b600355005b603a5f606a565b80156068576001816054605a93604e84606a565b0183606e565b035f606e565b5f808080305af46006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "36156081573330036074575b5f3560f81c5f355f5260013603906001908060f1146064578060f21460545760f4146046575b5050333003603b57005b60425f6094565b5f55005b5f918291305af4505f806031565b505f91829182305af2505f806031565b505f91829182305af1505f806031565b607d60015f6098565b600b565b60926001608c5f6094565b015f6098565b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    storage={0: 24743, 1: 24743},
                    code=bytes.fromhex(
                        "60065f601d565b5f5560106001601d565b6001555f80808080335af1005b5c9056"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af16006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 0x7F9317BD, 1: 1},
                    code=bytes.fromhex(
                        "5f8060208180803560e01c60043581835582525af160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 15, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "366012575b600b5f6020565b5f5260205ff35b601c6160a75f6024565b6004565b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60106001600a5f6012565b015f6016565b005b5c90565b5d56"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608d565b5f80808080305af1600255602e60016089565b600355005b603a5f6089565b8015608757604a600182035f608d565b5f80808080305af1156083576001606191035f608d565b5f80808080305af115608357607f60016078816089565b016001608d565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "63ca11bacc3314603f575b63ca11bacc3303601657005b60235f35806001555f607f565b5f8080808063ca11bacc5af1600255603a6001607b565b600355005b60465f607b565b80156079576001816060606693605a84607b565b0183607f565b035f607f565b5f8080808063ca11bacc5af1600a575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    storage={0: 24743, 1: 24743, 16: 1, 17: 1},
                    code=bytes.fromhex(
                        "60205f600181806157a75af16010555f515f555f805260205f80806157a75afa6011555f516001555f805260205f6001816157a75afa6012555f5160025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af26006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608c565b5f80808080305af1600255602e60016088565b600355005b603a5f6088565b8015608657604a600182035f608c565b5f80808080305af2156082576001606191035f608c565b5f808080305af415608257607e60016077816088565b016001608c565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "60065f604e565b5f555f8080808061add15af2601155601c5f604e565b6001555f80808061add15af460125560325f604e565b6002555f8080808061add15af160135560495f604e565b600355005b5c9056"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606e565b5f80808080305af1600255602e6001606a565b600355005b603a5f606a565b80156068576001816054605a93604e84606a565b0183606e565b035f606e565b5f808080305af46006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "36156081573330036074575b5f3560f81c5f355f5260013603906001908060f1146064578060f21460545760f4146046575b5050333003603b57005b60425f6094565b5f55005b5f918291305af4505f806031565b505f91829182305af2505f806031565b505f91829182305af1505f806031565b607d60015f6098565b600b565b60926001608c5f6094565b015f6098565b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    storage={0: 24743, 1: 24743},
                    code=bytes.fromhex(
                        "60065f601d565b5f5560106001601d565b6001555f80808080335af1005b5c9056"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af16006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 0x5D7935DF, 1: 1},
                    code=bytes.fromhex(
                        "5f8060208180803560e01c60043581835582525af160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "366012575b600b5f6020565b5f5260205ff35b601c6160a75f6024565b6004565b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60106001600a5f6012565b015f6016565b005b5c90565b5d56"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608d565b5f80808080305af1600255602e60016089565b600355005b603a5f6089565b8015608757604a600182035f608d565b5f80808080305af1156083576001606191035f608d565b5f80808080305af115608357607f60016078816089565b016001608d565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "63ca11bacc3314603f575b63ca11bacc3303601657005b60235f35806001555f607f565b5f8080808063ca11bacc5af1600255603a6001607b565b600355005b60465f607b565b80156079576001816060606693605a84607b565b0183607f565b035f607f565b5f8080808063ca11bacc5af1600a575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    storage={2: 24743, 18: 24743},
                    code=bytes.fromhex(
                        "60205f600181806157a75af16010555f515f555f805260205f80806157a75afa6011555f516001555f805260205f6001816157a75afa6012555f5160025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af26006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608c565b5f80808080305af1600255602e60016088565b600355005b603a5f6088565b8015608657604a600182035f608c565b5f80808080305af2156082576001606191035f608c565b5f808080305af415608257607e60016077816088565b016001608c565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "60065f604e565b5f555f8080808061add15af2601155601c5f604e565b6001555f80808061add15af460125560325f604e565b6002555f8080808061add15af160135560495f604e565b600355005b5c9056"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606e565b5f80808080305af1600255602e6001606a565b600355005b603a5f606a565b80156068576001816054605a93604e84606a565b0183606e565b035f606e565b5f808080305af46006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "36156081573330036074575b5f3560f81c5f355f5260013603906001908060f1146064578060f21460545760f4146046575b5050333003603b57005b60425f6094565b5f55005b5f918291305af4505f806031565b505f91829182305af2505f806031565b505f91829182305af1505f806031565b607d60015f6098565b600b565b60926001608c5f6094565b015f6098565b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    storage={0: 24743, 1: 24743},
                    code=bytes.fromhex(
                        "60065f601d565b5f5560106001601d565b6001555f80808080335af1005b5c9056"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    storage={1: 16, 2: 1, 3: 136},
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af16006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={0: 0xEBD141D5, 1: 1},
                    code=bytes.fromhex(
                        "5f8060208180803560e01c60043581835582525af160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "366012575b600b5f6020565b5f5260205ff35b601c6160a75f6024565b6004565b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60106001600a5f6012565b015f6016565b005b5c90565b5d56"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608d565b5f80808080305af1600255602e60016089565b600355005b603a5f6089565b8015608757604a600182035f608d565b5f80808080305af1156083576001606191035f608d565b5f80808080305af115608357607f60016078816089565b016001608d565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "63ca11bacc3314603f575b63ca11bacc3303601657005b60235f35806001555f607f565b5f8080808063ca11bacc5af1600255603a6001607b565b600355005b60465f607b565b80156079576001816060606693605a84607b565b0183607f565b035f607f565b5f8080808063ca11bacc5af1600a575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    storage={2: 24743, 18: 24743},
                    code=bytes.fromhex(
                        "60205f600181806157a75af16010555f515f555f805260205f80806157a75afa6011555f516001555f805260205f6001816157a75afa6012555f5160025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af26006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f608c565b5f80808080305af1600255602e60016088565b600355005b603a5f6088565b8015608657604a600182035f608c565b5f80808080305af2156082576001606191035f608c565b5f808080305af415608257607e60016077816088565b016001608c565b6006565b5f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "60065f604e565b5f555f8080808061add15af2601155601c5f604e565b6001555f80808061add15af460125560325f604e565b6002555f8080808061add15af160135560495f604e565b600355005b5c9056"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606e565b5f80808080305af1600255602e6001606a565b600355005b603a5f606a565b80156068576001816054605a93604e84606a565b0183606e565b035f606e565b5f808080305af46006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "36156081573330036074575b5f3560f81c5f355f5260013603906001908060f1146064578060f21460545760f4146046575b5050333003603b57005b60425f6094565b5f55005b5f918291305af4505f806031565b505f91829182305af2505f806031565b505f91829182305af1505f806031565b607d60015f6098565b600b565b60926001608c5f6094565b015f6098565b005b5c90565b5d56"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    storage={0: 24743, 1: 24743},
                    code=bytes.fromhex(
                        "60065f601d565b5f5560106001601d565b6001555f80808080335af1005b5c9056"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    storage={1: 256, 2: 1, 3: 32896},
                    code=bytes.fromhex(
                        "3033146033575b303303600e57005b601b5f35806001555f606f565b5f80808080305af1600255602e6001606b565b600355005b603a5f606b565b80156069576001816054605a93604e84606b565b0183606f565b035f606f565b5f80808080305af16006575f80fd5b005b5c90565b5d56"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={0: 0xEBD141D5, 1: 1},
                    code=bytes.fromhex(
                        "5f8060208180803560e01c60043581835582525af160015500"
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
        nonce=1,
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
