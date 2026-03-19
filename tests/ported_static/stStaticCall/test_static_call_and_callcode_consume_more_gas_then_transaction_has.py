"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_CallAndCallcodeConsumeMoreGasThenTransactionHasFiller.json
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
    "000000000000000000000000438f316ba8e30f69666a3477a7f5cd26235d3cbb",
    "0000000000000000000000007d77eaf6dc93e2b7b83a8e06314af1ce47cd2596",
]

TX_GAS = [600000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_CallAndCallcodeConsumeMoreGasThenTransactionHasFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call_and_callcode_consume_more_gas_then_transaction_has(
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
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x9,
                value=Op.STATICCALL(
                    gas=0x927C0,
                    address=0xFD59ABAE521384B5731AC657616680219FBC423D,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0xA,
                value=Op.CALLCODE(
                    gas=0x927C0,
                    address=0xFD59ABAE521384B5731AC657616680219FBC423D,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x438f316ba8e30f69666a3477a7f5cd26235d3cbb"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x9,
                value=Op.STATICCALL(
                    gas=0x927C0,
                    address=0x9620801959B49D6D1BD08F0CDAFDA5D87E900403,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0xA,
                value=Op.CALLCODE(
                    gas=0x927C0,
                    address=0xFD59ABAE521384B5731AC657616680219FBC423D,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x7d77eaf6dc93e2b7b83a8e06314af1ce47cd2596"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x12) + Op.STOP,
        nonce=0,
        address=Address("0x9620801959b49d6d1bd08f0cdafda5d87e900403"),  # noqa: E501
    )
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
    pre[sender] = Account(balance=0xE8D4A51000)
    callee_3 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x12) + Op.STOP,
        nonce=0,
        address=Address("0xfd59abae521384b5731ac657616680219fbc423d"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600073fd59abae521384b5731ac657616680219fbc423d620927c0fa6009556000600060006000600073fd59abae521384b5731ac657616680219fbc423d620927c0f2600a5500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000600060006000739620801959b49d6d1bd08f0cdafda5d87e900403620927c0fa6009556000600060006000600073fd59abae521384b5731ac657616680219fbc423d620927c0f2600a5500"  # noqa: E501
                    )
                ),
                callee_2: Account(code=bytes.fromhex("601260005200")),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000346000355af1600055600160015500"
                    )
                ),
                callee_3: Account(code=bytes.fromhex("601260005500")),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600073fd59abae521384b5731ac657616680219fbc423d620927c0fa6009556000600060006000600073fd59abae521384b5731ac657616680219fbc423d620927c0f2600a5500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    storage={0: 18, 9: 1, 10: 1},
                    code=bytes.fromhex(
                        "6000600060006000739620801959b49d6d1bd08f0cdafda5d87e900403620927c0fa6009556000600060006000600073fd59abae521384b5731ac657616680219fbc423d620927c0f2600a5500"  # noqa: E501
                    ),
                ),
                callee_2: Account(code=bytes.fromhex("601260005200")),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000346000355af1600055600160015500"
                    ),
                ),
                callee_3: Account(code=bytes.fromhex("601260005500")),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
