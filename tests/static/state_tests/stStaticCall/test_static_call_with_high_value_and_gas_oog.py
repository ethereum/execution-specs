"""
Ported from:
tests/static/state_tests/stStaticCall/static_callWithHighValueAndGasOOGFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x07a120
    call
    stop

callee code:
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    push1 0x00
    mstore
    push32 0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa
    push1 0x20
    mstore
    push1 0x02
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xd5d9e9e0158920b17b6df82fac474b3e2691ee99
    push12 0xffffffffffffffffffffffff
    staticcall
    push1 0x00
    sstore
    push1 0x00
    mload
    push1 0x01
    sstore
    stop

callee_1 code:
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    push1 0x00
    mstore
    push32 0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa
    push1 0x20
    mstore
    push1 0x02
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xd2b07d10e28b46411527b841f0e0382a8e3bcb80
    push12 0xffffffffffffffffffffffff
    staticcall
    push1 0x00
    sstore
    push1 0x00
    mload
    push1 0x01
    sstore
    stop

callee_2 code:
    push3 0x2fffff
    push1 0x00
    sha3
    stop

callee_3 code:
    push1 0x37
    push1 0x00
    mstore8
    push1 0x02
    push1 0x00
    return
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
    ["tests/static/state_tests/stStaticCall/static_callWithHighValueAndGasOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000a5b789cb3b73deb59cef5b261568362db2f967dd",
        "000000000000000000000000be9c847927d7e832ff5655392c160933d99cb4e8",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_with_high_value_and_gas_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x46fcfdfd17a5789b6ab6d7e23f33f4eadecfb5ad")
    callee = Address("0xa5b789cb3b73deb59cef5b261568362db2f967dd")
    callee_1 = Address("0xbe9c847927d7e832ff5655392c160933d99cb4e8")
    callee_2 = Address("0xd2b07d10e28b46411527b841f0e0382a8e3bcb80")
    callee_3 = Address("0xd5d9e9e0158920b17b6df82fac474b3e2691ee99")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x7a120]
        + Op.CALL + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH32[0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x0] + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH20[0xd5d9e9e0158920b17b6df82fac474b3e2691ee99]
        + Op.PUSH12[0xffffffffffffffffffffffff] + Op.STATICCALL + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH32[0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x0] + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH20[0xd2b07d10e28b46411527b841f0e0382a8e3bcb80]
        + Op.PUSH12[0xffffffffffffffffffffffff] + Op.STATICCALL + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x1, 0x1: 0x1},
    )
    pre[callee_2] = Account(
        balance=23,
        nonce=0,
        code=Op.PUSH3[0x2fffff] + Op.PUSH1[0x0] + Op.SHA3 + Op.STOP,
    )
    pre[callee_3] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PUSH1[0x37] + Op.PUSH1[0x0] + Op.MSTORE8 + Op.PUSH1[0x2] + Op.PUSH1[0x0]
        + Op.RETURN
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
        gas_limit=3000000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
