"""
Gas analysis showed this test's gas can go as low as 21053, and still...

Ported from:
state_tests/stQuadraticComplexityTest/Create1000Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

from tests.ported_static.constants import HIGH_GAS_LIMIT
from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stQuadraticComplexityTest/Create1000Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.slow
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
def test_create1000(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Gas analysis showed this test's gas can go as low as 21053, and..."""
    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 1000) [i](+ @i 1) [[ 0 ]] (CREATE 1 0 50000) ) [[ 1 ]] @i}  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x23, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0x3E8))
        )
        + Op.SSTORE(
            key=0x0, value=Op.CREATE(value=0x1, offset=0x0, size=0xC350)
        )
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                compute_create_address(
                    address=contract_0, nonce=867
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=781
                ): Account.NONEXISTENT,
                contract_0: Account(storage={0: 0, 1: 0}, nonce=1),
                compute_create_address(
                    address=contract_0, nonce=960
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=394
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=500
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=20
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=328
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=494
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                compute_create_address(
                    address=contract_0, nonce=867
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=781
                ): Account.NONEXISTENT,
                contract_0: Account(storage={0: 0, 1: 0}, nonce=1),
                compute_create_address(
                    address=contract_0, nonce=960
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=394
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=500
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=20
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=328
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=494
                ): Account.NONEXISTENT,
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [150000, 250000000]
    tx_value = [10]

    env = Environment(gas_limit=HIGH_GAS_LIMIT)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
