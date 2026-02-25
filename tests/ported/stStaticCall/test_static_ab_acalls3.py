"""
Ported from:
tests/static/state_tests/stStaticCall/static_ABAcalls3Filler.json

callee code:
    push1 0x01
    push1 0x00
    sload
    add
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xe40c059876e334b99a5d199693978c39bedb690d
    push3 0x0186a0
    gas
    sub
    staticcall
    stop

callee_1 code:
    push1 0x01
    push1 0x00
    sload
    add
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xe278f8058bef1396c2b1df4d1dc4b65233133c57
    push3 0x0186a0
    gas
    sub
    staticcall
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

callee_2 code:
    push1 0x01
    push1 0x00
    sload
    add
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x407da20797d4e89c2f4e48c502385c1514d9fa52
    push3 0x0186a0
    gas
    sub
    staticcall
    stop

callee_3 code:
    push1 0x01
    push1 0x00
    sload
    add
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x0b1f7380db647f1d85565b28978ba83861b99965
    push3 0x0186a0
    gas
    sub
    staticcall
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
    ["tests/static/state_tests/stStaticCall/static_ABAcalls3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000407da20797d4e89c2f4e48c502385c1514d9fa52",
        "000000000000000000000000e40c059876e334b99a5d199693978c39bedb690d",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_ab_acalls3(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e")
    callee = Address("0x0b1f7380db647f1d85565b28978ba83861b99965")
    callee_1 = Address("0x407da20797d4e89c2f4e48c502385c1514d9fa52")
    callee_2 = Address("0xe278f8058bef1396c2b1df4d1dc4b65233133c57")
    callee_3 = Address("0xe40c059876e334b99a5d199693978c39bedb690d")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xe40c059876e334b99a5d199693978c39bedb690d] + Op.PUSH3[0x186a0]
        + Op.GAS + Op.SUB + Op.STATICCALL + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xfa3e8,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xe278f8058bef1396c2b1df4d1dc4b65233133c57] + Op.PUSH3[0x186a0]
        + Op.GAS + Op.SUB + Op.STATICCALL + Op.STOP
    ),
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
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x407da20797d4e89c2f4e48c502385c1514d9fa52] + Op.PUSH3[0x186a0]
        + Op.GAS + Op.SUB + Op.STATICCALL + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xfa3e8,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xb1f7380db647f1d85565b28978ba83861b99965] + Op.PUSH3[0x186a0]
        + Op.GAS + Op.SUB + Op.STATICCALL + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=tx_data,
        gas_limit=10000000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
