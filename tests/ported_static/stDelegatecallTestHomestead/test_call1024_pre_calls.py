"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stDelegatecallTestHomestead
Call1024PreCallsFiller.json
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stDelegatecallTestHomestead/Call1024PreCallsFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_gas_limit, expected_post",
    [
        (
            11937600034817,
            {
                Address("0x515e9a6500c10f0db92754d10136694bb188153b"): Account(
                    storage={0: 1025, 1: 1}
                )
            },
        ),
        (
            9214364837600034817,
            {
                Address("0x515e9a6500c10f0db92754d10136694bb188153b"): Account(
                    storage={0: 1025, 1: 1}
                )
            },
        ),
        (
            9381323795670,
            {
                Address("0x515e9a6500c10f0db92754d10136694bb188153b"): Account(
                    storage={0: 989, 1: 1, 2: 1, 3: 1}
                )
            },
        ),
    ],
    ids=["case0", "case1", "case2"],
)
@pytest.mark.pre_alloc_mutable
def test_call1024_pre_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xCC381C83857B17CA629268ED418E2915A0287B84EFE9CF2204C020302E83CDA0
    )
    callee = Address("0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    # Source: LLL
    # { [[ 2 ]] (CALL 0xffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 1 0 0 0 0) [[ 3 ]] (CALL 0xffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 1 0 0 0 0)  [[ 0 ]] (ADD @@0 1) [[ 1 ]] (DELEGATECALL 0xfffffffffff <contract:target:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=0xFFFF,
                    address=0xD9B97C712EBCE43F3C19179BBEF44B550F9E8BC0,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x3,
                value=Op.CALL(
                    gas=0xFFFF,
                    address=0xD9B97C712EBCE43F3C19179BBEF44B550F9E8BC0,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
            + Op.SSTORE(
                key=0x1,
                value=Op.DELEGATECALL(
                    gas=0xFFFFFFFFFFF,
                    address=0x515E9A6500C10F0DB92754D10136694BB188153B,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=2024,
        nonce=0,
        address=Address("0x515e9a6500c10f0db92754d10136694bb188153b"),  # noqa: E501
    )
    pre[callee] = Account(balance=7000, nonce=0)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=tx_gas_limit,
        value=10,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
