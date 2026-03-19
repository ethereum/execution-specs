"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_CallAskMoreGasOnDepth2ThenTransactionHasFiller.json
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
    "000000000000000000000000ef69a9b2c20255fb7bd2b0ac7d45601a03d570b0",
    "0000000000000000000000008169dc735802bb5c18a777052cf4ce326b5fd725",
]

TX_GAS = [600000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_CallAskMoreGasOnDepth2ThenTransactionHasFiller.json",  # noqa: E501
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
def test_static_call_ask_more_gas_on_depth2_then_transaction_has(
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
        code=Op.SSTORE(key=0x8, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x5044bfb29664a79de12215897c630dc8a11b0b97"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x8, value=0x1)
            + Op.SSTORE(
                key=0x9,
                value=Op.STATICCALL(
                    gas=0x30D40,
                    address=0xE5A4D8074950EC8067D602848B666CA151B09C9F,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x8169dc735802bb5c18a777052cf4ce326b5fd725"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x8, value=Op.GAS) + Op.STOP,
        nonce=0,
        address=Address("0x91b291a3336bc1357388354df18ca061b39e3745"),  # noqa: E501
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
    callee_3 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x8, value=Op.GAS)
            + Op.MSTORE(
                offset=0x9,
                value=Op.STATICCALL(
                    gas=0x927C0,
                    address=0x5044BFB29664A79DE12215897C630DC8A11B0B97,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xd9539c5a3dc4713d47a547bfc9a075bd97287080"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x8, value=Op.GAS)
            + Op.MSTORE(
                offset=0x9,
                value=Op.STATICCALL(
                    gas=0x927C0,
                    address=0x91B291A3336BC1357388354DF18CA061B39E3745,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xe5a4d8074950ec8067d602848b666ca151b09c9f"),  # noqa: E501
    )
    callee_5 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x8, value=0x1)
            + Op.SSTORE(
                key=0x9,
                value=Op.STATICCALL(
                    gas=0x30D40,
                    address=0xD9539C5A3DC4713D47A547BFC9A075BD97287080,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xef69a9b2c20255fb7bd2b0ac7d45601a03d570b0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600160085500")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600855600060006000600073e5a4d8074950ec8067d602848b666ca151b09c9f62030d40fa60095500"  # noqa: E501
                    )
                ),
                callee_2: Account(code=bytes.fromhex("5a60085200")),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000346000355af1600055600160015500"
                    ),
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "5a6008526000600060006000735044bfb29664a79de12215897c630dc8a11b0b97620927c0fa60095200"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "5a60085260006000600060007391b291a3336bc1357388354df18ca061b39e3745620927c0fa60095200"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    storage={8: 1, 9: 1},
                    code=bytes.fromhex(
                        "6001600855600060006000600073d9539c5a3dc4713d47a547bfc9a075bd9728708062030d40fa60095500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600160085500")),
                callee_1: Account(
                    storage={8: 1, 9: 1},
                    code=bytes.fromhex(
                        "6001600855600060006000600073e5a4d8074950ec8067d602848b666ca151b09c9f62030d40fa60095500"  # noqa: E501
                    ),
                ),
                callee_2: Account(code=bytes.fromhex("5a60085200")),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000346000355af1600055600160015500"
                    ),
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "5a6008526000600060006000735044bfb29664a79de12215897c630dc8a11b0b97620927c0fa60095200"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "5a60085260006000600060007391b291a3336bc1357388354df18ca061b39e3745620927c0fa60095200"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "6001600855600060006000600073d9539c5a3dc4713d47a547bfc9a075bd9728708062030d40fa60095500"  # noqa: E501
                    )
                ),
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
