"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stBadOpcode/operationDiffGasFiller.yml
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
    ["tests/static/state_tests/stBadOpcode/operationDiffGasFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "048071d300000000000000000000000000000000000000000000000000000000000000f200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2700}
                )
            },
        ),
        (
            "048071d300000000000000000000000000000000000000000000000000000000000000f100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2700}
                )
            },
        ),
        (
            "048071d300000000000000000000000000000000000000000000000000000000000000f500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000c0def5"): Account(
                    storage={0: 0x1C1BD7A2F25CA2F4577AD12388656BC147F96DAB}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 54300}
                ),
            },
        ),
        (
            "048071d300000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000c0def0"): Account(
                    storage={0: 0xB44F2C88D3D4283CD1E54E418C4FF7E6A6C73202}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 54200}
                ),
            },
        ),
        (
            "048071d300000000000000000000000000000000000000000000000000000000000000f400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2700}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000003b00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2800}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000005100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 9200}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000005300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 9200}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000005200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 9200}
                )
            },
        ),
        (
            "048071d3000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 18400}
                )
            },
        ),
        (
            "048071d300000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2700}
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
def test_operation_diff_gas(
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
    #    mstore(0, 0xDEADBEEF)
    #    return(0, 0x100)
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0xDEADBEEF)
            + Op.RETURN(offset=0x0, size=0x100)
        ),
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
    #    let useless := mload(0xBEEF)
    # }
    pre.deploy_contract(
        code=Op.MLOAD(offset=0xBEEF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0de51"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    mstore(0xBEEF, 0xFF)
    # }
    pre.deploy_contract(
        code=Op.MSTORE(offset=0xBEEF, value=0xFF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0de52"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    mstore8(0xBEEF, 0xFF)
    # }
    pre.deploy_contract(
        code=Op.MSTORE8(offset=0xBEEF, value=0xFF) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000c0de53"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    sstore(0,create(0, 0, 0x200))
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CREATE(value=Op.DUP1, offset=0x0, size=0x200),
            )
            + Op.STOP
        ),
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
    #    sstore(0,create2(0, 0, 0x200, 0x5A17))
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CREATE2(
                    value=Op.DUP1,
                    offset=0x0,
                    size=0x200,
                    salt=0x5A17,
                ),
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
    #   // Run the operation with gasAmt, gasAmt+gasDiff, gasAmt+2*gasDiff, etc.  # noqa: E501
    #   let gasAmt := calldataload(0x24)
    #   let gasDiff := calldataload(0x44)
    #   let addr := add(0xC0DE00, calldataload(0x04))
    #   let result := 0
    #
    #   for { } eq(result, 0) { } {     // Until the operation is successful
    #      result := call(gasAmt, addr, 0, 0, 0, 0, 0)
    #      gasAmt := add(gasAmt, gasDiff)
    #   }
    #   sstore(0, sub(gasAmt, gasDiff))
    # }
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x44)
            + Op.CALLDATALOAD(offset=0x24)
            + Op.ADD(Op.CALLDATALOAD(offset=0x4), 0xC0DE00)
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x1C, condition=Op.EQ)
            + Op.POP
            + Op.SSTORE(key=0x0, value=Op.SUB)
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.DUP4
            + Op.CALL(
                gas=Op.DUP10,
                address=Op.DUP8,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=Op.DUP2,
            )
            + Op.SWAP4
            + Op.ADD
            + Op.SWAP3
            + Op.JUMP(pc=0x11)
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
