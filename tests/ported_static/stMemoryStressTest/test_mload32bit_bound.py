"""
Test_mload32bit_bound.

Ported from:
state_tests/stMemoryStressTest/mload32bitBoundFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
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


@pytest.mark.ported_from(
    ["state_tests/stMemoryStressTest/mload32bitBoundFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_mload32bit_bound(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_mload32bit_bound."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xA3A3360EDACC183E5D6D28657FC0A09CD4819B2C73A02881B04471F81BE35A5A
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=17592320524892,
    )

    # Source: lll
    # { [[ 1 ]] (MLOAD 4294967296) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x100000000)) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x74639ACDFE345F749D595381961DAC48C3C5E56A),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3E801F4FA93760)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={},
                    code=bytes.fromhex("6401000000005160015500"),
                    nonce=0,
                ),
                sender: Account(storage={}, code=b"", nonce=1),
            },
        },
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={},
                    code=bytes.fromhex("6401000000005160015500"),
                    nonce=0,
                ),
                sender: Account(storage={}, code=b"", nonce=1),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [150000, 16777216]
    tx_value = [10]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
