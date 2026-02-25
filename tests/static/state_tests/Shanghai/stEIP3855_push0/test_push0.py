"""
Ported from:
tests/static/state_tests/Shanghai/stEIP3855_push0/push0Filler.yml

callee code:
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    ... (2030 more instructions)

callee_1 code:
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    push0
    ... (1005 more instructions)

callee_2 code:
    push1 0x02
    push0
    sstore
    push1 0x00
    push1 0x01
    sstore

callee_3 code:
    push1 0x00
    dup1
    dup1
    dup1
    push2 0x0600
    push3 0x0186a0
    staticcall
    push1 0x00
    sstore
    push1 0x01
    dup1
    sstore
    push1 0x01
    push1 0x00
    push1 0x1f
    returndatacopy
    push1 0x00
    mload
    push1 0x02
    sstore
    ... (1 more instructions)

callee_4 code:
    push1 0xff
    push0
    mstore8
    push1 0x01
    push1 0x00
    return

callee_5 code:
    push1 0x04
    jump
    push0
    jumpdest
    push1 0x01
    push0
    sstore
    stop

callee_6 code:
    push1 0x01
    push0
    sstore

contract code:
    push1 0x00
    dup1
    dup1
    dup1
    dup1
    dup1
    calldataload
    push1 0x60
    shr
    push3 0x0186a0
    call
    push1 0x00
    sstore
    push1 0x01
    dup1
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
    ["tests/static/state_tests/Shanghai/stEIP3855_push0/push0Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0000000000000000000000000000000000000200",
        "0000000000000000000000000000000000000300",
        "0000000000000000000000000000000000000700",
        "0000000000000000000000000000000000000400",
        "0000000000000000000000000000000000000500",
        "0000000000000000000000000000000000001000",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5'],
)
@pytest.mark.pre_alloc_mutable
def test_push0(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee = Address("0x0000000000000000000000000000000000000200")
    callee_1 = Address("0x0000000000000000000000000000000000000300")
    callee_2 = Address("0x0000000000000000000000000000000000000400")
    callee_3 = Address("0x0000000000000000000000000000000000000500")
    callee_4 = Address("0x0000000000000000000000000000000000000600")
    callee_5 = Address("0x0000000000000000000000000000000000000700")
    callee_6 = Address("0x0000000000000000000000000000000000001000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR + Op.OR
        + Op.PUSH1[0x1] + Op.SWAP1 + Op.SSTORE
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
        + Op.PUSH0 + Op.PUSH0 + Op.PUSH0
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x2] + Op.PUSH0 + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.SSTORE,
        storage={0x0: 0xa, 0x1: 0xa},
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.PUSH2[0x600]
        + Op.PUSH3[0x186a0] + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.DUP1 + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1f] + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0xff] + Op.PUSH0 + Op.MSTORE8 + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.RETURN
    ),
    )
    pre[callee_5] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x4] + Op.JUMP + Op.PUSH0 + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH0
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_6] = Account(balance=0, nonce=0, code=Op.PUSH1[0x1] + Op.PUSH0 + Op.SSTORE)
    pre[sender] = Account(balance=0x100000000000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.CALLDATALOAD + Op.PUSH1[0x60] + Op.SHR + Op.PUSH3[0x186a0] + Op.CALL
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.DUP1 + Op.SSTORE + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=700000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
