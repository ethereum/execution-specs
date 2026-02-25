"""
CALL to ECREC precompile with input that has a valid signature structure but that does not recover a valid key. Specifies a 32 byte output range in memory. ECREC should return an empty response and the 32 byte output range should be left unchanged.

Ported from:
tests/static/state_tests/stPreCompiledContracts2/CallEcrecoverUnrecoverableKeyFiller.json

contract code:
    push32 0xa8b53bdf3306a35a7103ab5504a0c9b492295564b6202b1942a84ef300107281
    push1 0x00
    mstore
    push1 0x1b
    push1 0x20
    mstore
    push32 0x3078356531653033663533636531386237373263636230303933666637316633
    push1 0x40
    mstore
    push32 0x6635336635633735623734646362333161383561613862383839326234653862
    push1 0x60
    mstore
    push32 0x1122334455667788991011121314151617181920212223242526272829303132
    push1 0x80
    mstore
    push1 0x20
    push1 0x80
    push1 0x80
    push1 0x00
    push1 0x00
    ... (9 more instructions)
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
    ["tests/static/state_tests/stPreCompiledContracts2/CallEcrecoverUnrecoverableKeyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_ecrecover_unrecoverable_key(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CALL to ECREC precompile with input that has a valid signature structure but that does not recover a valid key. Specifies a 32 byte output range in memory. ECREC should return an empty response and the 32 byte output range should be left unchanged.."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x85c44d846ed50ac9e384c1b575fd96f3edf5751f")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(
        balance=0x1312d00,
        nonce=0,
        code=(
        Op.PUSH32[0xa8b53bdf3306a35a7103ab5504a0c9b492295564b6202b1942a84ef300107281]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x1b] + Op.PUSH1[0x20] + Op.MSTORE
        + Op.PUSH32[0x3078356531653033663533636531386237373263636230303933666637316633]
        + Op.PUSH1[0x40] + Op.MSTORE
        + Op.PUSH32[0x6635336635633735623734646362333161383561613862383839326234653862]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH32[0x1122334455667788991011121314151617181920212223242526272829303132]
        + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH3[0x493e0] + Op.CALL + Op.POP + Op.PUSH1[0x80] + Op.MLOAD
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=3652240,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
