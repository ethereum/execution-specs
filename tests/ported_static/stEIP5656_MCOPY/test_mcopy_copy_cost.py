"""
Test cases for the cost of memory copy in the MCOPY instruction.

Ported from:
state_tests/Cancun/stEIP5656_MCOPY/MCOPY_copy_costFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
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
    ["state_tests/Cancun/stEIP5656_MCOPY/MCOPY_copy_costFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="src0_size0-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="src0_size0-g1",
        ),
        pytest.param(
            1,
            0,
            0,
            id="src0_size1-g0",
        ),
        pytest.param(
            1,
            1,
            0,
            id="src0_size1-g1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="src0_size31-g0",
        ),
        pytest.param(
            2,
            1,
            0,
            id="src0_size31-g1",
        ),
        pytest.param(
            3,
            0,
            0,
            id="src0_size32-g0",
        ),
        pytest.param(
            3,
            1,
            0,
            id="src0_size32-g1",
        ),
        pytest.param(
            4,
            0,
            0,
            id="src0_size33-g0",
        ),
        pytest.param(
            4,
            1,
            0,
            id="src0_size33-g1",
        ),
        pytest.param(
            5,
            0,
            0,
            id="src0_size44767-g0",
        ),
        pytest.param(
            5,
            1,
            0,
            id="src0_size44767-g1",
        ),
        pytest.param(
            6,
            0,
            0,
            id="src0_size44768-g0",
        ),
        pytest.param(
            6,
            1,
            0,
            id="src0_size44768-g1",
        ),
        pytest.param(
            7,
            0,
            0,
            id="src0_size44769-g0",
        ),
        pytest.param(
            7,
            1,
            0,
            id="src0_size44769-g1",
        ),
        pytest.param(
            8,
            0,
            0,
            id="src1_size0-g0",
        ),
        pytest.param(
            8,
            1,
            0,
            id="src1_size0-g1",
        ),
        pytest.param(
            9,
            0,
            0,
            id="src1_size1-g0",
        ),
        pytest.param(
            9,
            1,
            0,
            id="src1_size1-g1",
        ),
        pytest.param(
            10,
            0,
            0,
            id="src1_size31-g0",
        ),
        pytest.param(
            10,
            1,
            0,
            id="src1_size31-g1",
        ),
        pytest.param(
            11,
            0,
            0,
            id="src1_size32-g0",
        ),
        pytest.param(
            11,
            1,
            0,
            id="src1_size32-g1",
        ),
        pytest.param(
            12,
            0,
            0,
            id="src1_size33-g0",
        ),
        pytest.param(
            12,
            1,
            0,
            id="src1_size33-g1",
        ),
        pytest.param(
            13,
            0,
            0,
            id="src1_size44767-g0",
        ),
        pytest.param(
            13,
            1,
            0,
            id="src1_size44767-g1",
        ),
        pytest.param(
            14,
            0,
            0,
            id="src1_size44768-g0",
        ),
        pytest.param(
            14,
            1,
            0,
            id="src1_size44768-g1",
        ),
        pytest.param(
            15,
            0,
            0,
            id="src1_size44769-g0",
        ),
        pytest.param(
            15,
            1,
            0,
            id="src1_size44769-g1",
        ),
        pytest.param(
            16,
            0,
            0,
            id="src31_size0-g0",
        ),
        pytest.param(
            16,
            1,
            0,
            id="src31_size0-g1",
        ),
        pytest.param(
            17,
            0,
            0,
            id="src31_size1-g0",
        ),
        pytest.param(
            17,
            1,
            0,
            id="src31_size1-g1",
        ),
        pytest.param(
            18,
            0,
            0,
            id="src31_size31-g0",
        ),
        pytest.param(
            18,
            1,
            0,
            id="src31_size31-g1",
        ),
        pytest.param(
            19,
            0,
            0,
            id="src31_size32-g0",
        ),
        pytest.param(
            19,
            1,
            0,
            id="src31_size32-g1",
        ),
        pytest.param(
            20,
            0,
            0,
            id="src31_size33-g0",
        ),
        pytest.param(
            20,
            1,
            0,
            id="src31_size33-g1",
        ),
        pytest.param(
            21,
            0,
            0,
            id="src31_size44767-g0",
        ),
        pytest.param(
            21,
            1,
            0,
            id="src31_size44767-g1",
        ),
        pytest.param(
            22,
            0,
            0,
            id="src31_size44768-g0",
        ),
        pytest.param(
            22,
            1,
            0,
            id="src31_size44768-g1",
        ),
        pytest.param(
            23,
            0,
            0,
            id="src31_size44769-g0",
        ),
        pytest.param(
            23,
            1,
            0,
            id="src31_size44769-g1",
        ),
        pytest.param(
            24,
            0,
            0,
            id="src32_size0-g0",
        ),
        pytest.param(
            24,
            1,
            0,
            id="src32_size0-g1",
        ),
        pytest.param(
            25,
            0,
            0,
            id="src32_size1-g0",
        ),
        pytest.param(
            25,
            1,
            0,
            id="src32_size1-g1",
        ),
        pytest.param(
            26,
            0,
            0,
            id="src32_size31-g0",
        ),
        pytest.param(
            26,
            1,
            0,
            id="src32_size31-g1",
        ),
        pytest.param(
            27,
            0,
            0,
            id="src32_size32-g0",
        ),
        pytest.param(
            27,
            1,
            0,
            id="src32_size32-g1",
        ),
        pytest.param(
            28,
            0,
            0,
            id="src32_size33-g0",
        ),
        pytest.param(
            28,
            1,
            0,
            id="src32_size33-g1",
        ),
        pytest.param(
            29,
            0,
            0,
            id="src32_size44767-g0",
        ),
        pytest.param(
            29,
            1,
            0,
            id="src32_size44767-g1",
        ),
        pytest.param(
            30,
            0,
            0,
            id="src32_size44768-g0",
        ),
        pytest.param(
            30,
            1,
            0,
            id="src32_size44768-g1",
        ),
        pytest.param(
            31,
            0,
            0,
            id="src32_size44769-g0",
        ),
        pytest.param(
            31,
            1,
            0,
            id="src32_size44769-g1",
        ),
    ],
)
def test_mcopy_copy_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test cases for the cost of memory copy in the MCOPY instruction."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x3B9ACA00)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1687174231,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: yul
    # shanghai optimise {
    #   function mcopy(dst, src, size) { verbatim_3i_0o(hex"5e", dst, src, size) }  # noqa: E501
    #
    #   // Put a flag in storage indicating successful execution (will be reverted in case of OOG).  # noqa: E501
    #   sstore(0, 1)
    #
    #   // Expand memory to cover memory expansion cost before MCOPY.
    #   // The test uses up to 1400 memory words.
    #   mstore(44800, 1)
    #
    #   // MCOPY using src and size from CALLDATA to 0 destination.
    #   mcopy(0, calldataload(0), calldataload(32))
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.JUMP(pc=0xC)
        + Op.JUMPDEST
        + Op.MCOPY(dest_offset=Op.DUP3, offset=Op.DUP3, size=Op.DUP3)
        + Op.POP * 3
        + Op.JUMP
        + Op.JUMPDEST
        + Op.SSTORE(key=Op.PUSH0, value=0x1)
        + Op.MSTORE(offset=0xAF00, value=0x1)
        + Op.PUSH1[0x22]
        + Op.CALLDATALOAD(offset=0x20)
        + Op.CALLDATALOAD(offset=Op.PUSH0)
        + Op.PUSH0
        + Op.JUMP(pc=0x3)
        + Op.JUMPDEST,
        nonce=1,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {
                "data": [
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                    22,
                    23,
                    24,
                    25,
                    26,
                    27,
                    28,
                    29,
                    30,
                    31,
                ],
                "gas": 0,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 1})},
        },
        {
            "indexes": {
                "data": [
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    16,
                    17,
                    18,
                    19,
                    20,
                    24,
                    25,
                    26,
                    27,
                    28,
                ],
                "gas": 1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 1})},
        },
        {
            "indexes": {
                "data": [13, 14, 15, 21, 22, 23, 29, 30, 31],
                "gas": 1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 0})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(0x0) + Hash(0x0),
        Hash(0x0) + Hash(0x1),
        Hash(0x0) + Hash(0x1F),
        Hash(0x0) + Hash(0x20),
        Hash(0x0) + Hash(0x21),
        Hash(0x0) + Hash(0xAEDF),
        Hash(0x0) + Hash(0xAEE0),
        Hash(0x0) + Hash(0xAEE1),
        Hash(0x1) + Hash(0x0),
        Hash(0x1) + Hash(0x1),
        Hash(0x1) + Hash(0x1F),
        Hash(0x1) + Hash(0x20),
        Hash(0x1) + Hash(0x21),
        Hash(0x1) + Hash(0xAEDF),
        Hash(0x1) + Hash(0xAEE0),
        Hash(0x1) + Hash(0xAEE1),
        Hash(0x1F) + Hash(0x0),
        Hash(0x1F) + Hash(0x1),
        Hash(0x1F) + Hash(0x1F),
        Hash(0x1F) + Hash(0x20),
        Hash(0x1F) + Hash(0x21),
        Hash(0x1F) + Hash(0xAEDF),
        Hash(0x1F) + Hash(0xAEE0),
        Hash(0x1F) + Hash(0xAEE1),
        Hash(0x20) + Hash(0x0),
        Hash(0x20) + Hash(0x1),
        Hash(0x20) + Hash(0x1F),
        Hash(0x20) + Hash(0x20),
        Hash(0x20) + Hash(0x21),
        Hash(0x20) + Hash(0xAEDF),
        Hash(0x20) + Hash(0xAEE0),
        Hash(0x20) + Hash(0xAEE1),
    ]
    tx_gas = [100000, 55697]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
