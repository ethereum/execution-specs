"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_callBasicFiller.json
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
    "000000000000000000000000d3c0847ca0222f22dcfb4a433a378ff58ad6a881",
    "000000000000000000000000ead198f480fb91a5fbedcf5eb28cd369ee4c6cf2",
    "000000000000000000000000eb015f637a39c63f8b6db67505f5c02c613defc1",
    "000000000000000000000000d5b64fa2ca1e471b45b639a5e9c259ca24c28ace",
]

TX_GAS = [1000000]

TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stStaticCall/static_callBasicFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(2, 0, 0, id="case2"),
        pytest.param(3, 0, 0, id="case3"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call_basic(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
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

    # Source: LLL
    # {  [[ 0 ]] (STATICCALL 100000 (CALLDATALOAD 0) 0 0 0 0) [[ 1 ]] 1 }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x186A0,
                    address=Op.CALLDATALOAD(offset=0x0),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x13670d6bd41acd42d75e7c4c25df7384a6fbd752"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.LOG0(offset=0x1, size=0xA)
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.STOP
        ),
        balance=23,
        nonce=0,
        address=Address("0x2e0dd8abe4e68c5b602f3c65051f4b30c6d018da"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        balance=23,
        nonce=0,
        address=Address("0xc93c7a588b13699e562b3933e8f2b1c15e610781"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        storage={0x1: 0x1},
        balance=23,
        nonce=0,
        address=Address("0xd3c0847ca0222f22dcfb4a433a378ff58ad6a881"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALLCODE(
                    gas=0x9C40,
                    address=0xC93C7A588B13699E562B3933E8F2B1C15E610781,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.STOP
        ),
        balance=23,
        nonce=0,
        address=Address("0xd5b64fa2ca1e471b45b639a5e9c259ca24c28ace"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={0x1: 0x0},
        balance=23,
        nonce=0,
        address=Address("0xead198f480fb91a5fbedcf5eb28cd369ee4c6cf2"),  # noqa: E501
    )
    callee_5 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=0x9C40,
                    address=0x2E0DD8ABE4E68C5B602F3C65051F4B30C6D018DA,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.STOP
        ),
        balance=23,
        nonce=0,
        address=Address("0xeb015f637a39c63f8b6db67505f5c02c613defc1"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa600055600160015500"
                    ),
                ),
                callee: Account(code=bytes.fromhex("600a6001a0600160015200")),
                callee_1: Account(code=bytes.fromhex("600160015200")),
                callee_2: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6000600060006000600173c93c7a588b13699e562b3933e8f2b1c15e610781619c40f250600160015200"  # noqa: E501
                    )
                ),
                callee_4: Account(code=bytes.fromhex("600060015500")),
                callee_5: Account(
                    code=bytes.fromhex(
                        "60006000600060006000732e0dd8abe4e68c5b602f3c65051f4b30c6d018da619c40f150600160015200"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa600055600160015500"
                    ),
                ),
                callee: Account(code=bytes.fromhex("600a6001a0600160015200")),
                callee_1: Account(code=bytes.fromhex("600160015200")),
                callee_2: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6000600060006000600173c93c7a588b13699e562b3933e8f2b1c15e610781619c40f250600160015200"  # noqa: E501
                    )
                ),
                callee_4: Account(code=bytes.fromhex("600060015500")),
                callee_5: Account(
                    code=bytes.fromhex(
                        "60006000600060006000732e0dd8abe4e68c5b602f3c65051f4b30c6d018da619c40f150600160015200"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa600055600160015500"
                    ),
                ),
                callee: Account(code=bytes.fromhex("600a6001a0600160015200")),
                callee_1: Account(code=bytes.fromhex("600160015200")),
                callee_2: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6000600060006000600173c93c7a588b13699e562b3933e8f2b1c15e610781619c40f250600160015200"  # noqa: E501
                    )
                ),
                callee_4: Account(code=bytes.fromhex("600060015500")),
                callee_5: Account(
                    code=bytes.fromhex(
                        "60006000600060006000732e0dd8abe4e68c5b602f3c65051f4b30c6d018da619c40f150600160015200"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa600055600160015500"
                    ),
                ),
                callee: Account(code=bytes.fromhex("600a6001a0600160015200")),
                callee_1: Account(code=bytes.fromhex("600160015200")),
                callee_2: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6000600060006000600173c93c7a588b13699e562b3933e8f2b1c15e610781619c40f250600160015200"  # noqa: E501
                    )
                ),
                callee_4: Account(code=bytes.fromhex("600060015500")),
                callee_5: Account(
                    code=bytes.fromhex(
                        "60006000600060006000732e0dd8abe4e68c5b602f3c65051f4b30c6d018da619c40f150600160015200"  # noqa: E501
                    )
                ),
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
