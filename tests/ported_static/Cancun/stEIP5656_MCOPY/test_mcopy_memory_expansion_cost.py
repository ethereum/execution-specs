"""
Test cases for the memory expansion cost in the MCOPY instruction.

Ported from:
tests/static/state_tests/Cancun/stEIP5656_MCOPY
MCOPY_memory_expansion_costFiller.yml
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
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001f00000000000000000000000000000000000000000000000000000000000002c2",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002c2",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000003e000000000000000000000000000000000000000000000000000000000000001f00000000000000000000000000000000000000000000000000000000000002c2",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000003e00000000000000000000000000000000000000000000000000000000000002c2",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000003e000000000000000000000000000000000000000000000000000000000000003e00000000000000000000000000000000000000000000000000000000000002c2",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000002100000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000540",  # noqa: E501
    "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "0000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",  # noqa: E501
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000",  # noqa: E501
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000ffffffffffffffff",  # noqa: E501
]

TX_GAS = [100000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/Cancun/stEIP5656_MCOPY/MCOPY_memory_expansion_costFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(7, 0, 0, id="case2"),
        pytest.param(10, 0, 0, id="case3"),
        pytest.param(2, 0, 0, id="case4"),
        pytest.param(4, 0, 0, id="case5"),
        pytest.param(11, 0, 0, id="case6"),
        pytest.param(12, 0, 0, id="case7"),
        pytest.param(9, 0, 0, id="case8"),
        pytest.param(3, 0, 0, id="case9"),
        pytest.param(5, 0, 0, id="case10"),
        pytest.param(6, 0, 0, id="case11"),
        pytest.param(8, 0, 0, id="case12"),
        pytest.param(13, 0, 0, id="case13"),
        pytest.param(16, 0, 0, id="case14"),
        pytest.param(18, 0, 0, id="case15"),
        pytest.param(14, 0, 0, id="case16"),
        pytest.param(17, 0, 0, id="case17"),
        pytest.param(20, 0, 0, id="case18"),
        pytest.param(21, 0, 0, id="case19"),
        pytest.param(15, 0, 0, id="case20"),
        pytest.param(19, 0, 0, id="case21"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_mcopy_memory_expansion_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test cases for the memory expansion cost in the MCOPY instruction."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xF79127A3004ABDE26A4CBD80C428CB10F829FA11B54D36E7B326F4F4A5927ACF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1687174231,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: Yul
    # {
    #   // Take most of the SSTORE cost before MCOPY.
    #   sstore(0, 1)
    #
    #   // MCOPY using parameters from CALLDATA.
    #   mcopy(calldataload(0), calldataload(32), calldataload(64))
    #
    #   // Put MSIZE in storage.
    #   sstore(0, msize())
    # }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=Op.PUSH0, value=0x1)
            + Op.MCOPY(
                dest_offset=Op.CALLDATALOAD(offset=Op.PUSH0),
                offset=Op.CALLDATALOAD(offset=0x20),
                size=Op.CALLDATALOAD(offset=0x40),
            )
            + Op.SSTORE(key=Op.PUSH0, value=Op.MSIZE)
            + Op.STOP
        ),
        storage={0x0: 0xFA11ED},
        address=Address("0x147daecf943fa4fb48d1b7287571525b0baefeb9"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3B9ACA00)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex("60015f556040356020355f355e595f5500")
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 768},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1408},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1408},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 768},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 768},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1408},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 12, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1408},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1408},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 768},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 768},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1408},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1408},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 13, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1408},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 16, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 0xFA11ED},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 18, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 0xFA11ED},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 14, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex("60015f556040356020355f355e595f5500")
                )
            },
        },
        {
            "indexes": {"data": 17, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 0xFA11ED},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 20, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 0xFA11ED},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 21, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 0xFA11ED},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 15, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 0xFA11ED},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
        {
            "indexes": {"data": 19, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 0xFA11ED},
                    code=bytes.fromhex("60015f556040356020355f355e595f5500"),
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
