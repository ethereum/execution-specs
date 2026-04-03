"""
Test_mload32bit_bound_msize.

Ported from:
state_tests/stMemoryStressTest/mload32bitBound_MsizeFiller.json
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
    ["state_tests/stMemoryStressTest/mload32bitBound_MsizeFiller.json"],
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
def test_mload32bit_bound_msize(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_mload32bit_bound_msize."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x7DD14755C573E37C1F649B0C53B9815F76AEBD636DF7CCFA97F4579F33BA59A0
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=175923205248920000,
    )

    # Source: lll
    # { [4294967295] 1 [[ 0 ]] (MSIZE)}
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0xFFFFFFFF, value=0x1)
        + Op.SSTORE(key=0x0, value=Op.MSIZE)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x15D5A32351458FF3DCA214BD202C21F066031AE1),  # noqa: E501
    )
    pre[sender] = Account(balance=0x186A0C3B1E19A180)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={0: 0},
                    code=bytes.fromhex("600163ffffffff525960005500"),
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
                    storage={0: 0},
                    code=bytes.fromhex("600163ffffffff525960005500"),
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

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
