"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_contractCreationMakeCallThatAskMoreGasThenTransactionProvidedFiller.json
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
    "604060006040600073100000000000000000000000000000000000000161c350fa",
    "604060006040600073200000000000000000000000000000000000000161c350fa",
    "604060006040600073300000000000000000000000000000000000000161c350fa",
    "604060006040600073400000000000000000000000000000000000000161c350fa",
]

TX_GAS = [96000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_contractCreationMakeCallThatAskMoreGasThenTransactionProvidedFiller.json",  # noqa: E501
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
def test_static_contract_creation_make_call_that_ask_more_gas_then_transaction_provided(  # noqa: E501
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
        gas_limit=100000000,
    )

    # Source: LLL
    # {(SSTORE 1 1)}
    contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: LLL
    # {(MSTORE 1 1)}
    callee_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address("0x2000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: LLL
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }
    callee_2 = pre.deploy_contract(
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
        balance=0x186A0,
        nonce=0,
        address=Address("0x3000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: LLL
    # { (CALLCODE 1000 0x4000000000000000000000000000000000000004 0 0 0 0 0) }
    callee_3 = pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=0x3E8,
                address=0x4000000000000000000000000000000000000004,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0x186A0,
        nonce=0,
        address=Address("0x4000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: LLL
    # { (MSTORE 1 1) }
    callee_4 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address("0x4000000000000000000000000000000000000004"),  # noqa: E501
    )
    # Source: LLL
    # { (CALLCODE 1000000 0x4000000000000000000000000000000000000004 0 0 0 0 0) }  # noqa: E501
    callee_5 = pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=0xF4240,
                address=0x4000000000000000000000000000000000000004,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0x186A0,
        nonce=0,
        address=Address("0x5000000000000000000000000000000000000001"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x10C8E0)
    # Source: LLL
    # {(STATICCALL 50000 0x1000000000000000000000000000000000000001 0 64 0 64)}
    callee_6 = pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0xC350,
                address=0x1000000000000000000000000000000000000001,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        balance=0x186A0,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(code=bytes.fromhex("600160015500")),
                callee_1: Account(code=bytes.fromhex("600160015200")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "600060006000600060007340000000000000000000000000000000000000046103e8f200"  # noqa: E501
                    )
                ),
                callee_4: Account(code=bytes.fromhex("600160015200")),
                callee_5: Account(
                    code=bytes.fromhex(
                        "60006000600060006000734000000000000000000000000000000000000004620f4240f200"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "604060006040600073100000000000000000000000000000000000000161c350fa00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(code=bytes.fromhex("600160015500")),
                callee_1: Account(code=bytes.fromhex("600160015200")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "600060006000600060007340000000000000000000000000000000000000046103e8f200"  # noqa: E501
                    )
                ),
                callee_4: Account(code=bytes.fromhex("600160015200")),
                callee_5: Account(
                    code=bytes.fromhex(
                        "60006000600060006000734000000000000000000000000000000000000004620f4240f200"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "604060006040600073100000000000000000000000000000000000000161c350fa00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(code=bytes.fromhex("600160015500")),
                callee_1: Account(code=bytes.fromhex("600160015200")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "600060006000600060007340000000000000000000000000000000000000046103e8f200"  # noqa: E501
                    )
                ),
                callee_4: Account(code=bytes.fromhex("600160015200")),
                callee_5: Account(
                    code=bytes.fromhex(
                        "60006000600060006000734000000000000000000000000000000000000004620f4240f200"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "604060006040600073100000000000000000000000000000000000000161c350fa00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(code=bytes.fromhex("600160015500")),
                callee_1: Account(code=bytes.fromhex("600160015200")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "600060006000600060007340000000000000000000000000000000000000046103e8f200"  # noqa: E501
                    )
                ),
                callee_4: Account(code=bytes.fromhex("600160015200")),
                callee_5: Account(
                    code=bytes.fromhex(
                        "60006000600060006000734000000000000000000000000000000000000004620f4240f200"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "604060006040600073100000000000000000000000000000000000000161c350fa00"  # noqa: E501
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
