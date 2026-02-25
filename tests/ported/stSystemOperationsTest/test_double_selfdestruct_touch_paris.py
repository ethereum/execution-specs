"""
A single contract can execute SELFDESTRUCT multiple times using by being called
multiple times. The second and later SELFDESTRUCTs have little effect but can
touch some new beneficiary addresses.


Ported from:
tests/static/state_tests/stSystemOperationsTest/doubleSelfdestructTouch_ParisFiller.yml

callee code:
    push1 0x01
    push1 0x00
    sload
    add
    dup1
    push1 0x00
    sstore
    sload
    selfdestruct

contract code:
    push1 0x00
    dup1
    dup1
    dup1
    callvalue
    dup1
    push1 0x01
    shr
    swap1
    dup3
    dup1
    dup1
    dup1
    dup6
    push20 0x29e4504a3d2a0e0ae0ebbbefedd4570639b3ebee
    push3 0x011170
    call
    pop
    sub
    push20 0x29e4504a3d2a0e0ae0ebbbefedd4570639b3ebee
    ... (3 more instructions)
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
    ["tests/static/state_tests/stSystemOperationsTest/doubleSelfdestructTouch_ParisFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_value",
    [
        0,
        1,
        2,
    ],
    ids=['case0', 'case1', 'case2'],
)
@pytest.mark.pre_alloc_mutable
def test_double_selfdestruct_touch_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
) -> None:
    """A single contract can execute SELFDESTRUCT multiple times using by being called
multiple times. The second and later SELFDESTRUCTs have little effect but can
touch some new beneficiary addresses.
."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x3a164fee089b5ce1f6f7071e90f56caeb7f19b1d")
    contract = Address("0x8ec7465877d3957084dc907c0f6d8f2911a17a52")
    callee = Address("0x29e4504a3d2a0e0ae0ebbbefedd4570639b3ebee")
    callee_1 = Address("0x68fa59e127b7526718eb0a4e113df5793628cb91")
    callee_2 = Address("0x76fae819612a29489a1a43208613d8f8557b8898")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=999,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.ADD + Op.DUP1 + Op.PUSH1[0x0]
        + Op.SSTORE + Op.SLOAD + Op.SELFDESTRUCT
    ),
        storage={0x0: 0x0, 0x1: 0x68fa59e127b7526718eb0a4e113df5793628cb91, 0x2: 0x76fae819612a29489a1a43208613d8f8557b8898},
    )
    pre[sender] = Account(balance=0x5f5e102, nonce=0)
    pre[callee_1] = Account(balance=10, nonce=0)
    pre[callee_2] = Account(balance=10, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.CALLVALUE + Op.DUP1
        + Op.PUSH1[0x1] + Op.SHR + Op.SWAP1 + Op.DUP3 + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.DUP6 + Op.PUSH20[0x29e4504a3d2a0e0ae0ebbbefedd4570639b3ebee]
        + Op.PUSH3[0x11170] + Op.CALL + Op.POP + Op.SUB
        + Op.PUSH20[0x29e4504a3d2a0e0ae0ebbbefedd4570639b3ebee] + Op.PUSH3[0x11170]
        + Op.CALL + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xe92c121432830128ca66d3d8c4e6d8d96cc4befa7c612d28415082eb3c8339c5"
        ),
        to=contract,
        data=b"",
        gas_limit=10000000,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
