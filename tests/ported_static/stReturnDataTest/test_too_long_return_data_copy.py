"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
state_tests/stReturnDataTest/tooLongReturnDataCopyFiller.yml
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
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stReturnDataTest/tooLongReturnDataCopyFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="success",
        ),
        pytest.param(
            1,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            2,
            0,
            0,
            id="success",
        ),
        pytest.param(
            3,
            0,
            0,
            id="success",
        ),
        pytest.param(
            4,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            5,
            0,
            0,
            id="success",
        ),
        pytest.param(
            6,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            7,
            0,
            0,
            id="success",
        ),
        pytest.param(
            8,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            9,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            10,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            11,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            12,
            0,
            0,
            id="success",
        ),
        pytest.param(
            13,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            14,
            0,
            0,
            id="success",
        ),
        pytest.param(
            15,
            0,
            0,
            id="success",
        ),
        pytest.param(
            16,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            17,
            0,
            0,
            id="success",
        ),
        pytest.param(
            18,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            19,
            0,
            0,
            id="success",
        ),
        pytest.param(
            20,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            21,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            22,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            23,
            0,
            0,
            id="fail",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_too_long_return_data_copy(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
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
    # berlin
    # {
    #    // How many bytes to return
    #    let byteCount := calldataload(0)
    #
    #    // Some junk data
    #    mstore(0, 0x1F1E1D1C1B1A191817161514131211100F0E0D0C0B0A090807060504030201FF)  # noqa: E501
    #
    #    sstore(0, byteCount)
    #
    #    // Return the result
    #    return(0x00, byteCount)
    # }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x0)
        + Op.MSTORE(
            offset=0x0,
            value=0x1F1E1D1C1B1A191817161514131211100F0E0D0C0B0A090807060504030201FF,  # noqa: E501
        )
        + Op.SSTORE(key=0x0, value=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN,
        nonce=1,
    )
    # Source: yul
    # berlin
    # {
    #    // How many bytes to return
    #    let byteCount := calldataload(0)
    #
    #    // Some junk data
    #    mstore(0, 0x1F1E1D1C1B1A191817161514131211100F0E0D0C0B0A090807060504030201FF)  # noqa: E501
    #
    #    sstore(0, byteCount)
    #
    #    // Return the result
    #    revert(0x00, byteCount)
    # }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x0)
        + Op.MSTORE(
            offset=0x0,
            value=0x1F1E1D1C1B1A191817161514131211100F0E0D0C0B0A090807060504030201FF,  # noqa: E501
        )
        + Op.SSTORE(key=0x0, value=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.REVERT,
        nonce=1,
    )
    # Source: yul
    # berlin
    # {
    #    let lengthReturned := calldataload(0x04)
    #    let offsetCopied   := calldataload(0x24)
    #    let lengthCopied   := calldataload(0x44)
    #    let contract       := calldataload(0x64)
    #    mstore(0, lengthReturned)
    #
    #    // The length of the buffer to be returned is part of the calldata
    #    // for this contract. However, it is necessary to send it to the
    #    // contract we're calling (either <contract:0x000000000000000000000000000000000000c0de> or <contract:0x0000000000000000000000000000000000000bad>) so it will know  # noqa: E501
    #    // what size of buffer to return to us
    #    let retVal := call(gas(), contract, 0,
    #       0, 0x20,    // input buffer with lengthReturned
    #       0, 0x100)    // output buffer
    #
    #    // Copy the return data (which fails if
    #    // offsetCopied+lengthCopied > lengthReturned)
    #    returndatacopy(0x100, offsetCopied, lengthCopied)
    #
    #
    #    // Show that other copies of excess length work (otherwise
    #    // the goat will never die)
    #    extcodecopy(<contract:0x000000000000000000000000000000000000c0de>, 0,0, add(0x20,extcodesize(<contract:0x000000000000000000000000000000000000c0de>)))  # noqa: E501
    #    calldatacopy(0,0, add(0x20,calldatasize()))
    #    codecopy(0,0, add(0x20,codesize()))
    #
    #
    #    // If we get here, kill the goat to show success
    #    sstore(0, 0xDEAD)
    # ... (1 more lines)
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x4)
        + Op.CALLDATALOAD(offset=0x24)
        + Op.PUSH2[0x100]
        + Op.PUSH1[0x0]
        + Op.PUSH1[0x20]
        + Op.DUP2
        + Op.DUP1
        + Op.CALLDATALOAD(offset=0x44)
        + Op.SWAP7
        + Op.CALLDATALOAD(offset=0x64)
        + Op.SWAP1
        + Op.DUP3
        + Op.MSTORE
        + Op.GAS
        + Op.POP(Op.CALL)
        + Op.PUSH2[0x100]
        + Op.RETURNDATACOPY
        + Op.EXTCODECOPY(
            address=addr,
            dest_offset=Op.DUP1,
            offset=0x0,
            size=Op.ADD(0x20, Op.EXTCODESIZE(address=addr)),
        )
        + Op.CALLDATACOPY(
            dest_offset=Op.DUP1, offset=0x0, size=Op.ADD(0x20, Op.CALLDATASIZE)
        )
        + Op.CODECOPY(
            dest_offset=Op.DUP1, offset=0x0, size=Op.ADD(0x20, Op.CODESIZE)
        )
        + Op.SSTORE(key=0x0, value=0xDEAD)
        + Op.STOP,
        storage={0: 24743},
        balance=0xDE0B6B3A7640000,
        nonce=1,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {
                "data": [1, 4, 6, 8, 9, 10, 11, 13, 16, 18, 20, 21, 22, 23],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 24743})},
        },
        {
            "indexes": {
                "data": [0, 2, 3, 5, 7, 12, 14, 15, 17, 19],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 57005})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(addr, left_padding=True),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x1)
        + Hash(addr, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x0)
        + Hash(0x8)
        + Hash(addr, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x0)
        + Hash(0x10)
        + Hash(addr, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x0)
        + Hash(0x11)
        + Hash(addr, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x1)
        + Hash(0xF)
        + Hash(addr, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x1)
        + Hash(0x10)
        + Hash(addr, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x8)
        + Hash(0x8)
        + Hash(addr, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x9)
        + Hash(0x8)
        + Hash(addr, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x10)
        + Hash(0x8)
        + Hash(addr, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x10)
        + Hash(0x10)
        + Hash(addr, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x20)
        + Hash(0x10)
        + Hash(addr, left_padding=True),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(addr_2, left_padding=True),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x1)
        + Hash(addr_2, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x0)
        + Hash(0x8)
        + Hash(addr_2, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x0)
        + Hash(0x10)
        + Hash(addr_2, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x0)
        + Hash(0x11)
        + Hash(addr_2, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x1)
        + Hash(0xF)
        + Hash(addr_2, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x1)
        + Hash(0x10)
        + Hash(addr_2, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x8)
        + Hash(0x8)
        + Hash(addr_2, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x9)
        + Hash(0x8)
        + Hash(addr_2, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x10)
        + Hash(0x8)
        + Hash(addr_2, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x10)
        + Hash(0x10)
        + Hash(addr_2, left_padding=True),
        Bytes("917694f9")
        + Hash(0x10)
        + Hash(0x20)
        + Hash(0x10)
        + Hash(addr_2, left_padding=True),
    ]
    tx_gas = [16777216]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        gas_price=100,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
