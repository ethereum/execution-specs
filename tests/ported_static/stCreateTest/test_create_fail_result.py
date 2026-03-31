"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
state_tests/stCreateTest/createFailResultFiller.yml
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
    ["state_tests/stCreateTest/createFailResultFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="CREATE--OOG",
        ),
        pytest.param(
            1,
            0,
            0,
            id="CREATE2-OOG",
        ),
        pytest.param(
            2,
            0,
            0,
            id="CREATE--GOOD",
        ),
        pytest.param(
            3,
            0,
            0,
            id="CREATE2-GOOD",
        ),
        pytest.param(
            4,
            0,
            0,
            id="CREATE--BAD",
        ),
        pytest.param(
            5,
            0,
            0,
            id="CREATE2-BAD",
        ),
        pytest.param(
            6,
            0,
            0,
            id="CREATE2-BOOM",
        ),
        pytest.param(
            7,
            0,
            0,
            id="CREATE2-BAD-BOOM",
        ),
        pytest.param(
            8,
            0,
            0,
            id="CREATE--BOOM",
        ),
        pytest.param(
            9,
            0,
            0,
            id="CREATE--BAD-BOOM",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_fail_result(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x000000000000000000000000000000000000DA7A)
    contract_1 = Address(0x0000000000000000000000000000000000000BAD)
    contract_2 = Address(0x000000000000000000000000000000000000600D)
    contract_3 = Address(0x0000000000000000000000000000000000C0DEF0)
    contract_4 = Address(0x0000000000000000000000000000000000C0DEF5)
    contract_5 = Address(0x0000000000000000000000000000000000C0DEFF)
    contract_6 = Address(0xBB0237AB04970E3CF3E813C02064662ADC89336B)
    contract_7 = Address(0x13C950F8740FFAEA1869A88D70B029E8B0C9A8DA)
    contract_8 = Address(0x0000000000000000000000000000000000C0DEEE)
    contract_9 = Address(0xF9D1EA8EAB6963659EE85B3E0B4D8A57E7EDBA2B)
    contract_10 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
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
    # berlin
    # {
    #     mstore(0x00, 0xDEADBEEF)
    #     mstore(0x20, 0x60A7)
    #
    #     // Return with two words of data
    #     return(0, 0x40)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0xDEADBEEF)
        + Op.MSTORE(offset=0x20, value=0x60A7)
        + Op.RETURN(offset=0x0, size=0x40),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x000000000000000000000000000000000000DA7A),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    mstore(0, 0x0BAD0BAD0BAD)
    #    revert(0, 0x20)
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0xBAD0BAD0BAD)
        + Op.REVERT(offset=0x0, size=0x20),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000000BAD),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    mstore(0, 0x600D)
    #    return(0, 0x20)
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x600D)
        + Op.RETURN(offset=0x0, size=0x20),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x000000000000000000000000000000000000600D),  # noqa: E501
    )
    # Source: yul
    # berlin
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
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
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
            dest_offset=0x200, offset=0x0, size=Op.RETURNDATASIZE
        )
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x200))
        + Op.SSTORE(key=0x3, value=Op.MLOAD(offset=0x220))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DEF0),  # noqa: E501
    )
    # Source: yul
    # berlin
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
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
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
            dest_offset=0x200, offset=0x0, size=Op.RETURNDATASIZE
        )
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x200))
        + Op.SSTORE(key=0x3, value=Op.MLOAD(offset=0x220))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DEF5),  # noqa: E501
    )
    # Source: yul
    # berlin
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
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
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
            dest_offset=0x200, offset=0x0, size=Op.RETURNDATASIZE
        )
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x200))
        + Op.SSTORE(key=0x3, value=Op.MLOAD(offset=0x220))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DEFF),  # noqa: E501
    )
    # Source: raw
    # 0x600100
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x1] + Op.STOP,
        balance=24589,
        nonce=1,
        address=Address(0xBB0237AB04970E3CF3E813C02064662ADC89336B),  # noqa: E501
    )
    # Source: raw
    # 0x600100
    contract_7 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x1] + Op.STOP,
        balance=24589,
        nonce=1,
        address=Address(0x13C950F8740FFAEA1869A88D70B029E8B0C9A8DA),  # noqa: E501
    )
    # Source: yul
    # berlin
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
    contract_8 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
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
            dest_offset=0x200, offset=0x0, size=Op.RETURNDATASIZE
        )
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x200))
        + Op.SSTORE(key=0x3, value=Op.MLOAD(offset=0x220))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000C0DEEE),  # noqa: E501
    )
    # Source: raw
    # 0x600100
    contract_9 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x1] + Op.STOP,
        balance=24589,
        nonce=1,
        address=Address(0xF9D1EA8EAB6963659EE85B3E0B4D8A57E7EDBA2B),  # noqa: E501
    )
    # Source: yul
    # berlin
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
    # ... (14 more lines)
    contract_10 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x20]
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
        + Op.JUMP(pc=0x3F),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_10: Account(
                    storage={
                        0: 0,
                        1: 0,
                        2: 0,
                        16: 1,
                        17: 64,
                        18: 0xDEADBEEF,
                        19: 24743,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_3: Account(
                    storage={
                        0: 0xB44F2C88D3D4283CD1E54E418C4FF7E6A6C73202,
                        1: 0,
                        2: 0,
                        3: 0,
                        16: 1,
                        17: 64,
                        18: 0xDEADBEEF,
                        19: 24743,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_4: Account(
                    storage={
                        0: 0x65EE26A034447B6AC64ABDCA1CCCB7B747E4A231,
                        1: 0,
                        2: 0,
                        3: 0,
                        16: 1,
                        17: 64,
                        18: 0xDEADBEEF,
                        19: 24743,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_3: Account(
                    storage={
                        0: 0,
                        1: 32,
                        2: 0xBAD0BAD0BAD,
                        16: 1,
                        17: 64,
                        18: 0xDEADBEEF,
                        19: 24743,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_4: Account(
                    storage={
                        0: 0,
                        1: 32,
                        2: 0xBAD0BAD0BAD,
                        16: 1,
                        17: 64,
                        18: 0xDEADBEEF,
                        19: 24743,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [6], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_5: Account(
                    storage={
                        0: 0,
                        1: 0,
                        16: 1,
                        17: 64,
                        18: 0xDEADBEEF,
                        19: 24743,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_5: Account(
                    storage={
                        0: 0,
                        1: 0,
                        16: 1,
                        17: 64,
                        18: 0xDEADBEEF,
                        19: 24743,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [8], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_8: Account(
                    storage={
                        0: 0,
                        1: 0,
                        16: 1,
                        17: 64,
                        18: 0xDEADBEEF,
                        19: 24743,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [9], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_8: Account(
                    storage={
                        0: 0,
                        1: 0,
                        16: 1,
                        17: 64,
                        18: 0xDEADBEEF,
                        19: 24743,
                    },
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0x6),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0x6),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(contract_2, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(contract_2, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(contract_1, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(contract_1, left_padding=True),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(contract_2, left_padding=True),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(contract_1, left_padding=True),
        Bytes("1a8451e6") + Hash(0xEE) + Hash(contract_2, left_padding=True),
        Bytes("1a8451e6") + Hash(0xEE) + Hash(contract_1, left_padding=True),
    ]
    tx_gas = [16777216]

    tx = Transaction(
        sender=sender,
        to=contract_10,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
