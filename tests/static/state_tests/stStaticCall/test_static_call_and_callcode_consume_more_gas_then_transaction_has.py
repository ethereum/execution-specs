"""
Ported from:
tests/static/state_tests/stStaticCall/static_CallAndCallcodeConsumeMoreGasThenTransactionHasFiller.json

callee code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xfd59abae521384b5731ac657616680219fbc423d
    push3 0x0927c0
    staticcall
    push1 0x09
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xfd59abae521384b5731ac657616680219fbc423d
    push3 0x0927c0
    callcode
    push1 0x0a
    sstore
    stop

callee_1 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x9620801959b49d6d1bd08f0cdafda5d87e900403
    push3 0x0927c0
    staticcall
    push1 0x09
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xfd59abae521384b5731ac657616680219fbc423d
    push3 0x0927c0
    callcode
    push1 0x0a
    sstore
    stop

callee_2 code:
    push1 0x12
    push1 0x00
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
    push1 0x12
    push1 0x00
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
    ["tests/static/state_tests/stStaticCall/static_CallAndCallcodeConsumeMoreGasThenTransactionHasFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000438f316ba8e30f69666a3477a7f5cd26235d3cbb",
        "0000000000000000000000007d77eaf6dc93e2b7b83a8e06314af1ce47cd2596",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_and_callcode_consume_more_gas_then_transaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e")
    callee = Address("0x438f316ba8e30f69666a3477a7f5cd26235d3cbb")
    callee_1 = Address("0x7d77eaf6dc93e2b7b83a8e06314af1ce47cd2596")
    callee_2 = Address("0x9620801959b49d6d1bd08f0cdafda5d87e900403")
    callee_3 = Address("0xfd59abae521384b5731ac657616680219fbc423d")

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
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xfd59abae521384b5731ac657616680219fbc423d] + Op.PUSH3[0x927c0]
        + Op.STATICCALL + Op.PUSH1[0x9] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xfd59abae521384b5731ac657616680219fbc423d] + Op.PUSH3[0x927c0]
        + Op.CALLCODE + Op.PUSH1[0xa] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x9620801959b49d6d1bd08f0cdafda5d87e900403] + Op.PUSH3[0x927c0]
        + Op.STATICCALL + Op.PUSH1[0x9] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xfd59abae521384b5731ac657616680219fbc423d] + Op.PUSH3[0x927c0]
        + Op.CALLCODE + Op.PUSH1[0xa] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x12] + Op.PUSH1[0x0] + Op.MSTORE + Op.STOP,
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLVALUE
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALL + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x12] + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )

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
