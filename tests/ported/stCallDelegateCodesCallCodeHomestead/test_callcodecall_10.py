"""
Ported from:
tests/static/state_tests/stCallDelegateCodesCallCodeHomestead/callcodecall_10Filler.json

callee code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x02
    push20 0xd42cd48f1d9a88f4b75bfb5e46e754c1128bd7fb
    push3 0x03d090
    callcode
    push1 0x01
    sstore
    stop

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x69142b38329c92930601fe8da12dc5866cde11c3
    push3 0x055730
    delegatecall
    push1 0x00
    sstore
    stop

callee_1 code:
    push1 0x01
    push1 0x02
    sstore
    caller
    push1 0x04
    sstore
    callvalue
    push1 0x05
    sstore
    address
    push1 0xe6
    sstore
    origin
    push1 0xe8
    sstore
    calldatasize
    push1 0xec
    sstore
    codesize
    push1 0xee
    ... (5 more instructions)
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
    ["tests/static/state_tests/stCallDelegateCodesCallCodeHomestead/callcodecall_10Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecall_10(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xd26e26d5a4796d450bfa296d70c05f02dbc1a4b9")
    callee = Address("0x69142b38329c92930601fe8da12dc5866cde11c3")
    callee_1 = Address("0xd42cd48f1d9a88f4b75bfb5e46e754c1128bd7fb")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x2] + Op.PUSH20[0xd42cd48f1d9a88f4b75bfb5e46e754c1128bd7fb]
        + Op.PUSH3[0x3d090] + Op.CALLCODE + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x69142b38329c92930601fe8da12dc5866cde11c3] + Op.PUSH3[0x55730]
        + Op.DELEGATECALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SSTORE + Op.CALLER + Op.PUSH1[0x4]
        + Op.SSTORE + Op.CALLVALUE + Op.PUSH1[0x5] + Op.SSTORE + Op.ADDRESS
        + Op.PUSH1[0xe6] + Op.SSTORE + Op.ORIGIN + Op.PUSH1[0xe8] + Op.SSTORE
        + Op.CALLDATASIZE + Op.PUSH1[0xec] + Op.SSTORE + Op.CODESIZE + Op.PUSH1[0xee]
        + Op.SSTORE + Op.GASPRICE + Op.PUSH1[0xf0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=3000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
