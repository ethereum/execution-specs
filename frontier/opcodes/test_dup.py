"""
abstract: Test DUP
    Test the DUP opcodes.

"""
import pytest

from ethereum_test_forks import Frontier, Homestead
from ethereum_test_tools import Account, Address, Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTestFiller, Storage, TestAddress, Transaction


@pytest.mark.parametrize(
    "dup_opcode",
    [
        Op.DUP1,
        Op.DUP2,
        Op.DUP3,
        Op.DUP4,
        Op.DUP5,
        Op.DUP6,
        Op.DUP7,
        Op.DUP8,
        Op.DUP9,
        Op.DUP10,
        Op.DUP11,
        Op.DUP12,
        Op.DUP13,
        Op.DUP14,
        Op.DUP15,
        Op.DUP16,
    ],
    ids=lambda op: str(op),
)
def test_dup(
    state_test: StateTestFiller,
    fork: str,
    dup_opcode: Op,
):
    """
    Test the DUP1-DUP16 opcodes.

    note: Test case ported from:

        - [ethereum/tests/GeneralStateTests/VMTests/vmTests/dup.json](https://github.com/ethereum/tests/blob/develop/GeneralStateTests/VMTests/vmTests/dup.json)
        by Ori Pomerantz.
    """  # noqa: E501
    env = Environment()
    pre = {TestAddress: Account(balance=1000000000000000000000)}
    post = {}

    account = Address(0x100)

    # Push 0x00 - 0x10 onto the stack
    account_code = b"".join([Op.PUSH1(i) for i in range(0x11)])

    # Use the DUP opcode
    account_code += dup_opcode

    # Save each stack value into different keys in storage
    account_code += b"".join([Op.PUSH1(i) + Op.SSTORE for i in range(0x11)])

    pre[account] = Account(code=account_code)

    tx = Transaction(
        ty=0x0,
        nonce=0,
        to=account,
        gas_limit=500000,
        gas_price=10,
        protected=False if fork in [Frontier, Homestead] else True,
        data="",
    )

    """
    Storage will be structured as follows:

    0x00: 0x10-0x01 (Depending on DUP opcode)
    0x01: 0x10
    0x02: 0x0F
    0x03: 0x0E
    0x04: 0x0D
    0x05: 0x0C
    0x06: 0x0B
    0x07: 0x0A
    0x08: 0x09
    0x09: 0x08
    0x0A: 0x07
    0x0B: 0x06
    0x0C: 0x05
    0x0D: 0x04
    0x0E: 0x03
    0x0F: 0x02
    0x10: 0x01

    DUP1 copies the first element of the stack (0x10).
    DUP16 copies the 16th element of the stack (0x01).
    """
    s: Storage.StorageDictType = dict(zip(range(1, 17), range(16, 0, -1)))
    s[0] = 16 - (dup_opcode.int() - 0x80)

    post[account] = Account(storage=s)

    state_test(env=env, pre=pre, post=post, tx=tx)
