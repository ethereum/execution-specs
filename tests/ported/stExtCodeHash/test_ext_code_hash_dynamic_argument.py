"""
EXTCODEHASH/EXTCODESIZE with address from a dynamic argument

Ported from:
tests/static/state_tests/stExtCodeHash/extCodeHashDynamicArgumentFiller.json

callee code:
    slt
    callvalue

contract code:
    push1 0x00
    calldataload
    extcodehash
    push1 0x00
    sstore
    push1 0x00
    calldataload
    extcodesize
    push1 0x01
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
    ["tests/static/state_tests/stExtCodeHash/extCodeHashDynamicArgumentFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0000000000000000000000000000000000000000000000000000000000000001",
        "00000000000000000000000076fae819612a29489a1a43208613d8f8557b8898",
        "00000000000000000000000054b3b055779972844a92b30244148fc92092c216",
        "0000000000000000000000005d8645d9535c54ae9d2d01dba614bc0c249b0dee",
        "000000000000000000000000deadbeef00000000000000000000000000000005",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4'],
)
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_dynamic_argument(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """EXTCODEHASH/EXTCODESIZE with address from a dynamic argument."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xdb8d53aa9bdea0a4e33a6cbc0a1a6991e26e57fa")
    callee = Address("0x54b3b055779972844a92b30244148fc92092c216")
    callee_1 = Address("0x5d8645d9535c54ae9d2d01dba614bc0c249b0dee")
    callee_2 = Address("0x76fae819612a29489a1a43208613d8f8557b8898")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[callee] = Account(balance=0xde0b6b3a7640000, nonce=0, code=Op.SLT + Op.CALLVALUE)
    pre[callee_1] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_2] = Account(balance=10, nonce=0)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.EXTCODEHASH + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.EXTCODESIZE + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
        storage={0x0: 0xdeadbeef},
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=tx_data,
        gas_limit=400000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
