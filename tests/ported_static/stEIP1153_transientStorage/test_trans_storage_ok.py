"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/Cancun/stEIP1153_transientStorage/transStorageOKFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/Cancun/stEIP1153_transientStorage/transStorageOKFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="sum_16",
        ),
        pytest.param(
            1,
            0,
            0,
            id="callcode_sum_16",
        ),
        pytest.param(
            2,
            0,
            0,
            id="delegate_sum_16",
        ),
        pytest.param(
            3,
            0,
            0,
            id="sum_256",
        ),
        pytest.param(
            4,
            0,
            0,
            id="callback_sum_10",
        ),
        pytest.param(
            5,
            0,
            0,
            id="callback_sum_50",
        ),
        pytest.param(
            6,
            0,
            0,
            id="bin_tree_6",
        ),
        pytest.param(
            7,
            0,
            0,
            id="delegate_bin_tree_6",
        ),
        pytest.param(
            8,
            0,
            0,
            id="inherit_trans",
        ),
        pytest.param(
            9,
            0,
            0,
            id="deep_call",
        ),
        pytest.param(
            10,
            0,
            0,
            id="deep_call",
        ),
        pytest.param(
            11,
            0,
            0,
            id="deep_call",
        ),
        pytest.param(
            12,
            0,
            0,
            id="deep_call",
        ),
        pytest.param(
            13,
            0,
            0,
            id="deep_call",
        ),
        pytest.param(
            14,
            0,
            0,
            id="deep_call",
        ),
        pytest.param(
            15,
            0,
            0,
            id="static_call",
        ),
    ],
)
def test_trans_storage_ok(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    sender = pre.fund_eoa()

    # Source: yul
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
    contract_0 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x33, condition=Op.EQ(Op.CALLER, Op.ADDRESS))
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
        + Op.JUMP,
        nonce=1,
    )
    # Source: yul
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
    contract_1 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x33, condition=Op.EQ(Op.CALLER, Op.ADDRESS))
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
        + Op.JUMP,
        nonce=1,
    )
    # Source: yul
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
    contract_2 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x33, condition=Op.EQ(Op.CALLER, Op.ADDRESS))
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
        + Op.JUMP,
        nonce=1,
    )
    # Source: yul
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
    contract_3 = pre.deploy_contract(
        code=Op.PUSH1[0x6]
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
        + Op.JUMP,
        storage={0: 24743, 1: 24743},
        nonce=1,
    )
    # Source: yul
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
    contract_5 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x33, condition=Op.EQ(Op.CALLER, Op.ADDRESS))
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
                )
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
                )
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
        + Op.JUMP,
        nonce=1,
    )
    # Source: yul
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
    contract_6 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x33, condition=Op.EQ(Op.CALLER, Op.ADDRESS))
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
                )
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
                )
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
        + Op.JUMP,
        nonce=1,
    )
    # Source: yul
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
    contract_7 = pre.deploy_contract(
        code=Op.PUSH1[0x10]
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
        + Op.JUMP,
        nonce=1,
    )
    # Source: yul
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
    contract_9 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x81, condition=Op.ISZERO(Op.CALLDATASIZE))
        + Op.JUMPI(pc=0x74, condition=Op.SUB(Op.ADDRESS, Op.CALLER))
        + Op.JUMPDEST
        + Op.SHR(0xF8, Op.CALLDATALOAD(offset=Op.PUSH0))
        + Op.MSTORE(offset=Op.PUSH0, value=Op.CALLDATALOAD(offset=Op.PUSH0))
        + Op.SUB(Op.CALLDATASIZE, 0x1)
        + Op.SWAP1
        + Op.PUSH1[0x1]
        + Op.SWAP1
        + Op.JUMPI(pc=0x64, condition=Op.EQ(0xF1, Op.DUP1))
        + Op.JUMPI(pc=0x54, condition=Op.EQ(0xF2, Op.DUP1))
        + Op.PUSH1[0xF4]
        + Op.JUMPI(pc=0x46, condition=Op.EQ)
        + Op.JUMPDEST
        + Op.POP * 2
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
        + Op.JUMP,
        nonce=1,
    )
    # Source: yul
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
    contract_10 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x12, condition=Op.CALLDATASIZE)
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
        + Op.JUMP,
        nonce=1,
    )
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x20))
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(address=Op.CALLDATALOAD(offset=0x0), args_size=0x20),
        )
        + Op.STOP,
        nonce=1,
    )
    # Source: yul
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
    contract_4 = pre.deploy_contract(
        code=Op.JUMPI(
            pc=0x6F, condition=Op.EQ(Op.CALLER, Op.PUSH20[contract_3])
        )
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x36, condition=Op.SUB(Op.CALLER, Op.PUSH20[contract_3]))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x43]
        + Op.CALLDATALOAD(offset=Op.PUSH0)
        + Op.SSTORE(key=0x1, value=Op.DUP1)
        + Op.PUSH0
        + Op.JUMP(pc=0xBF)
        + Op.JUMPDEST
        + Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=Op.GAS,
                address=Op.PUSH20[contract_3],
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=Op.PUSH0,
            ),
        )
        + Op.PUSH1[0x6A]
        + Op.PUSH1[0x1]
        + Op.JUMP(pc=0xBB)
        + Op.JUMPDEST
        + Op.PUSH1[0x3]
        + Op.SSTORE
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x76]
        + Op.PUSH0
        + Op.JUMP(pc=0xBB)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0xB9, condition=Op.ISZERO(Op.DUP1))
        + Op.PUSH1[0x1]
        + Op.DUP2
        + Op.PUSH1[0x90]
        + Op.PUSH1[0x96]
        + Op.SWAP4
        + Op.PUSH1[0x8A]
        + Op.DUP5
        + Op.JUMP(pc=0xBB)
        + Op.JUMPDEST
        + Op.ADD
        + Op.DUP4
        + Op.JUMP(pc=0xBF)
        + Op.JUMPDEST
        + Op.SUB
        + Op.PUSH0
        + Op.JUMP(pc=0xBF)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1A,
            condition=Op.CALL(
                gas=Op.GAS,
                address=Op.PUSH20[contract_3],
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
        + Op.JUMP,
        nonce=1,
    )
    # Source: yul
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
    contract_8 = pre.deploy_contract(
        code=Op.PUSH1[0x6]
        + Op.PUSH0
        + Op.JUMP(pc=0x84)
        + Op.JUMPDEST
        + Op.PUSH0
        + Op.SSTORE
        + Op.SSTORE(
            key=0x11,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=Op.PUSH20[contract_7],
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=Op.PUSH0,
            ),
        )
        + Op.PUSH1[0x2E]
        + Op.PUSH0
        + Op.JUMP(pc=0x84)
        + Op.JUMPDEST
        + Op.PUSH1[0x1]
        + Op.SSTORE
        + Op.SSTORE(
            key=0x12,
            value=Op.DELEGATECALL(
                gas=Op.GAS,
                address=Op.PUSH20[contract_7],
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=Op.PUSH0,
            ),
        )
        + Op.PUSH1[0x56]
        + Op.PUSH0
        + Op.JUMP(pc=0x84)
        + Op.JUMPDEST
        + Op.PUSH1[0x2]
        + Op.SSTORE
        + Op.SSTORE(
            key=0x13,
            value=Op.CALL(
                gas=Op.GAS,
                address=Op.PUSH20[contract_7],
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=Op.PUSH0,
            ),
        )
        + Op.PUSH1[0x7F]
        + Op.PUSH0
        + Op.JUMP(pc=0x84)
        + Op.JUMPDEST
        + Op.PUSH1[0x3]
        + Op.SSTORE
        + Op.STOP
        + Op.JUMPDEST
        + Op.TLOAD
        + Op.SWAP1
        + Op.JUMP,
        storage={0: 24743},
        nonce=1,
    )
    # Source: yul
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
    contract_11 = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x10,
            value=Op.CALL(
                gas=Op.GAS,
                address=contract_10,
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
                address=contract_10,
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
                address=contract_10,
                args_offset=Op.DUP2,
                args_size=0x1,
                ret_offset=Op.PUSH0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=Op.PUSH0))
        + Op.STOP,
        storage={2: 24743, 18: 24743},
        nonce=1,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: contract_0, 1: 1}),
                contract_0: Account(storage={1: 16, 2: 1, 3: 136}),
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: contract_1, 1: 1}),
                contract_1: Account(storage={1: 16, 2: 1, 3: 136}),
            },
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: contract_2, 1: 1}),
                contract_2: Account(storage={1: 16, 2: 1, 3: 136}),
            },
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: contract_0, 1: 1}),
                contract_0: Account(storage={1: 256, 2: 1, 3: 32896}),
            },
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: contract_4, 1: 1}),
                contract_4: Account(storage={1: 10, 2: 1, 3: 55}),
                contract_3: Account(storage={0: 0, 1: 0}),
            },
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: contract_4, 1: 1}),
                contract_4: Account(storage={1: 50, 2: 1, 3: 1275}),
                contract_3: Account(storage={0: 0, 1: 0}),
            },
        },
        {
            "indexes": {"data": [6], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: contract_5, 1: 1}),
                contract_5: Account(storage={1: 6, 2: 1, 3: 63}),
            },
        },
        {
            "indexes": {"data": [7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: contract_6, 1: 1}),
                contract_6: Account(storage={1: 6, 2: 1, 3: 63}),
            },
        },
        {
            "indexes": {"data": [8], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: contract_8, 1: 1}),
                contract_8: Account(
                    storage={0: 0, 1: 1, 2: 2, 3: 2, 17: 1, 18: 1, 19: 1},
                ),
            },
        },
        {
            "indexes": {
                "data": [9, 10, 11, 12, 13, 14],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: contract_9, 1: 1}),
                contract_9: Account(storage={0: 2}),
            },
        },
        {
            "indexes": {"data": [15], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: contract_11, 1: 1}),
                contract_11: Account(
                    storage={0: 24743, 1: 24743, 2: 0, 16: 1, 17: 1, 18: 0},
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(contract_0, left_padding=True) + Hash(0x10),
        Hash(contract_1, left_padding=True) + Hash(0x10),
        Hash(contract_2, left_padding=True) + Hash(0x10),
        Hash(contract_0, left_padding=True) + Hash(0x100),
        Hash(contract_4, left_padding=True) + Hash(0xA),
        Hash(contract_4, left_padding=True) + Hash(0x32),
        Hash(contract_5, left_padding=True) + Hash(0x6),
        Hash(contract_6, left_padding=True) + Hash(0x6),
        Hash(contract_8, left_padding=True),
        Hash(contract_9, left_padding=True)
        + Hash(
            0xF2F4F1F2F4F1F2F4F1F2F4F1F2F4F1F2F4F1F2F4F1F2F4F1F2F4F1F2F4F1F1F1
        ),
        Hash(contract_9, left_padding=True)
        + Hash(
            0xF1F1F1F1F2F2F2F2F4F4F4F4F1F1F1F1F2F2F2F2F4F4F4F4F1F1F1F1F2F2F2F2
        ),
        Hash(contract_9, left_padding=True)
        + Hash(
            0xF1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1
        ),
        Hash(contract_9, left_padding=True)
        + Hash(
            0xF1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1
        ),
        Hash(contract_9, left_padding=True)
        + Hash(
            0xF2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2
        ),
        Hash(contract_9, left_padding=True)
        + Hash(
            0xF4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4
        ),
        Hash(contract_11, left_padding=True),
    ]
    tx_gas = [16777216]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
