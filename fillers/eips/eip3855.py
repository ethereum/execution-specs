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
    code = bytes(
        [
            0x60,  # PUSH1
            0x01,
            0x5F,  # PUSH0
            0x55,  # SSTORE
        ]
    )

    pre[addr_1] = Account(code=code)
    post[addr_1] = Account(storage={0x00: 0x01})

    yield StateTest(
        env=env, pre=pre, post=post, txs=[tx], name="push0_key_sstore"
    )

    """
    Test case 2: Fill stack with PUSH0, then OR all values and save using
    SSTORE
    """
    code = bytes([0x5F] * 1024)  # PUSH0
    code += bytes([0x17] * 1023)  # OR
    code += bytes(
        [
            0x60,  # PUSH1
            0x01,
            0x90,  # SWAP1
            0x55,  # SSTORE
        ]
    )

    pre[addr_1] = Account(code=code)
    post[addr_1] = Account(storage={0x00: 0x01})

    yield StateTest(
        env=env, pre=pre, post=post, txs=[tx], name="push0_fill_stack"
    )

    """
    Test case 3: Stack overflow by using PUSH0 1025 times
    """
    code = bytes(
        [
            0x60,  # PUSH1
            0x01,
            0x5F,  # PUSH0
            0x55,  # SSTORE
        ]
    )
    code += bytes([0x5F] * 1025)  # PUSH0, stack overflow

    pre[addr_1] = Account(code=code)
    post[addr_1] = Account(storage={0x00: 0x00})

    yield StateTest(
        env=env, pre=pre, post=post, txs=[tx], name="push0_stack_overflow"
    )

    """
    Test case 4: Update already existing storage value
    """
    code = bytes(
        [
            0x60,  # PUSH1
            0x02,
            0x5F,  # PUSH0
            0x55,  # SSTORE
            0x5F,  # PUSH0
            0x60,  # PUSH1
            0x01,
            0x55,  # SSTORE
        ]
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
    code_2 = bytes(
        [
            0x60,  # PUSH1
            0xFF,
            0x5F,  # PUSH0
            0x53,  # MSTORE8
            0x60,  # PUSH1
            0x01,
            0x60,  # PUSH1
            0x00,
            0xF3,  # RETURN
        ]
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
    code = bytes(
        [
            0x60,  # PUSH1
            0x04,
            0x56,  # JUMP
            0x5F,  # PUSH0
            0x5B,  # JUMPDEST
            0x60,  # PUSH1
            0x01,
            0x5F,  # PUSH0
            0x55,  # SSTORE
            0x00,  # STOP
        ]
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
        code=bytes([0x5F]),  # PUSH0
        extra_stack_items=1,
    )

    pre[addr_1] = Account(code=code)
    post[addr_1] = Account(storage={0x00: 0x02})

    yield StateTest(
        env=env, pre=pre, post=post, txs=[tx], name="push0_gas_cost"
    )
