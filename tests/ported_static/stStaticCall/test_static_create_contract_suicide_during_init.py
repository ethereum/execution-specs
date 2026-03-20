"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_CREATE_ContractSuicideDuringInitFiller.json
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
    "600060006000600073c94f5374fce5edbc8e2a8697c15331677e6ebf0b61ea60fa506d64600c6000556000526005601bf360005273c94f5374fce5edbc8e2a8697c15331677e6ebf0bff",  # noqa: E501
    "600060006000600073b94f5374fce5edbc8e2a8697c15331677e6ebf0b61ea60fa506d64600c6000556000526005601bf360005273c94f5374fce5edbc8e2a8697c15331677e6ebf0bff",  # noqa: E501
    "600060006000600073d94f5374fce5edbc8e2a8697c15331677e6ebf0b61ea60fa506d64600c6000556000526005601bf360005273c94f5374fce5edbc8e2a8697c15331677e6ebf0bff",  # noqa: E501
    "600060006000600073e94f5374fce5edbc8e2a8697c15331677e6ebf0b61ea60fa506d64600c6000556000526005601bf360005273c94f5374fce5edbc8e2a8697c15331677e6ebf0bff",  # noqa: E501
]

TX_GAS = [150000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_CREATE_ContractSuicideDuringInitFiller.json",  # noqa: E501
    ],
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
def test_static_create_contract_suicide_during_init(
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

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: LLL
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }
    contract = pre.deploy_contract(
        code=(
            Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1C,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.POP(Op.EXTCODESIZE(address=0x1))
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x0)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=11,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: LLL
    # { (MSTORE 1 1) }
    callee_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: LLL
    # { (SSTORE 1 1) }
    callee_2 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=11,
        nonce=0,
        address=Address("0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: LLL
    # { (CALL 100 0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b 1 0 0 0 0) }
    callee_3 = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0x64,
                address=0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=11,
        nonce=0,
        address=Address("0xe94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160015200")),
                callee_2: Account(code=bytes.fromhex("600160015500")),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6000600060006000600173c94f5374fce5edbc8e2a8697c15331677e6ebf0b6064f100"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160015200")),
                callee_2: Account(code=bytes.fromhex("600160015500")),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6000600060006000600173c94f5374fce5edbc8e2a8697c15331677e6ebf0b6064f100"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160015200")),
                callee_2: Account(code=bytes.fromhex("600160015500")),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6000600060006000600173c94f5374fce5edbc8e2a8697c15331677e6ebf0b6064f100"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b00"  # noqa: E501
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160015200")),
                callee_2: Account(code=bytes.fromhex("600160015500")),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6000600060006000600173c94f5374fce5edbc8e2a8697c15331677e6ebf0b6064f100"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=None,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
