"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSystemOperationsTest/CalltoReturn2Filler.json
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
        "tests/static/state_tests/stSystemOperationsTest/CalltoReturn2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callto_return2(
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
        gas_limit=10000000,
    )

    # Source: raw bytecode
    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x1)
            + Op.MSTORE8(offset=0x0, value=0x37)
            + Op.PUSH1[0x2]
            + Op.PUSH1[0x0]
            + Op.CALLCODE
        ),
        balance=23,
        nonce=0,
        address=Address("0x2b45331c406df38b99656c3ed3a97ef219979232"),  # noqa: E501
    )
    # Source: LLL
    # { (MSTORE 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) (MSTORE 32 0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa ) [[ 0 ]] (CALL 5000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 23 0 64 0 2 ) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xAAFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFAA,  # noqa: E501
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x1388,
                    address=0x2B45331C406DF38B99656C3ED3A97EF219979232,
                    value=0x17,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x2,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xbd44c6eb4f918aa9ab1da6bca875839b1250e4e9"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("6001600155603760005360026000f2")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6000527faaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa60205260026000604060006017732b45331c406df38b99656c3ed3a97ef219979232611388f160005500"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=300000,
        value=100000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
