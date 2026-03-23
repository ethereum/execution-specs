"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest
contractCreationMakeCallThatAskMoreGasThenTransactionProvidedFiller.json
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
    "6040600060406000600073100000000000000000000000000000000000000161c350f1",
    "6040600060406000600073100000000000000000000000000000000000000161c350f1",
]

TX_GAS = [96000, 60000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCallCreateCallCodeTest/contractCreationMakeCallThatAskMoreGasThenTransactionProvidedFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 1, 0, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_contract_creation_make_call_that_ask_more_gas_then_transaction_provided(  # noqa: E501
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
    # {(SSTORE 1 1)}
    contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000001"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x10C8E0)
    # Source: LLL
    # {(CALL 50000 0x1000000000000000000000000000000000000001 0 0 64 0 64)}
    callee_1 = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0xC350,
                address=0x1000000000000000000000000000000000000001,
                value=0x0,
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
                contract: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6040600060406000600073100000000000000000000000000000000000000161c350f100"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(code=bytes.fromhex("600160015500")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6040600060406000600073100000000000000000000000000000000000000161c350f100"  # noqa: E501
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
