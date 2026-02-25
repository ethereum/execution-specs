"""
EXTCODECOPY edge case https://github.com/ethereum/tests/issues/438

Ported from:
tests/static/state_tests/stExtCodeHash/extCodeCopyBoundsFiller.yml

contract code:
    push2 0x1388
    push21 0x010000000000000000000000000000000000000000
    push1 0x01
    push20 0xedb4c1b7cc80ca722d0a6a35a1f72362e9527221
    extcodecopy
    push1 0x00
    mload
    push1 0x00
    sstore
    push1 0x20
    mload
    push1 0x01
    sstore
    push1 0x0c
    push21 0x010000000000000000000000000000000000000000
    push1 0x01
    push20 0xedb4c1b7cc80ca722d0a6a35a1f72362e9527221
    extcodecopy
    push1 0x00
    mload
    ... (20 more instructions)

callee code:
    push1 0x0c
    push1 0x63
    sstore
    push1 0x0b
    push1 0x63
    sstore
    push1 0x0a
    push1 0x63
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
    ["tests/static/state_tests/stExtCodeHash/extCodeCopyBoundsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_copy_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """EXTCODECOPY edge case https://github.com/ethereum/tests/issues/438."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x28bc9cf1b91da8f552405bfc65dbdd67cb03d8ed")
    callee = Address("0xedb4c1b7cc80ca722d0a6a35a1f72362e9527221")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH2[0x1388] + Op.PUSH21[0x10000000000000000000000000000000000000000]
        + Op.PUSH1[0x1] + Op.PUSH20[0xedb4c1b7cc80ca722d0a6a35a1f72362e9527221]
        + Op.EXTCODECOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0xc]
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x1]
        + Op.PUSH20[0xedb4c1b7cc80ca722d0a6a35a1f72362e9527221] + Op.EXTCODECOPY
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x20]
        + Op.MLOAD + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x5]
        + Op.PUSH1[0x1] + Op.PUSH20[0xedb4c1b7cc80ca722d0a6a35a1f72362e9527221]
        + Op.EXTCODECOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x4] + Op.SSTORE
        + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x5] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0xc] + Op.PUSH1[0x63] + Op.SSTORE + Op.PUSH1[0xb] + Op.PUSH1[0x63]
        + Op.SSTORE + Op.PUSH1[0xa] + Op.PUSH1[0x63] + Op.SSTORE + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=400000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
