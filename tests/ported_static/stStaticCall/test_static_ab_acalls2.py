"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_ABAcalls2Filler.json
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
    "000000000000000000000000cee890df61958e0d40fbbfc310af80b8c47d0dfe",
    "000000000000000000000000db486d3e181181d2063032b1250c07ca0185a446",
]

TX_GAS = [1000000000]

TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stStaticCall/static_ABAcalls2Filler.json"],
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
def test_static_ab_acalls2(
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
        gas_limit=10000000000,
    )

    # Source: LLL
    # { [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
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
        address=Address("0x2b0de1d059b61d3afbdbc6d7d59720fe04c1fff2"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
            + Op.STATICCALL(
                gas=Op.SUB(Op.GAS, 0x186A0),
                address=0xDB486D3E181181D2063032B1250C07CA0185A446,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x57efc7a25d8e40b0798fb4cbc2bcc3c124141cbb"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
            + Op.STATICCALL(
                gas=Op.SUB(Op.GAS, 0x186A0),
                address=0xE278F8058BEF1396C2B1DF4D1DC4B65233133C57,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xcee890df61958e0d40fbbfc310af80b8c47d0dfe"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
            + Op.STATICCALL(
                gas=Op.SUB(Op.GAS, 0x186A0),
                address=0x57EFC7A25D8E40B0798FB4CBC2BCC3C124141CBB,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xdb486d3e181181d2063032b1250c07ca0185a446"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
            + Op.STATICCALL(
                gas=Op.SUB(Op.GAS, 0x186A0),
                address=0xCEE890DF61958E0D40FBBFC310AF80B8C47D0DFE,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xe278f8058bef1396c2b1df4d1dc4b65233133c57"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000346000355af1600055600160015500"
                    ),
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "600160005101600052600060006000600073db486d3e181181d2063032b1250c07ca0185a446620186a05a03fa00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "600160005401600055600060006000600073e278f8058bef1396c2b1df4d1dc4b65233133c57620186a05a03fa00"  # noqa: E501
                    ),
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60016000510160005260006000600060007357efc7a25d8e40b0798fb4cbc2bcc3c124141cbb620186a05a03fa00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "600160005401600055600060006000600073cee890df61958e0d40fbbfc310af80b8c47d0dfe620186a05a03fa00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000346000355af1600055600160015500"
                    ),
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "600160005101600052600060006000600073db486d3e181181d2063032b1250c07ca0185a446620186a05a03fa00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "600160005401600055600060006000600073e278f8058bef1396c2b1df4d1dc4b65233133c57620186a05a03fa00"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60016000510160005260006000600060007357efc7a25d8e40b0798fb4cbc2bcc3c124141cbb620186a05a03fa00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "600160005401600055600060006000600073cee890df61958e0d40fbbfc310af80b8c47d0dfe620186a05a03fa00"  # noqa: E501
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
