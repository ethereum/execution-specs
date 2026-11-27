"""
Create2 inside Create2 inside Create2....

Ported from:
state_tests/stCreate2/Create2RecursiveFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreate2/Create2RecursiveFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
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
        pytest.param(
            0,
            2,
            0,
            id="-g2",
        ),
    ],
)
def test_create2_recursive(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Create2 inside Create2 inside Create2."""
    env = Environment(gas_limit=9223372036854775807)
    sender = pre.fund_eoa(amount=2**250)

    initcode_word = (
        0x606460006000396103E85A10601B576000606460006000F5601D565B5A5B
    )
    # Source: lll
    # { (MSTORE 0 0x606460006000396103e85a10601b576000606460006000f5601d565b5a5b)  (CREATE2 0 2 30 0) }  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=initcode_word)
        + Op.CREATE2(value=0x0, offset=0x2, size=0x1E, salt=0x0)
        + Op.STOP,
    )

    # Each level re-runs its own init code, zero-padded to 0x64 bytes.
    initcode = initcode_word.to_bytes(32, "big")[2:]
    chain = [
        compute_create_address(
            address=contract_0, salt=0, initcode=initcode, opcode=Op.CREATE2
        )
    ]
    while len(chain) < 1024:
        chain.append(
            compute_create_address(
                address=chain[-1],
                salt=0,
                initcode=initcode.ljust(0x64, b"\0"),
                opcode=Op.CREATE2,
            )
        )
    depth_1023, depth_1024 = chain[1022], chain[1023]

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {depth_1024: Account(nonce=1)},
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {depth_1024: Account.NONEXISTENT},
        },
        {
            "indexes": {"data": -1, "gas": 2, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {depth_1023: Account(nonce=1)},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_gas = [9151314442816847871, 20070000000000, 20080000000000]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
