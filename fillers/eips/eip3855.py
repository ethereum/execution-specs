"""
Test EIP-3855: PUSH0 Instruction
EIP: https://eips.ethereum.org/EIPS/eip-3855
Source tests: https://github.com/ethereum/tests/pull/1033
"""

from ethereum_test_tools import (
    Account,
    CodeGasMeasure,
    Environment,
    StateTest,
    TestAddress,
    Transaction,
    Yul,
    test_from,
    to_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op


@test_from(fork="shanghai", eips=[3855])
def test_push0(fork):
    """
    Test push0 opcode.
    """
    env = Environment()

    pre = {TestAddress: Account(balance=1000000000000000000000)}
    post = {}

    addr_1 = to_address(0x100)
    addr_2 = to_address(0x200)

    # Entry point for all test cases is the same address
    tx = Transaction(
        to=addr_1,
        gas_limit=100000,
    )

    """
    Test case 1: Simple PUSH0 as key to SSTORE
    """
    code = Op.PUSH1(1) + Op.PUSH0 + Op.SSTORE

    pre[addr_1] = Account(code=code)
    post[addr_1] = Account(storage={0x00: 0x01})

    yield StateTest(
        env=env, pre=pre, post=post, txs=[tx], name="push0_key_sstore"
    )

    """
    Test case 2: Fill stack with PUSH0, then OR all values and save using
    SSTORE
    """
    code = Op.PUSH0 * 1024
    code += Op.OR * 1023
    code += Op.PUSH1(1) + Op.SWAP1 + Op.SSTORE

    pre[addr_1] = Account(code=code)
    post[addr_1] = Account(storage={0x00: 0x01})

    yield StateTest(
        env=env, pre=pre, post=post, txs=[tx], name="push0_fill_stack"
    )

    """
    Test case 3: Stack overflow by using PUSH0 1025 times
    """
    code = Op.PUSH1(1) + Op.PUSH0 + Op.SSTORE
    code += Op.PUSH0 * 1025

    pre[addr_1] = Account(code=code)
    post[addr_1] = Account(storage={0x00: 0x00})

    yield StateTest(
        env=env, pre=pre, post=post, txs=[tx], name="push0_stack_overflow"
    )

    """
    Test case 4: Update already existing storage value
    """
    code = (
        Op.PUSH1(2) + Op.PUSH0 + Op.SSTORE + Op.PUSH0 + Op.PUSH1(1) + Op.SSTORE
    )

    pre[addr_1] = Account(code=code, storage={0x00: 0x0A, 0x01: 0x0A})
    post[addr_1] = Account(storage={0x00: 0x02, 0x01: 0x00})

    yield StateTest(
        env=env, pre=pre, post=post, txs=[tx], name="push0_storage_overwrite"
    )

    """
    Test case 5: PUSH0 during staticcall
    """
    code_1 = Yul(
        """
        {
            sstore(0, staticcall(100000, 0x200, 0, 0, 0, 0))
            sstore(0, 1)
            returndatacopy(0x1f, 0, 1)
            sstore(1, mload(0))
        }
        """
    )
    code_2 = (
        Op.PUSH1(0xFF)
        + Op.PUSH0
        + Op.MSTORE8
        + Op.PUSH1(1)
        + Op.PUSH1(0)
        + Op.RETURN
    )

    pre[addr_1] = Account(code=code_1)
    pre[addr_2] = Account(code=code_2)
    post[addr_1] = Account(storage={0x00: 0x01, 0x01: 0xFF})

    yield StateTest(
        env=env, pre=pre, post=post, txs=[tx], name="push0_during_staticcall"
    )

    del pre[addr_2]

    """
    Test case 6: Jump to a JUMPDEST next to a PUSH0, must succeed.
    """
    code = (
        Op.PUSH1(4)
        + Op.JUMP
        + Op.PUSH0
        + Op.JUMPDEST
        + Op.PUSH1(1)
        + Op.PUSH0
        + Op.SSTORE
        + Op.STOP
    )

    pre[addr_1] = Account(code=code)
    post[addr_1] = Account(storage={0x00: 0x01})

    yield StateTest(
        env=env, pre=pre, post=post, txs=[tx], name="push0_before_jumpdest"
    )

    """
    Test case 7: PUSH0 gas cost
    """
    code = CodeGasMeasure(
        code=Op.PUSH0,
        extra_stack_items=1,
    )

    pre[addr_1] = Account(code=code)
    post[addr_1] = Account(storage={0x00: 0x02})

    yield StateTest(
        env=env, pre=pre, post=post, txs=[tx], name="push0_gas_cost"
    )
