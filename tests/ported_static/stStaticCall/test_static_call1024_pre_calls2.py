"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_Call1024PreCalls2Filler.json
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
    "0000000000000000000000002455231c1be66d57981908f4ac3633dee2e242e0",
    "000000000000000000000000daf588778cbccf0d5636643dbc67b42246b52f4a",
]

TX_GAS = [9214364837600034817]

TX_VALUE = [10]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_Call1024PreCalls2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call1024_pre_calls2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xCC381C83857B17CA629268ED418E2915A0287B84EFE9CF2204C020302E83CDA0
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x2,
                value=Op.STATICCALL(
                    gas=0xFFFF,
                    address=0xEEB613E2A52609EE927BE8A5B80FF190F6B71A37,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x3,
                value=Op.STATICCALL(
                    gas=0xFFFF,
                    address=0xEEB613E2A52609EE927BE8A5B80FF190F6B71A37,
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
                    address=0x2455231C1BE66D57981908F4AC3633DEE2E242E0,
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
        address=Address("0x2455231c1be66d57981908f4ac3633dee2e242e0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    # Source: LLL
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=Op.CALLDATALOAD(offset=0x0),
                    value=Op.CALLVALUE,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0xFFFF,
                    address=0xEEB613E2A52609EE927BE8A5B80FF190F6B71A37,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0xFFFF,
                    address=0xEEB613E2A52609EE927BE8A5B80FF190F6B71A37,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x0, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
            + Op.DELEGATECALL(
                gas=0xFFFFFFFFFFF,
                address=0xDAF588778CBCCF0D5636643DBC67B42246B52F4A,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=2024,
        nonce=0,
        address=Address("0xdaf588778cbccf0d5636643dbc67b42246b52f4a"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x1) + Op.STOP,
        balance=7000,
        nonce=0,
        address=Address("0xeeb613e2a52609ee927be8a5b80ff190f6b71a37"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={0: 1024, 1: 1},
                    code=bytes.fromhex(
                        "600060006000600073eeb613e2a52609ee927be8a5b80ff190f6b71a3761fffffa600255600060006000600073eeb613e2a52609ee927be8a5b80ff190f6b71a3761fffffa6003556001600054016000556000600060006000732455231c1be66d57981908f4ac3633dee2e242e0650ffffffffffff460015500"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000346000355af1600055600160015500"
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "600060006000600073eeb613e2a52609ee927be8a5b80ff190f6b71a3761fffffa50600060006000600073eeb613e2a52609ee927be8a5b80ff190f6b71a3761fffffa50600160005101600052600060006000600073daf588778cbccf0d5636643dbc67b42246b52f4a650ffffffffffff400"  # noqa: E501
                    )
                ),
                callee_2: Account(code=bytes.fromhex("600160005200")),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600073eeb613e2a52609ee927be8a5b80ff190f6b71a3761fffffa600255600060006000600073eeb613e2a52609ee927be8a5b80ff190f6b71a3761fffffa6003556001600054016000556000600060006000732455231c1be66d57981908f4ac3633dee2e242e0650ffffffffffff460015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000346000355af1600055600160015500"
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "600060006000600073eeb613e2a52609ee927be8a5b80ff190f6b71a3761fffffa50600060006000600073eeb613e2a52609ee927be8a5b80ff190f6b71a3761fffffa50600160005101600052600060006000600073daf588778cbccf0d5636643dbc67b42246b52f4a650ffffffffffff400"  # noqa: E501
                    )
                ),
                callee_2: Account(code=bytes.fromhex("600160005200")),
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
