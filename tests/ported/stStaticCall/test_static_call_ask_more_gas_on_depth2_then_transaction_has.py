"""
Ported from:
tests/static/state_tests/stStaticCall/static_CallAskMoreGasOnDepth2ThenTransactionHasFiller.json

callee code:
    push1 0x01
    push1 0x08
    sstore
    stop

callee_1 code:
    push1 0x01
    push1 0x08
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xe5a4d8074950ec8067d602848b666ca151b09c9f
    push3 0x030d40
    staticcall
    push1 0x09
    sstore
    stop

callee_2 code:
    gas
    push1 0x08
    mstore
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    callvalue
    push1 0x00
    calldataload
    gas
    call
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee_3 code:
    gas
    push1 0x08
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x5044bfb29664a79de12215897c630dc8a11b0b97
    push3 0x0927c0
    staticcall
    push1 0x09
    mstore
    stop

callee_4 code:
    gas
    push1 0x08
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x91b291a3336bc1357388354df18ca061b39e3745
    push3 0x0927c0
    staticcall
    push1 0x09
    mstore
    stop

callee_5 code:
    push1 0x01
    push1 0x08
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xd9539c5a3dc4713d47a547bfc9a075bd97287080
    push3 0x030d40
    staticcall
    push1 0x09
    sstore
    stop
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stStaticCall/static_CallAskMoreGasOnDepth2ThenTransactionHasFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000ef69a9b2c20255fb7bd2b0ac7d45601a03d570b0",
        "0000000000000000000000008169dc735802bb5c18a777052cf4ce326b5fd725",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_ask_more_gas_on_depth2_then_transaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e")
    callee = Address("0x5044bfb29664a79de12215897c630dc8a11b0b97")
    callee_1 = Address("0x8169dc735802bb5c18a777052cf4ce326b5fd725")
    callee_2 = Address("0x91b291a3336bc1357388354df18ca061b39e3745")
    callee_3 = Address("0xd9539c5a3dc4713d47a547bfc9a075bd97287080")
    callee_4 = Address("0xe5a4d8074950ec8067d602848b666ca151b09c9f")
    callee_5 = Address("0xef69a9b2c20255fb7bd2b0ac7d45601a03d570b0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x8] + Op.SSTORE + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x8] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xe5a4d8074950ec8067d602848b666ca151b09c9f] + Op.PUSH3[0x30d40]
        + Op.STATICCALL + Op.PUSH1[0x9] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(balance=0, nonce=0, code=Op.GAS + Op.PUSH1[0x8] + Op.MSTORE + Op.STOP)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLVALUE
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALL + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x8] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x5044bfb29664a79de12215897c630dc8a11b0b97] + Op.PUSH3[0x927c0]
        + Op.STATICCALL + Op.PUSH1[0x9] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x8] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x91b291a3336bc1357388354df18ca061b39e3745] + Op.PUSH3[0x927c0]
        + Op.STATICCALL + Op.PUSH1[0x9] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x8] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xd9539c5a3dc4713d47a547bfc9a075bd97287080] + Op.PUSH3[0x30d40]
        + Op.STATICCALL + Op.PUSH1[0x9] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=tx_data,
        gas_limit=600000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
