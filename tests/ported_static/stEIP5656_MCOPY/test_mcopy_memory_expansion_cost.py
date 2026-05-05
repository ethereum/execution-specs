"""
Test cases for the memory expansion cost in the MCOPY instruction.

Ported from:
state_tests/Cancun/stEIP5656_MCOPY/MCOPY_memory_expansion_costFiller.yml
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
    [
        "state_tests/Cancun/stEIP5656_MCOPY/MCOPY_memory_expansion_costFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="dst0_src0_size0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="dst0_src31_size706",
        ),
        pytest.param(
            2,
            0,
            0,
            id="dst31_src0_size706",
        ),
        pytest.param(
            3,
            0,
            0,
            id="dst62_src31_size706",
        ),
        pytest.param(
            4,
            0,
            0,
            id="dst31_src62_size706",
        ),
        pytest.param(
            5,
            0,
            0,
            id="dst62_src62_size706",
        ),
        pytest.param(
            6,
            0,
            0,
            id="dst64_src0_size1344",
        ),
        pytest.param(
            7,
            0,
            0,
            id="dst0_src64_size1344",
        ),
        pytest.param(
            8,
            0,
            0,
            id="dst64_src33_size1344",
        ),
        pytest.param(
            9,
            0,
            0,
            id="dst33_src64_size1344",
        ),
        pytest.param(
            10,
            0,
            0,
            id="dst1_src33_size1344",
        ),
        pytest.param(
            11,
            0,
            0,
            id="dst33_src1_size1344",
        ),
        pytest.param(
            12,
            0,
            0,
            id="dst33_src33_size1344",
        ),
        pytest.param(
            13,
            0,
            0,
            id="dst64_src64_size1344",
        ),
        pytest.param(
            14,
            0,
            0,
            id="huge_size0",
        ),
        pytest.param(
            15,
            0,
            0,
            id="huge_src0_size1",
        ),
        pytest.param(
            16,
            0,
            0,
            id="huge_dst0_size1",
        ),
        pytest.param(
            17,
            0,
            0,
            id="huge_size_n255",
        ),
        pytest.param(
            18,
            0,
            0,
            id="huge_dst0_size_n256",
        ),
        pytest.param(
            19,
            0,
            0,
            id="huge_src0_size_n256",
        ),
        pytest.param(
            20,
            0,
            0,
            id="huge_size_n63",
        ),
        pytest.param(
            21,
            0,
            0,
            id="huge_size_n64",
        ),
    ],
)
def test_mcopy_memory_expansion_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test cases for the memory expansion cost in the MCOPY instruction."""
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
    # cancun {
    #   // Take most of the SSTORE cost before MCOPY.
    #   sstore(0, 1)
    #
    #   // MCOPY using parameters from CALLDATA.
    #   mcopy(calldataload(0), calldataload(32), calldataload(64))
    #
    #   // Put MSIZE in storage.
    #   sstore(0, msize())
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=Op.PUSH0, value=0x1)
        + Op.MCOPY(
            dest_offset=Op.CALLDATALOAD(offset=Op.PUSH0),
            offset=Op.CALLDATALOAD(offset=0x20),
            size=Op.CALLDATALOAD(offset=0x40),
        )
        + Op.SSTORE(key=Op.PUSH0, value=Op.MSIZE)
        + Op.STOP,
        storage={0: 0xFA11ED},
        nonce=1,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 14], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 0})},
        },
        {
            "indexes": {"data": [1, 2, 3, 4, 5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 768})},
        },
        {
            "indexes": {
                "data": [6, 7, 8, 9, 10, 11, 12, 13],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 1408})},
        },
        {
            "indexes": {
                "data": [15, 16, 17, 18, 19, 20, 21],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 0xFA11ED})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(0x0) + Hash(0x0) + Hash(0x0),
        Hash(0x0) + Hash(0x1F) + Hash(0x2C2),
        Hash(0x1F) + Hash(0x0) + Hash(0x2C2),
        Hash(0x3E) + Hash(0x1F) + Hash(0x2C2),
        Hash(0x1F) + Hash(0x3E) + Hash(0x2C2),
        Hash(0x3E) + Hash(0x3E) + Hash(0x2C2),
        Hash(0x40) + Hash(0x0) + Hash(0x540),
        Hash(0x0) + Hash(0x40) + Hash(0x540),
        Hash(0x40) + Hash(0x21) + Hash(0x540),
        Hash(0x21) + Hash(0x40) + Hash(0x540),
        Hash(0x1) + Hash(0x21) + Hash(0x540),
        Hash(0x21) + Hash(0x1) + Hash(0x540),
        Hash(0x21) + Hash(0x21) + Hash(0x540),
        Hash(0x40) + Hash(0x40) + Hash(0x540),
        Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(0x0),
        Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(0x0)
        + Hash(0x1),
        Hash(0x0)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(0x1),
        Hash(0x0)
        + Hash(0x0)
        + Hash(
            0x8000000000000000000000000000000000000000000000000000000000000000
        ),
        Hash(0x0)
        + Hash(0x1)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Hash(0x1)
        + Hash(0x0)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Hash(0x0) + Hash(0x0) + Hash(0x8000000000000000),
        Hash(0x1) + Hash(0x1) + Hash(0xFFFFFFFFFFFFFFFF),
    ]
    tx_gas = [100000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
