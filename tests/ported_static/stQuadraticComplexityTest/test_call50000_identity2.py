"""
Test_call50000_identity2.

Ported from:
state_tests/stQuadraticComplexityTest/Call50000_identity2Filler.json
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
    ["state_tests/stQuadraticComplexityTest/Call50000_identity2Filler.json"],
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
@pytest.mark.pre_alloc_mutable
def test_call50000_identity2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_call50000_identity2."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=882500000,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    # Source: lll
    # { (def 'i 0x80) [ 1 ] 42 (for {} (< @i 50000) [i](+ @i 1) [[ 0 ]] (CALL 1564 4 1 0 50000 1 50000) ) [[ 1 ]] @i [[ 2 ]] @1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x2A)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x32, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x61C,
                address=0x4,
                value=0x1,
                args_offset=0x0,
                args_size=0xC350,
                ret_offset=0x1,
                ret_size=0xC350,
            ),
        )
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x5)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x1))
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address(0x6DC17565113358633923F732D8C32382345D2D6F),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                sender: Account(storage={}, code=b"", nonce=1),
                target: Account(
                    storage={},
                    code=bytes.fromhex(
                        "602a6001525b61c350608051101560325761c350600161c35060006001600461061cf16000556001608051016080526005565b60805160015560015160025500"  # noqa: E501
                    ),
                    nonce=0,
                ),
            },
        },
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                sender: Account(storage={}, code=b"", nonce=1),
                target: Account(
                    storage={},
                    code=bytes.fromhex(
                        "602a6001525b61c350608051101560325761c350600161c35060006001600461061cf16000556001608051016080526005565b60805160015560015160025500"  # noqa: E501
                    ),
                    nonce=0,
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [150000, 250000000]
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
