"""
data0 - create collision to empty, data1 - to empty but nonce, data2 - to...

Ported from:
tests/static/state_tests/stCreateTest/CreateCollisionToEmpty2Filler.json
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
    "0000000000000000000000001000000000000000000000000000000000000000",
    "0000000000000000000000002000000000000000000000000000000000000000",
    "0000000000000000000000003000000000000000000000000000000000000000",
]

TX_GAS = [600000, 54000]

TX_VALUE = [0, 1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCreateTest/CreateCollisionToEmpty2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(0, 0, 1, id="case1"),
        pytest.param(0, 1, 0, id="case2"),
        pytest.param(0, 1, 1, id="case3"),
        pytest.param(1, 0, 0, id="case4"),
        pytest.param(1, 0, 1, id="case5"),
        pytest.param(1, 1, 0, id="case6"),
        pytest.param(1, 1, 1, id="case7"),
        pytest.param(2, 0, 0, id="case8"),
        pytest.param(2, 0, 1, id="case9"),
        pytest.param(2, 1, 0, id="case10"),
        pytest.param(2, 1, 1, id="case11"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_collision_to_empty2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Data0 - create collision to empty, data1 - to empty but nonce,..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )
    callee = Address("0x0bf4c804e0579073baf54ec4ec37cd04f3455c65")
    callee_2 = Address("0x13136008b64ff592819b2fa6d43f2835c452020e")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(balance=0, nonce=2)
    # Source: LLL
    # { (MSTORE 0 0x6001600155) [[1]] (CREATE 0 27 5) }
    callee_1 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x6001600155)
            + Op.SSTORE(
                key=0x1, value=Op.CREATE(value=0x0, offset=0x1B, size=0x5)
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[callee_2] = Account(balance=10, nonce=0)
    # Source: LLL
    # { (CALL 80000 (CALLDATALOAD 0) 0 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0x13880,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1a00000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { (MSTORE 0 0x6001600155) [[1]] (CREATE 0 27 5) }
    callee_3 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x6001600155)
            + Op.SSTORE(
                key=0x1, value=Op.CREATE(value=0x0, offset=0x1B, size=0x5)
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x2000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { (MSTORE 0 0x6001600155) [[1]] (CREATE 0 27 5) }
    callee_4 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x6001600155)
            + Op.SSTORE(
                key=0x1, value=Op.CREATE(value=0x0, offset=0x1B, size=0x5)
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x3000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_5 = pre.deploy_contract(
        code=bytes.fromhex("1122334455"),
        nonce=0,
        address=Address("0x4b86c4ed99b87f0f396bc0c76885453c343916ed"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(storage={}, nonce=0),
                callee_2: Account(storage={}, nonce=0, balance=10, code=b""),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    storage={1: 0x13136008B64FF592819B2FA6D43F2835C452020E},
                    nonce=1,
                ),
                callee_2: Account(
                    storage={1: 1}, nonce=1, balance=10, code=b""
                ),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": [1, 2], "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(storage={}, nonce=2, code=b""),
                callee_3: Account(storage={1: 0}, nonce=0),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(storage={}, nonce=2, code=b""),
                callee_3: Account(storage={1: 0}, nonce=0),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                callee_4: Account(storage={1: 0}, nonce=0),
                callee_5: Account(
                    storage={}, nonce=0, code=bytes.fromhex("1122334455")
                ),
                sender: Account(nonce=1),
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
