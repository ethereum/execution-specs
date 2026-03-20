"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSystemOperationsTest/ABAcallsSuicide0Filler.json
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
        "tests/static/state_tests/stSystemOperationsTest/ABAcallsSuicide0Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ab_acalls_suicide0(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: LLL
    # {  [[ (PC) ]] (CALL 100000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 24 0 0 0 0) (SELFDESTRUCT <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>)  }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=Op.PC,
                value=Op.CALL(
                    gas=0x186A0,
                    address=0x24940009F045E4134ED2AB242BE610D312FE9A29,
                    value=0x18,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SELFDESTRUCT(
                address=0x24940009F045E4134ED2AB242BE610D312FE9A29
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x10481e52c494fd0d78604b0f9207a89008f7e9a9"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=Op.PC,
                value=Op.ADD(
                    0x1,
                    Op.CALL(
                        gas=0xC350,
                        address=0x10481E52C494FD0D78604B0F9207A89008F7E9A9,
                        value=0x17,
                        args_offset=0x0,
                        args_size=0x0,
                        ret_offset=0x0,
                        ret_size=0x0,
                    ),
                ),
            )
            + Op.STOP
        ),
        balance=23,
        nonce=0,
        address=Address("0x24940009f045e4134ed2ab242be610d312fe9a29"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={36: 1},
                    code=bytes.fromhex(
                        "600060006000600060187324940009f045e4134ed2ab242be610d312fe9a29620186a0f158557324940009f045e4134ed2ab242be610d312fe9a29ff00"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={38: 1},
                    code=bytes.fromhex(
                        "600060006000600060177310481e52c494fd0d78604b0f9207a89008f7e9a961c350f1600101585500"  # noqa: E501
                    ),
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=10000000,
        value=100000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
