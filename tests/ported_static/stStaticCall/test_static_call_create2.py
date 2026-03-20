"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_callCreate2Filler.json
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
    "0000000000000000000000001000000000000000000000000000000000000001",
    "0000000000000000000000001000000000000000000000000000000000000002",
]

TX_GAS = [1000000]

TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stStaticCall/static_callCreate2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(2, 0, 0, id="case2"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call_create2(
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
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
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
    # {  [[ 0 ]] (CREATE 1 0 0) [[ 1 ]] (STATICCALL 300000 (SLOAD 0) 0 0 0 0) }
    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0, value=Op.CREATE(value=0x1, offset=0x0, size=0x0)
            )
            + Op.SSTORE(
                key=0x1,
                value=Op.STATICCALL(
                    gas=0x493E0,
                    address=Op.SLOAD(key=0x0),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # {  (MSTORE 0 0x6460016001556000526005601bf3 ) [[ 0 ]] (CREATE 1 18 14) [[ 1 ]] (STATICCALL 300000 (SLOAD 0) 0 0 0 0) }  # noqa: E501
    callee_1 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x6460016001556000526005601BF3)
            + Op.SSTORE(
                key=0x0, value=Op.CREATE(value=0x1, offset=0x12, size=0xE)
            )
            + Op.SSTORE(
                key=0x1,
                value=Op.STATICCALL(
                    gas=0x493E0,
                    address=Op.SLOAD(key=0x0),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: LLL
    # {  (MSTORE 0 0x6460016001556000526005601bf3 ) [[ 0 ]] (CREATE 1 18 14) [[ 1 ]] (STATICCALL 300000 (SLOAD 0) 0 0 0 0) (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x6460016001556000526005601BF3)
            + Op.SSTORE(
                key=0x0, value=Op.CREATE(value=0x1, offset=0x12, size=0xE)
            )
            + Op.SSTORE(
                key=0x1,
                value=Op.STATICCALL(
                    gas=0x493E0,
                    address=Op.SLOAD(key=0x0),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4B,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.POP(Op.EXTCODESIZE(address=0x1))
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x2F)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000002"),  # noqa: E501
    )
    # Source: LLL
    # {  (CALL 600000 (CALLDATALOAD 0) 0 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0x927C0,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xa000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={
                        0: 0x13136008B64FF592819B2FA6D43F2835C452020E,
                        1: 1,
                    }
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                callee_1: Account(
                    storage={
                        0: 0x5DDDFCE53EE040D9EB21AFBC0AE1BB4DBB0BA643,
                        1: 0,
                    }
                ),
                Address("0x5dddfce53ee040d9eb21afbc0ae1bb4dbb0ba643"): Account(
                    storage={}, code=bytes.fromhex("6001600155")
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {callee_1: Account(storage={0: 0, 1: 0})},
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
