"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stReturnDataTest/tooLongReturnDataCopyFiller.yml
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
    "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000001000000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
    "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000009000000000000000000000000000000000000000000000000000000000000000800000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
    "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000800000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
    "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001000000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
    "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001000000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
    "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000011000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
    "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000010000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
    "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000090000000000000000000000000000000000000000000000000000000000000008000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
    "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000008000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
    "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
    "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000010000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
    "917694f900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
    "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001100000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
    "",
    "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000800000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
    "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
    "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
    "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
    "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000008000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
    "917694f900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
    "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000800000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
    "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
    "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000f00000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
    "917694f9000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
]

TX_GAS = [16777216]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stReturnDataTest/tooLongReturnDataCopyFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(2, 0, 0, id="case2"),
        pytest.param(3, 0, 0, id="case3"),
        pytest.param(4, 0, 0, id="case4"),
        pytest.param(5, 0, 0, id="case5"),
        pytest.param(6, 0, 0, id="case6"),
        pytest.param(7, 0, 0, id="case7"),
        pytest.param(8, 0, 0, id="case8"),
        pytest.param(9, 0, 0, id="case9"),
        pytest.param(10, 0, 0, id="case10"),
        pytest.param(11, 0, 0, id="case11"),
        pytest.param(12, 0, 0, id="case12"),
        pytest.param(23, 0, 0, id="case13"),
        pytest.param(14, 0, 0, id="case14"),
        pytest.param(15, 0, 0, id="case15"),
        pytest.param(16, 0, 0, id="case16"),
        pytest.param(17, 0, 0, id="case17"),
        pytest.param(18, 0, 0, id="case18"),
        pytest.param(19, 0, 0, id="case19"),
        pytest.param(20, 0, 0, id="case20"),
        pytest.param(21, 0, 0, id="case21"),
        pytest.param(22, 0, 0, id="case22"),
        pytest.param(19, 0, 0, id="case23"),
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
    """Ori Pomerantz   qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x04DC42D61413D4DED993826AC4D6ED7A4A970C60335D2B285C60A4274E792FF1
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4503599627370496,
    )

    callee = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x0)
            + Op.MSTORE(
                offset=0x0,
                value=0x1F1E1D1C1B1A191817161514131211100F0E0D0C0B0A090807060504030201FF,  # noqa: E501
            )
            + Op.SSTORE(key=0x0, value=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.REVERT
        ),
        address=Address("0x23eef957bcfb3738417aee7fdf4294cf110d7881"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635C9ADC5DEA00000, nonce=1)
    callee_1 = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x0)
            + Op.MSTORE(
                offset=0x0,
                value=0x1F1E1D1C1B1A191817161514131211100F0E0D0C0B0A090807060504030201FF,  # noqa: E501
            )
            + Op.SSTORE(key=0x0, value=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.RETURN
        ),
        address=Address("0xa6e4f86617d6ab14d857f9115c2ab9f2787157ba"),  # noqa: E501
    )
    # Source: Yul
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
    # }
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x4)
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
                address=0xA6E4F86617D6AB14D857F9115C2AB9F2787157BA,
                dest_offset=Op.DUP1,
                offset=0x0,
                size=Op.ADD(
                    0x20,
                    Op.EXTCODESIZE(
                        address=0xA6E4F86617D6AB14D857F9115C2AB9F2787157BA,
                    ),
                ),
            )
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP1,
                offset=0x0,
                size=Op.ADD(0x20, Op.CALLDATASIZE),
            )
            + Op.CODECOPY(
                dest_offset=Op.DUP1,
                offset=0x0,
                size=Op.ADD(0x20, Op.CODESIZE),
            )
            + Op.SSTORE(key=0x0, value=0xDEAD)
            + Op.STOP
        ),
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        address=Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
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
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
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
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
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
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
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
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
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
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
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
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
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
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
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
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
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
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
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
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
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
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 23, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
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
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 57005},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
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
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    storage={0: 16},
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={0: 57005},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 16, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    storage={0: 16},
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={0: 57005},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 17, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    storage={0: 16},
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={0: 57005},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 18, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    storage={0: 16},
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={0: 57005},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 19, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 57005},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 20, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 57005},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 21, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 57005},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 22, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 57005},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 19, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000fd"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000357f1f1e1d1c1b1a191817161514131211100f0e0d0c0b0a090807060504030201ff600052806000556000f3"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 57005},
                    code=bytes.fromhex(
                        "600435602435610100600060208180604435966064359082525af1506101003e73a6e4f86617d6ab14d857f9115c2ab9f2787157ba3b60200160008073a6e4f86617d6ab14d857f9115c2ab9f2787157ba3c3660200160008037386020016000803961dead60005500"  # noqa: E501
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
        gas_price=100,
        nonce=1,
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
