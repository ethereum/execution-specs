"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stCreateTest/createFailResultFiller.yml
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stCreateTest/createFailResultFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ee0000000000000000000000000000000000000000000000000000000000000bad",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000c0deee"): Account(
                    storage={16: 1, 17: 64, 18: 0xDEADBEEF, 19: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1, 16: 1, 17: 64, 18: 0xDEADBEEF, 19: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000bad",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000c0def0"): Account(
                    storage={
                        1: 32,
                        2: 0xBAD0BAD0BAD,
                        16: 1,
                        17: 64,
                        18: 0xDEADBEEF,
                        19: 24743,
                    }
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1, 16: 1, 17: 64, 18: 0xDEADBEEF, 19: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ee000000000000000000000000000000000000000000000000000000000000600d",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000c0deee"): Account(
                    storage={16: 1, 17: 64, 18: 0xDEADBEEF, 19: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1, 16: 1, 17: 64, 18: 0xDEADBEEF, 19: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f0000000000000000000000000000000000000000000000000000000000000600d",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000c0def0"): Account(
                    storage={
                        0: 0xB44F2C88D3D4283CD1E54E418C4FF7E6A6C73202,
                        16: 1,
                        17: 64,
                        18: 0xDEADBEEF,
                        19: 24743,
                    }
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1, 16: 1, 17: 64, 18: 0xDEADBEEF, 19: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000006",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={16: 1, 17: 64, 18: 0xDEADBEEF, 19: 24743}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff0000000000000000000000000000000000000000000000000000000000000bad",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000c0deff"): Account(
                    storage={16: 1, 17: 64, 18: 0xDEADBEEF, 19: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1, 16: 1, 17: 64, 18: 0xDEADBEEF, 19: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000bad",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000c0def5"): Account(
                    storage={
                        1: 32,
                        2: 0xBAD0BAD0BAD,
                        16: 1,
                        17: 64,
                        18: 0xDEADBEEF,
                        19: 24743,
                    }
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1, 16: 1, 17: 64, 18: 0xDEADBEEF, 19: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000600d",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000c0deff"): Account(
                    storage={16: 1, 17: 64, 18: 0xDEADBEEF, 19: 24743}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1, 16: 1, 17: 64, 18: 0xDEADBEEF, 19: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f5000000000000000000000000000000000000000000000000000000000000600d",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000c0def5"): Account(
                    storage={
                        0: 0x65EE26A034447B6AC64ABDCA1CCCB7B747E4A231,
                        16: 1,
                        17: 64,
                        18: 0xDEADBEEF,
                        19: 24743,
                    }
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 1, 16: 1, 17: 64, 18: 0xDEADBEEF, 19: 24743}
                ),
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000006",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={16: 1, 17: 64, 18: 0xDEADBEEF, 19: 24743}
                )
            },
        ),
    ],
    ids=[
        "case0",
        "case1",
        "case2",
        "case3",
        "case4",
        "case5",
        "case6",
        "case7",
        "case8",
        "case9",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_fail_result(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
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
    #    mstore(0, 0x0BAD0BAD0BAD)
    #    revert(0, 0x20)
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0xBAD0BAD0BAD)
            + Op.REVERT(offset=0x0, size=0x20)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000000bad"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    mstore(0, 0x600D)
    #    return(0, 0x20)
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x600D)
            + Op.RETURN(offset=0x0, size=0x20)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x000000000000000000000000000000000000600d"),  # noqa: E501
    )
    # Source: Yul
    # {
    #     mstore(0x00, 0xDEADBEEF)
    #     mstore(0x20, 0x60A7)
    #
    #     // Return with two words of data
    #     return(0, 0x40)
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0xDEADBEEF)
            + Op.MSTORE(offset=0x20, value=0x60A7)
            + Op.RETURN(offset=0x0, size=0x40)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x000000000000000000000000000000000000da7a"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    // Before the main call, call DA7A to fill up the return buffer
    #    sstore(0x10, call(gas(), 0xDA7A, 0, 0, 0, 0x100, 0x40))
    #    sstore(0x11, returndatasize())
    #    sstore(0x12, mload(0x100))
    #    sstore(0x13, mload(0x120))
    #
    #    // Read the constructor code from the appropriate contract
    #    let srcAddr := calldataload(0)   // either 600D or BAD
    #
    #    let codeSize := extcodesize(srcAddr)
    #    extcodecopy(srcAddr, 0, 0, codeSize)
    #
    #    // Create
    #    sstore(0,create(0, 0, codeSize))
    #
    #    // If we have a returned buffer, see what it is
    #    sstore(1,returndatasize())
    #    returndatacopy(0x200, 0, returndatasize())
    #    sstore(2, mload(0x200))
    #    sstore(3, mload(0x220))
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x10,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=0xDA7A,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=0x0,
                    ret_offset=0x100,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x11, value=Op.RETURNDATASIZE)
            + Op.SSTORE(key=0x12, value=Op.MLOAD(offset=0x100))
            + Op.SSTORE(key=0x13, value=Op.MLOAD(offset=0x120))
            + Op.PUSH1[0x0]
            + Op.CALLDATALOAD(offset=Op.DUP1)
            + Op.DUP2
            + Op.EXTCODESIZE(address=Op.DUP2)
            + Op.SWAP3
            + Op.DUP4
            + Op.SWAP3
            + Op.EXTCODECOPY
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.SSTORE(key=0x0, value=Op.CREATE)
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.RETURNDATACOPY(
                dest_offset=0x200,
                offset=0x0,
                size=Op.RETURNDATASIZE,
            )
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x200))
            + Op.SSTORE(key=0x3, value=Op.MLOAD(offset=0x220))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0deee"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    // Before the main call, call DA7A to fill up the return buffer
    #    sstore(0x10, call(gas(), 0xDA7A, 0, 0, 0, 0x100, 0x40))
    #    sstore(0x11, returndatasize())
    #    sstore(0x12, mload(0x100))
    #    sstore(0x13, mload(0x120))
    #
    #
    #    // Read the constructor code from the appropriate contract
    #    let srcAddr := calldataload(0)   // either 600D or BAD
    #
    #    let codeSize := extcodesize(srcAddr)
    #    extcodecopy(srcAddr, 0, 0, codeSize)
    #
    #    // Create
    #    sstore(0,create(0, 0, codeSize))
    #
    #    // If we have a returned buffer, see what it is
    #    sstore(1,returndatasize())
    #    returndatacopy(0x200, 0, returndatasize())
    #    sstore(2, mload(0x200))
    #    sstore(3, mload(0x220))
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x10,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=0xDA7A,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=0x0,
                    ret_offset=0x100,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x11, value=Op.RETURNDATASIZE)
            + Op.SSTORE(key=0x12, value=Op.MLOAD(offset=0x100))
            + Op.SSTORE(key=0x13, value=Op.MLOAD(offset=0x120))
            + Op.PUSH1[0x0]
            + Op.CALLDATALOAD(offset=Op.DUP1)
            + Op.DUP2
            + Op.EXTCODESIZE(address=Op.DUP2)
            + Op.SWAP3
            + Op.DUP4
            + Op.SWAP3
            + Op.EXTCODECOPY
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.SSTORE(key=0x0, value=Op.CREATE)
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.RETURNDATACOPY(
                dest_offset=0x200,
                offset=0x0,
                size=Op.RETURNDATASIZE,
            )
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x200))
            + Op.SSTORE(key=0x3, value=Op.MLOAD(offset=0x220))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0def0"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    // Before the main call, call DA7A to fill up the return buffer
    #    sstore(0x10, call(gas(), 0xDA7A, 0, 0, 0, 0x100, 0x40))
    #    sstore(0x11, returndatasize())
    #    sstore(0x12, mload(0x100))
    #    sstore(0x13, mload(0x120))
    #
    #    // Read the constructor code from the appropriate contract
    #    let srcAddr := calldataload(0)   // either 600D or BAD
    #
    #    let codeSize := extcodesize(srcAddr)
    #    extcodecopy(srcAddr, 0, 0, codeSize)
    #
    #    // Create
    #    sstore(0,create2(0, 0, codeSize, 0x5A17))
    #
    #    // If we have a returned buffer, see what it is
    #    sstore(1,returndatasize())
    #    returndatacopy(0x200, 0, returndatasize())
    #    sstore(2, mload(0x200))
    #    sstore(3, mload(0x220))
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x10,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=0xDA7A,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=0x0,
                    ret_offset=0x100,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x11, value=Op.RETURNDATASIZE)
            + Op.SSTORE(key=0x12, value=Op.MLOAD(offset=0x100))
            + Op.SSTORE(key=0x13, value=Op.MLOAD(offset=0x120))
            + Op.PUSH2[0x5A17]
            + Op.PUSH1[0x0]
            + Op.CALLDATALOAD(offset=Op.DUP1)
            + Op.DUP2
            + Op.EXTCODESIZE(address=Op.DUP2)
            + Op.SWAP3
            + Op.DUP4
            + Op.SWAP3
            + Op.EXTCODECOPY
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.SSTORE(key=0x0, value=Op.CREATE2)
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.RETURNDATACOPY(
                dest_offset=0x200,
                offset=0x0,
                size=Op.RETURNDATASIZE,
            )
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x200))
            + Op.SSTORE(key=0x3, value=Op.MLOAD(offset=0x220))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0def5"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    // Before the main call, call DA7A to fill up the return buffer
    #    sstore(0x10, call(gas(), 0xDA7A, 0, 0, 0, 0x100, 0x40))
    #    sstore(0x11, returndatasize())
    #    sstore(0x12, mload(0x100))
    #    sstore(0x13, mload(0x120))
    #
    #    // Read the constructor code from the appropriate contract
    #    let srcAddr := calldataload(0)   // either 600D or BAD
    #
    #    let codeSize := extcodesize(srcAddr)
    #    extcodecopy(srcAddr, 0, 0, codeSize)
    #
    #    // Create
    #    sstore(0,create2(0, 0, codeSize, 0xBAD05A17))
    #
    #    // If we have a returned buffer, see what it is
    #    sstore(1,returndatasize())
    #    returndatacopy(0x200, 0, returndatasize())
    #    sstore(2, mload(0x200))
    #    sstore(3, mload(0x220))
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x10,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=0xDA7A,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=0x0,
                    ret_offset=0x100,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x11, value=Op.RETURNDATASIZE)
            + Op.SSTORE(key=0x12, value=Op.MLOAD(offset=0x100))
            + Op.SSTORE(key=0x13, value=Op.MLOAD(offset=0x120))
            + Op.PUSH4[0xBAD05A17]
            + Op.PUSH1[0x0]
            + Op.CALLDATALOAD(offset=Op.DUP1)
            + Op.DUP2
            + Op.EXTCODESIZE(address=Op.DUP2)
            + Op.SWAP3
            + Op.DUP4
            + Op.SWAP3
            + Op.EXTCODECOPY
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.SSTORE(key=0x0, value=Op.CREATE2)
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.RETURNDATACOPY(
                dest_offset=0x200,
                offset=0x0,
                size=Op.RETURNDATASIZE,
            )
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x200))
            + Op.SSTORE(key=0x3, value=Op.MLOAD(offset=0x220))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0deff"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.PUSH1[0x1] + Op.STOP,
        balance=0x600D,
        address=Address("0x13c950f8740ffaea1869a88d70b029e8b0c9a8da"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.PUSH1[0x1] + Op.STOP,
        balance=0x600D,
        address=Address("0xbb0237ab04970e3cf3e813c02064662adc89336b"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   // The operation to run
    #   // F0 - CREATE
    #   // F5 - CREATE2
    #   let oper := calldataload(0x04)
    #
    #   // The condition for it
    #   // 0x0006 - OUT OF GAS
    #   // 0x0BAD - REVERT with data
    #   // 0x600D - Success
    #   let cond := calldataload(0x24)
    #   let addr := add(0xC0DE00, oper)
    #
    #
    #
    #   // Before the main call, call DA7A to fill up the return buffer
    #   sstore(0x10, call(gas(), 0xDA7A, 0, 0, 0, 0x100, 0x40))
    #   sstore(0x11, returndatasize())
    #   sstore(0x12, mload(0x100))
    #   sstore(0x13, mload(0x120))
    #
    #
    #   let gasAmt := gas()
    #
    #   // Out Of Gas, CREATE[2] always costs more than 32k in gas
    #   // but we need to also pay for the four SSTOREs that verify DA7A was
    #   // called correctly
    #   if eq(cond,0x0006) { gasAmt := add(30000,mul(22100,4)) }
    #
    #   // Send the condition to the contract we call so it'll know whether
    # ... (13 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.PUSH1[0x20]
            + Op.PUSH2[0x200]
            + Op.DUP2
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.ADD(Op.CALLDATALOAD(offset=0x4), 0xC0DE00)
            + Op.CALLDATALOAD(offset=0x24)
            + Op.SSTORE(
                key=0x10,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=0xDA7A,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP5,
                    ret_offset=0x100,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x11, value=Op.RETURNDATASIZE)
            + Op.SSTORE(key=0x12, value=Op.MLOAD(offset=0x100))
            + Op.SSTORE(key=0x13, value=Op.MLOAD(offset=0x120))
            + Op.GAS
            + Op.SWAP1
            + Op.JUMPI(pc=0x52, condition=Op.EQ(Op.DUP2, 0x6))
            + Op.JUMPDEST
            + Op.DUP4
            + Op.MSTORE
            + Op.SSTORE(key=0x0, value=Op.CALL)
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x200))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH3[0x1CE80]
            + Op.SWAP2
            + Op.POP
            + Op.JUMP(pc=0x3F)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.PUSH1[0x1] + Op.STOP,
        balance=0x600D,
        address=Address("0xf9d1ea8eab6963659ee85b3e0b4d8a57e7edba2b"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        nonce=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
