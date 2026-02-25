"""
Puts the point (0, 0) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 0 bytes. Gives the execution 21000 bytes

Ported from:
tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_0_21000_0Filler.json

contract code:
    push1 0x00
    calldataload
    push1 0x1c
    mstore
    push21 0x010000000000000000000000000000000000000000
    push1 0x20
    mstore
    push16 0xffffffffffffffffffffffffffffffff
    push1 0x40
    mstore
    push32 0xffffffffffffffffffffffffffffffff00000000000000000000000000000001
    push1 0x60
    mstore
    push21 0x02540be3fffffffffffffffffffffffffdabf41c00
    push1 0x80
    mstore
    push32 0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400
    push1 0xa0
    mstore
    push4 0x30c8d1da
    ... (97 more instructions)
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
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_0_21000_0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        42592,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_0_21000_0(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 0 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x4a26e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a75f5d92, nonce=5)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=5,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_0_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43168,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_0_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x2aa0e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a76155f2, nonce=2)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=2,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_0_21000_40Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        42912,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_0_21000_40(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 40 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x548ce, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a75eb732, nonce=6)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000002800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=6,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_0_21000_64Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        42912,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_0_21000_64(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 64 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x352ae, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a760ad52, nonce=3)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=3,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_0_21000_80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43040,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_0_21000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x3fa4e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a76005b2, nonce=4)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=4,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_0_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43040,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_0_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x201ee, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a761fe12, nonce=1)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=1,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_0_28000_0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        49592,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_0_28000_0(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 0 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x46150a, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a71deaf6, nonce=102)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=102,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_0_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50168,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_0_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x44aa7f, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a71f5581, nonce=99)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=99,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_0_28000_40Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        49912,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_0_28000_40(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 40 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x468c1a, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a71d73e6, nonce=103)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000002800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=103,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_0_28000_64Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        49912,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_0_28000_64(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 64 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x4523db, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a71edc25, nonce=100)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=100,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_0_28000_80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50040,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_0_28000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x459c31, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a71e63cf, nonce=101)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=101,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_0_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        35000,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_0_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x43f70e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a72008f2, nonce=98)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=98,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_1_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43232,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_1_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x115ece, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a752a132, nonce=24)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=24,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_1_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43104,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_1_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x10b66e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7534992, nonce=23)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=23,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_1_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50232,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_1_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x51a411, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7125bef, nonce=121)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=121,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_1_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50104,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_1_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x512af8, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a712d508, nonce=120)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=120,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_2_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43232,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_2_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x18170e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a74be8f2, nonce=34)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=34,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_2_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43104,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_2_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x176eae, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a74c9152, nonce=33)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=33,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_2_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50232,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_2_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x57ae10, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a70c51f0, nonce=131)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=131,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_2_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        33000,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_2_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x5734f7, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a70ccb09, nonce=130)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0x556a3c03566b04196c534f5612f50167917d72e6ab9b687e10e72dbe0e0f9279},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=130,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_340282366920938463463374607431768211456_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43232,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_340282366920938463463374607431768211456_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x25878e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a73e7872, nonce=54)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=54,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_340282366920938463463374607431768211456_21000_80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43104,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_340282366920938463463374607431768211456_21000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x26306e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a73dcf92, nonce=55)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=55,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_340282366920938463463374607431768211456_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43104,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_340282366920938463463374607431768211456_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x24df2e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a73f20d2, nonce=53)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=53,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_340282366920938463463374607431768211456_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50232,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_340282366920938463463374607431768211456_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x63c20e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7003df2, nonce=151)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=151,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_340282366920938463463374607431768211456_28000_80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50104,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_340282366920938463463374607431768211456_28000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x643baa, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6ffc456, nonce=152)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=152,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_340282366920938463463374607431768211456_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        33000,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_340282366920938463463374607431768211456_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x6348f5, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a700b70b, nonce=150)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xf348aa9f55b137fd60af9c782c04ea7c52c0b193972d1c3aa63d78a110fa2e20},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=150,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_5616_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        45024,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_5616_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x2fa1ae, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7345e52, nonce=69)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=69,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_5616_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        44896,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_5616_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x2ef24e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7350db2, nonce=68)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=68,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_5616_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        52024,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_5616_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x6cd6c8, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6f72938, nonce=166)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=166,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_5616_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        33000,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_5616_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x6c56af, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6f7a951, nonce=165)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xa97df6032909972db52b8144798569bb6169ec8b3e065841da96b3d866aa131e},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=165,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_5617_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        45088,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_5617_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x36a02e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a72d5fd2, nonce=79)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=79,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_5617_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        44960,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_5617_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x35f08e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a72e0f72, nonce=78)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=78,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_5617_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        52088,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_5617_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x732707, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6f0d8f9, nonce=176)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=176,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_5617_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        33000,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_5617_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x72a6ae, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6f15952, nonce=175)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0x289df36ee06bbcd57a9ce2a88d2bcda09715d42f96f7f23c48cdd54e2002f059},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=175,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_9935_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        45216,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_9935_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x3da16e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7265e92, nonce=89)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=89,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_9935_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        45088,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_9935_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x3cf14e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7270eb2, nonce=88)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=88,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_9935_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        52216,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_9935_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x797a06, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6ea85fa, nonce=186)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=186,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_9935_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        52088,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_9935_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x78f92d, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6eb06d3, nonce=185)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=185,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_9_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43232,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_9_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x1ecf4e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a74530b2, nonce=44)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000090000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=44,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_9_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43104,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_9_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x1e26ee, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a745d912, nonce=43)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=43,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_9_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50232,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_9_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x5db80f, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a70647f1, nonce=141)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000090000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=141,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-0_9_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        33000,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_0_9_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 0) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x5d3ef6, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a706c10a, nonce=140)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0x94b60ed39c6fe45858b5931190d93861a2d2538991194cdf9a39b5e83dec0827},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=140,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_0_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43232,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_0_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0xebd4e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a75542b2, nonce=20)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=20,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_0_21000_64Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        42976,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_0_21000_64(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 64 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0xf662e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a75499d2, nonce=21)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=21,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_0_21000_80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43104,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_0_21000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x100e0e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a753f1f2, nonce=22)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=22,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_0_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43104,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_0_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0xe14ee, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a755eb12, nonce=19)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=19,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_0_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50232,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_0_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x4edfd0, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7152030, nonce=117)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=117,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_0_28000_64Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        49976,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_0_28000_64(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 64 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x4fa408, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7145bf8, nonce=118)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=118,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_0_28000_80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50104,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_0_28000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x506740, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a71398c0, nonce=119)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=119,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_0_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50104,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_0_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x4e1c18, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a715e3e8, nonce=116)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=116,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_1_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43296,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_1_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x16c58e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a74d3a72, nonce=32)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=32,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_1_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43168,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_1_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x161cee, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a74de312, nonce=31)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=31,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_1_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50296,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_1_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x56707f, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a70d8f81, nonce=129)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0x556a3c03566b04196c534f5612f50167917d72e6ab9b687e10e72dbe0e0f9279},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=129,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_1_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50168,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_1_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x55ac87, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a70e5379, nonce=128)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0x556a3c03566b04196c534f5612f50167917d72e6ab9b687e10e72dbe0e0f9279},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=128,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_2_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43296,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_2_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x1d7dce, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7468232, nonce=42)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=42,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_2_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43168,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_2_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x1cd52e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7472ad2, nonce=41)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000002"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=41,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_2_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50296,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_2_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x5c7a7e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7078582, nonce=139)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0x94b60ed39c6fe45858b5931190d93861a2d2538991194cdf9a39b5e83dec0827},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=139,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_2_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50168,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_2_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x5bb686, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a708497a, nonce=138)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0x94b60ed39c6fe45858b5931190d93861a2d2538991194cdf9a39b5e83dec0827},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000002"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=138,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_340282366920938463463374607431768211456_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43296,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_340282366920938463463374607431768211456_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x2da08e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7365f72, nonce=66)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=66,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_340282366920938463463374607431768211456_21000_80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43168,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_340282366920938463463374607431768211456_21000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x2e49ae, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a735b652, nonce=67)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=67,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_340282366920938463463374607431768211456_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43168,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_340282366920938463463374607431768211456_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x2cf7ee, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7370812, nonce=65)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=65,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_340282366920938463463374607431768211456_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50296,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_340282366920938463463374607431768211456_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x6ace3f, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6f931c1, nonce=163)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xa97df6032909972db52b8144798569bb6169ec8b3e065841da96b3d866aa131e},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=163,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_340282366920938463463374607431768211456_28000_80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50168,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_340282366920938463463374607431768211456_28000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x6b92b7, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6f86d49, nonce=164)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xa97df6032909972db52b8144798569bb6169ec8b3e065841da96b3d866aa131e},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=164,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_340282366920938463463374607431768211456_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50168,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_340282366920938463463374607431768211456_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x6a0a47, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6f9f5b9, nonce=162)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xa97df6032909972db52b8144798569bb6169ec8b3e065841da96b3d866aa131e},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=162,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_5616_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        45088,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_5616_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x35406e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a72ebf92, nonce=77)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000330644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=77,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_5616_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        44960,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_5616_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x3490ce, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a72f6f32, nonce=76)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000330644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=76,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_5616_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        52088,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_5616_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x71db36, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6f224ca, nonce=174)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0x289df36ee06bbcd57a9ce2a88d2bcda09715d42f96f7f23c48cdd54e2002f059},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000330644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=174,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_5616_28000_96_ParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        51960,
        90000,
        110000,
    ],
    ids=['case0', 'case1', 'case2'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_5616_28000_96_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=10, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0x16e360, nonce=173)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0x289df36ee06bbcd57a9ce2a88d2bcda09715d42f96f7f23c48cdd54e2002f059},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000330644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=173,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_5617_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        45152,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_5617_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x3c40ee, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a727bf12, nonce=87)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000330644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=87,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_5617_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        45024,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_5617_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x3b910e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7286ef2, nonce=86)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000330644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=86,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_5617_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        52152,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_5617_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x782d75, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6ebd28b, nonce=184)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000330644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=184,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_5617_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        52024,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_5617_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x77623d, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6ec9dc3, nonce=183)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000330644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=183,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_9935_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        45280,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_9935_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x43462e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a720b9d2, nonce=97)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=97,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_9935_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        45152,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_9935_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x4295ce, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7216a32, nonce=96)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=96,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_9935_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        52280,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_9935_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x7e8474, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6e57b8c, nonce=194)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0x40c97882e95e71d48d97c8655188333e16470e807a99282b8795064ca6ca4dcf},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=194,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_9935_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        52152,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_9935_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x7db8bc, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6e64744, nonce=193)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0x40c97882e95e71d48d97c8655188333e16470e807a99282b8795064ca6ca4dcf},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=193,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_9_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43296,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_9_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x24360e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a73fc9f2, nonce=52)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000090000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=52,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_9_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43168,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_9_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x238d6e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7407292, nonce=51)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000009"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=51,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_9_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50296,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_9_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x62847d, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7017b83, nonce=149)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xf348aa9f55b137fd60af9c782c04ea7c52c0b193972d1c3aa63d78a110fa2e20},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000090000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=149,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_0-3_9_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50168,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_0_3_9_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (0, 3) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x61c085, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7023f7b, nonce=148)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xf348aa9f55b137fd60af9c782c04ea7c52c0b193972d1c3aa63d78a110fa2e20},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000009"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=148,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_1-2_0_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43296,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_0_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x6990e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a75d66f2, nonce=8)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=8,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_1-2_0_21000_64Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43040,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_0_21000_64(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 64 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x7422e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a75cbdd2, nonce=9)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=9,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_1-2_0_21000_80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43168,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_0_21000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x7ea4e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a75c15b2, nonce=10)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=10,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_1-2_0_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43168,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_0_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x5f06e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a75e0f92, nonce=7)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=7,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_1-2_0_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50296,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_0_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x477dc9, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a71c8237, nonce=105)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=105,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_1-2_0_28000_64Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50040,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_0_28000_64(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 64 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x47f7a5, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a71c085b, nonce=106)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=106,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_1-2_0_28000_80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50168,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_0_28000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x48707b, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a71b8f85, nonce=107)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=107,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_1-2_0_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50168,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_0_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x470470, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a71cfb90, nonce=104)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=104,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_1-2_1_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43360,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_1_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x12b08e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7514f72, nonce=26)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=26,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_1-2_1_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43232,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_1_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x1207ae, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a751f852, nonce=25)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=25,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_1-2_1_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        50360,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_1_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x529746, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a71168ba, nonce=123)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xe90b7bceb6e7df5418fb78d8ee546e97c83a08bbccc01a0644d599ccd2a7c2e0},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=123,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_1-2_1_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        33000,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_1_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x521dad, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a711e253, nonce=122)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=122,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_1-2_2_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43360,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_2_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x1968ce, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a74a9732, nonce=36)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=36,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge2/ecmul_1-2_2_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        43232,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_2_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000000")
    callee_1 = Address("0x0000000000000000000000000000000000000001")
    callee_2 = Address("0x0000000000000000000000000000000000000002")
    callee_3 = Address("0x0000000000000000000000000000000000000003")
    callee_4 = Address("0x0000000000000000000000000000000000000004")
    callee_5 = Address("0x0000000000000000000000000000000000000005")
    callee_6 = Address("0x0000000000000000000000000000000000000006")
    callee_7 = Address("0x0000000000000000000000000000000000000007")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_9] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_10] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(balance=0x18bfee, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a74b4012, nonce=35)
    pre[callee_14] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x1c] + Op.MSTORE
        + Op.PUSH21[0x10000000000000000000000000000000000000000] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffff00000000000000000000000000000001]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH21[0x2540be3fffffffffffffffffffffffffdabf41c00] + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH4[0x30c8d1da] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0xc0]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x40] + Op.PUSH2[0x260]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x7]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x40] + Op.PUSH2[0x240] + Op.MSTORE + Op.PUSH2[0x240]
        + Op.PUSH1[0x60] + Op.DUP1 + Op.PUSH2[0x2c0] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x1b] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x2c0] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x2c0] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000002"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=35,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
