"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stBadOpcode/measureGasFiller.yml
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
    ["tests/static/state_tests/stBadOpcode/measureGasFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000f2",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 144}
                )
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000f1",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 144}
                )
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000f5",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 32193}
                )
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000f0",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 32089}
                )
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000f4",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 141}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000003b",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 221}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000051",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 8110}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000053",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 8113}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000052",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 8113}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000020",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 18348}
                )
            },
        ),
        (
            "693c613900000000000000000000000000000000000000000000000000000000000000fa",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 141}
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
        "case10",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_measure_gas(
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
    #    stop()
    # }
    pre.deploy_contract(
        code=bytes.fromhex("00"),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x000000000000000000000000000000000000ca11"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    let useless := keccak256(0,0xBEEF)
    # }
    pre.deploy_contract(
        code=Op.SHA3(offset=0x0, size=0xBEEF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0de20"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   let addr := 0xCA11
    #   extcodecopy(addr, 0, 0, extcodesize(addr))
    # }
    pre.deploy_contract(
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
    #    let useless := mload(0xB000)
    # }
    pre.deploy_contract(
        code=Op.MLOAD(offset=0xB000) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0de51"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    mstore(0xB000, 0xFF)
    # }
    pre.deploy_contract(
        code=Op.MSTORE(offset=0xB000, value=0xFF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0de52"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    mstore8(0xB000, 0xFF)
    # }
    pre.deploy_contract(
        code=Op.MSTORE8(offset=0xB000, value=0xFF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0de53"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    pop(create(0, 0, 0x200))
    # }
    pre.deploy_contract(
        code=Op.CREATE(value=Op.DUP1, offset=0x0, size=0x200) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0def0"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    let retval := call(gas(), 0xCA11, 0, 0, 0x100, 0, 0x100)
    # }
    pre.deploy_contract(
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
    pre.deploy_contract(
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
    pre.deploy_contract(
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
    #    // SALT needs to be different each time
    #    pop(create2(0, 0, 0x200, add(0x5A17, gas())))
    # }
    pre.deploy_contract(
        code=(
            Op.CREATE2(
                value=Op.DUP1,
                offset=0x0,
                size=0x200,
                salt=Op.ADD(0x5A17, Op.GAS),
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
    pre.deploy_contract(
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
    #   // Find the operation's cost in gas
    #   let min :=     0
    #   let max := 60000
    #   let addr := add(0xC0DE00, calldataload(0x04))
    #
    #   for { } gt(sub(max,min), 1) { } { // Until we get the exact figure
    #      let middle := div(add(min,max),2)
    #      let result := call(middle, addr, 0, 0, 0, 0, 0)
    #      if eq(result, 0) { min := middle }
    #      if eq(result, 1) { max := middle }
    #   }
    #   sstore(0, max)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.PUSH2[0xEA60]
            + Op.ADD(Op.CALLDATALOAD(offset=0x4), 0xC0DE00)
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x1C, condition=Op.GT(Op.SUB(Op.DUP5, Op.DUP2), 0x1))
            + Op.SSTORE(key=0x0, value=Op.DUP3)
            + Op.STOP
            + Op.JUMPDEST
            + Op.DIV(Op.ADD(Op.DUP3, Op.DUP4), 0x2)
            + Op.CALL(
                gas=Op.DUP7,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
            + Op.JUMPI(pc=0x44, condition=Op.ISZERO(Op.DUP1))
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.JUMPI(pc=0x3D, condition=Op.EQ)
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMP(pc=0xD)
            + Op.JUMPDEST
            + Op.SWAP3
            + Op.POP
            + Op.CODESIZE
            + Op.JUMP(pc=0x38)
            + Op.JUMPDEST
            + Op.SWAP1
            + Op.SWAP2
            + Op.POP
            + Op.DUP2
            + Op.SWAP1
            + Op.JUMP(pc=0x31)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
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
