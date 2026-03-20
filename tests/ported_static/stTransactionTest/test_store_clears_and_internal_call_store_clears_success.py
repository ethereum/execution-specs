"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stTransactionTest
StoreClearsAndInternalCallStoreClearsSuccessFiller.json
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


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stTransactionTest/StoreClearsAndInternalCallStoreClearsSuccessFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_store_clears_and_internal_call_store_clears_success(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x96C07046493EC8728482079AB999D2994420D9CF4D3491DFD06871B106D9D87B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0x1DCD6500)
    # Source: LLL
    # {(SSTORE 0 0)(SSTORE 1 0)(SSTORE 2 0)(SSTORE 3 0) (CALL 50000 <contract:0x0000000000000000000000000000000000000000> 1 0 0 0 0) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x0)
            + Op.SSTORE(key=0x1, value=0x0)
            + Op.SSTORE(key=0x2, value=0x0)
            + Op.SSTORE(key=0x3, value=0x0)
            + Op.CALL(
                gas=0xC350,
                address=0xD61E0564FAB2B0DA5136F75DB579B663BD9F2BD8,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        storage={0x0: 0xC, 0x1: 0xC, 0x2: 0xC, 0x3: 0xC, 0x4: 0xC},
        balance=10,
        nonce=0,
        address=Address("0x8989e867016031a6730f2b84d5e47e1f0f83bdd9"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x0)
            + Op.SSTORE(key=0x1, value=0x0)
            + Op.SSTORE(key=0x2, value=0x0)
            + Op.SSTORE(key=0x3, value=0x0)
            + Op.SSTORE(key=0x4, value=0x0)
            + Op.SSTORE(key=0x5, value=0x0)
            + Op.SSTORE(key=0x6, value=0x0)
            + Op.SSTORE(key=0x7, value=0x0)
            + Op.SSTORE(key=0x8, value=0x0)
            + Op.SSTORE(key=0x9, value=0x0)
            + Op.STOP
        ),
        storage={
            0x0: 0xC,
            0x1: 0xC,
            0x2: 0xC,
            0x3: 0xC,
            0x4: 0xC,
            0x5: 0xC,
            0x6: 0xC,
            0x7: 0xC,
            0x8: 0xC,
            0x9: 0xC,
        },
        nonce=0,
        address=Address("0xd61e0564fab2b0da5136f75db579b663bd9f2bd8"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={4: 12},
                    code=bytes.fromhex(
                        "60006000556000600155600060025560006003556000600060006000600173d61e0564fab2b0da5136f75db579b663bd9f2bd861c350f100"  # noqa: E501
                    ),
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "600060005560006001556000600255600060035560006004556000600555600060065560006007556000600855600060095500"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=200000,
        value=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
