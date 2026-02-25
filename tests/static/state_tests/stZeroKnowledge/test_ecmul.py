"""
Puts the point (1, 2) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes

Ported from:
tests/static/state_tests/stZeroKnowledge/ecmul_1-2_2_28000_128Filler.json

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
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_2_28000_128Filler.json"],
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
def test_ecmul_1_2_2_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x5f5e100, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0x5f5e100, nonce=133)
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
        storage={0x0: 0x8a5045bc7a493061be89fdbc32ea8ae69e8d8b55ebe445fa41fa534b1543ab50},
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
        nonce=133,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_2_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        30000,
        90000,
        110000,
        200000,
        40000,
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_2_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x5827ac, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a70bd854, nonce=132)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000002"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=132,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_340282366920938463463374607431768211456_21000_128Filler.json"],
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
def test_ecmul_1_2_340282366920938463463374607431768211456_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x2781ae, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a73c7e52, nonce=57)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=57,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_340282366920938463463374607431768211456_21000_80Filler.json"],
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
def test_ecmul_1_2_340282366920938463463374607431768211456_21000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x282b0e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a73bd4f2, nonce=58)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=58,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_340282366920938463463374607431768211456_21000_96Filler.json"],
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
def test_ecmul_1_2_340282366920938463463374607431768211456_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x26d8ce, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a73d2732, nonce=56)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=56,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_340282366920938463463374607431768211456_28000_128Filler.json"],
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
def test_ecmul_1_2_340282366920938463463374607431768211456_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x652e5c, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6fed1a4, nonce=154)
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
        storage={0x0: 0x467d6413c98fb304cd61014865afdb7b3b81fa53f7ef4046e6a833162c5bb5c},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=154,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_340282366920938463463374607431768211456_28000_80Filler.json"],
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
def test_ecmul_1_2_340282366920938463463374607431768211456_28000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x65a878, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6fe5788, nonce=155)
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
        storage={0x0: 0x467d6413c98fb304cd61014865afdb7b3b81fa53f7ef4046e6a833162c5bb5c},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=155,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_340282366920938463463374607431768211456_28000_96Filler.json"],
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
def test_ecmul_1_2_340282366920938463463374607431768211456_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x64b4c3, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6ff4b3d, nonce=153)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=153,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_5616_21000_128Filler.json"],
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
def test_ecmul_1_2_5616_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x31016e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a732fe92, nonce=71)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000230644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=71,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_5616_21000_96Filler.json"],
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
def test_ecmul_1_2_5616_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x30518e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a733ae72, nonce=70)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000230644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=70,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_5616_28000_128Filler.json"],
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
def test_ecmul_1_2_5616_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x6dd7fd, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6f62803, nonce=168)
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
        storage={0x0: 0xac1de87792e425a22b81bdf624dc1b24fee26f16e9a879172aebc261cc51a2fe},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000230644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=168,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_5617_21000_128Filler.json"],
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
def test_ecmul_1_2_5617_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x38006e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a72bff92, nonce=81)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000230644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=81,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_5617_21000_96Filler.json"],
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
def test_ecmul_1_2_5617_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x37504e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a72cafb2, nonce=80)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000230644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=80,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_5617_28000_128Filler.json"],
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
def test_ecmul_1_2_5617_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x7428bc, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6efd744, nonce=178)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000230644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=178,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_5617_28000_96Filler.json"],
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
def test_ecmul_1_2_5617_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x73a7e3, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6f0581d, nonce=177)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000230644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=177,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_616_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        30000,
        90000,
        110000,
        200000,
        40000,
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_616_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x6d5764, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6f6a89c, nonce=167)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000230644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=167,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_9935_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        45344,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_9935_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x3f02ae, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a724fd52, nonce=91)
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
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=91,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_9935_21000_96Filler.json"],
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
def test_ecmul_1_2_9935_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x3e520e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a725adf2, nonce=90)
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
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=90,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_9935_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        52344,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_9935_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x7a7cbb, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6e98345, nonce=188)
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
        storage={0x0: 0xa34b6e4f9c282ff62c1e6f53fd92ad8efd8346d9866333a95ab4506a8158afc7},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=188,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_9935_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        31736,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_2_9935_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x79fb62, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6ea049e, nonce=187)
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
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=187,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_9_21000_128Filler.json"],
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
def test_ecmul_1_2_9_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x20210e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a743def2, nonce=46)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000090000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=46,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_9_21000_96Filler.json"],
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
def test_ecmul_1_2_9_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x1f782e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a74487d2, nonce=45)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000009"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=45,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_9_28000_128Filler.json"],
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
def test_ecmul_1_2_9_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x5eab44, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a70554bc, nonce=143)
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
        storage={0x0: 0xc7b29565a7dd9915e6fd86d026aef2fc454506bae7f90e2f2bec5f25f01b2d95},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000090000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=143,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-2_9_28000_96Filler.json"],
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
def test_ecmul_1_2_9_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 2) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x5e31ab, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a705ce55, nonce=142)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000009"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=142,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_0_21000_128Filler.json"],
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
def test_ecmul_1_3_0_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0xc1b0e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a757e4f2, nonce=16)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=16,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_0_21000_64Filler.json"],
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
def test_ecmul_1_3_0_21000_64(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 64 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0xcc42e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7573bd2, nonce=17)
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
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000003"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=17,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_0_21000_80Filler.json"],
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
def test_ecmul_1_3_0_21000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0xd6c4e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a75693b2, nonce=18)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=18,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_0_21000_96Filler.json"],
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
def test_ecmul_1_3_0_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0xb726e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7588d92, nonce=15)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=15,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_0_28000_128Filler.json"],
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
def test_ecmul_1_3_0_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x4bd030, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7182fd0, nonce=113)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=113,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_0_28000_64Filler.json"],
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
def test_ecmul_1_3_0_28000_64(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 64 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x4c94a8, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7176b58, nonce=114)
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
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000003"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=114,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_0_28000_80_ParisFiller.json"],
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
def test_ecmul_1_3_0_28000_80_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 28000 bytes."""
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
    pre[sender] = Account(balance=0x5f5e100, nonce=115)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=115,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_0_28000_96Filler.json"],
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
def test_ecmul_1_3_0_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x4b0c38, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a718f3c8, nonce=112)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=112,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_1_21000_128Filler.json"],
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
def test_ecmul_1_3_1_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x15738e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a74e8c72, nonce=30)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=30,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_1_21000_96Filler.json"],
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
def test_ecmul_1_3_1_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x14caae, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a74f3552, nonce=29)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=29,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_1_28000_128Filler.json"],
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
def test_ecmul_1_3_1_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x54e7cf, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a70f1831, nonce=127)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=127,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_1_28000_96Filler.json"],
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
def test_ecmul_1_3_1_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x542397, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a70fdc69, nonce=126)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=126,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_2_21000_128Filler.json"],
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
def test_ecmul_1_3_2_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x1c2bce, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a747d432, nonce=40)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=40,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_2_21000_96Filler.json"],
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
def test_ecmul_1_3_2_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x1b82ee, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7487d12, nonce=39)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000002"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=39,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_2_28000_128Filler.json"],
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
def test_ecmul_1_3_2_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x5af1ce, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7090e32, nonce=137)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=137,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_2_28000_96Filler.json"],
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
def test_ecmul_1_3_2_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x5a2d96, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a709d26a, nonce=136)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000002"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=136,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_340282366920938463463374607431768211456_21000_128Filler.json"],
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
def test_ecmul_1_3_340282366920938463463374607431768211456_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x2ba5ae, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7385a52, nonce=63)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=63,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_340282366920938463463374607431768211456_21000_80Filler.json"],
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
def test_ecmul_1_3_340282366920938463463374607431768211456_21000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x2c4f0e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a737b0f2, nonce=64)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=64,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_340282366920938463463374607431768211456_21000_96Filler.json"],
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
def test_ecmul_1_3_340282366920938463463374607431768211456_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x2afcce, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7390332, nonce=62)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=62,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_340282366920938463463374607431768211456_28000_128Filler.json"],
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
def test_ecmul_1_3_340282366920938463463374607431768211456_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x688157, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6fb7ea9, nonce=160)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=160,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_340282366920938463463374607431768211456_28000_80Filler.json"],
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
def test_ecmul_1_3_340282366920938463463374607431768211456_28000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x69460f, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6fab9f1, nonce=161)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=161,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_340282366920938463463374607431768211456_28000_96Filler.json"],
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
def test_ecmul_1_3_340282366920938463463374607431768211456_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x67bd1f, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6fc42e1, nonce=159)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=159,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_5616_21000_128Filler.json"],
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
def test_ecmul_1_3_5616_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x33e06e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7301f92, nonce=75)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000330644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=75,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_5616_21000_96Filler.json"],
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
def test_ecmul_1_3_5616_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x33308e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a730cf72, nonce=74)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000330644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=74,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_5616_28000_128Filler.json"],
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
def test_ecmul_1_3_5616_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x704486, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6f3bb7a, nonce=172)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000330644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=172,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_5616_28000_96Filler.json"],
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
def test_ecmul_1_3_5616_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x6f794e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6f486b2, nonce=171)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000330644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=171,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_5617_21000_128Filler.json"],
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
def test_ecmul_1_3_5617_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x3ae06e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7291f92, nonce=85)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000330644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=85,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_5617_21000_96Filler.json"],
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
def test_ecmul_1_3_5617_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x3a304e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a729cfb2, nonce=84)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000330644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=84,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_5617_28000_128Filler.json"],
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
def test_ecmul_1_3_5617_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x769645, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6ed69bb, nonce=182)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000330644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=182,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_5617_28000_96Filler.json"],
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
def test_ecmul_1_3_5617_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x75cacd, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6ee3533, nonce=181)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000330644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=181,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_9935_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        45344,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_3_9935_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x41e4ae, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7221b52, nonce=95)
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
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000003ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=95,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_9935_21000_96Filler.json"],
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
def test_ecmul_1_3_9935_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x41340e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a722cbf2, nonce=94)
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
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000003ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=94,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_9935_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        52344,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_1_3_9935_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x7cec44, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6e713bc, nonce=192)
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
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000003ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=192,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_9935_28000_96Filler.json"],
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
def test_ecmul_1_3_9935_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x7c204c, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6e7dfb4, nonce=191)
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
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000003ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=191,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_9_21000_128Filler.json"],
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
def test_ecmul_1_3_9_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x22e40e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7411bf2, nonce=50)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000090000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=50,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_9_21000_96Filler.json"],
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
def test_ecmul_1_3_9_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x223b2e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a741c4d2, nonce=49)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000009"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=49,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_9_28000_128Filler.json"],
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
def test_ecmul_1_3_9_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x60fbcd, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7030433, nonce=147)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000090000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=147,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_1-3_9_28000_96Filler.json"],
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
def test_ecmul_1_3_9_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (1, 3) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x603795, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a703c86b, nonce=146)
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
        data=bytes.fromhex("30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000009"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=146,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_0_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        47200,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_0_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x94ace, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a75ab532, nonce=12)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000801a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=12,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_0_21000_64Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        46944,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_0_21000_64(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 64 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0xa032e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a759fcd2, nonce=13)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000401a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f6"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=13,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_0_21000_80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        47072,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_0_21000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0xaba8e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7594572, nonce=14)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000501a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=14,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_0_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        47072,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_0_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x892ee, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a75b6d12, nonce=11)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000601a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=11,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_0_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        54200,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_0_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x49726d, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a71a8d93, nonce=109)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000801a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=109,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_0_28000_64Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        53944,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_0_28000_64(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 64 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x49fb89, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a71a0477, nonce=110)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000401a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f6"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=110,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_0_28000_80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        54072,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_0_28000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x4a839f, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7197c61, nonce=111)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000501a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=111,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_0_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        54072,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_0_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 0 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x48e9d4, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a71b162c, nonce=108)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000601a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=108,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_1456_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        47264,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_1456_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x298c0e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a73a73f2, nonce=60)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000801a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f600000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=60,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_1456_21000_80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        47136,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_1456_21000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x2a44ae, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a739bb52, nonce=61)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000501a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=61,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_1456_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        47136,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_1456_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x28d3ee, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a73b2c12, nonce=59)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000601a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=59,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_1456_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        54264,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_1456_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x66aaea, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6fd5516, nonce=157)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000801a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f600000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=157,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_1456_28000_80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        54136,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_1456_28000_80(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 80 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x673446, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6fccbba, nonce=158)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000501a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=158,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_1456_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        34000,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_1456_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 340282366920938463463374607431768211456 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x662211, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6fdddef, nonce=156)
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
        storage={0x0: 0x467d6413c98fb304cd61014865afdb7b3b81fa53f7ef4046e6a833162c5bb5c},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000601a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000100000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=156,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_1_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        47264,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_1_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x14120e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a74fedf2, nonce=28)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000801a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f600000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=28,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_1_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        47136,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_1_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x1359ee, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a750a612, nonce=27)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000601a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000000000000000000000000000000000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=27,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_1_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        54264,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_1_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x539a3b, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a71065c5, nonce=125)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000801a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f600000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=125,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_1_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        34000,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_1_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 1 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x531162, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a710ee9e, nonce=124)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000601a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000000000000000000000000000000000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=124,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_2_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        47264,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_2_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x1aca4e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a74935b2, nonce=38)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000801a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f600000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=38,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_2_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        47136,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_2_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x1a122e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a749edd2, nonce=37)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000601a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000000000000000000000000000000000002"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=37,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_2_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        54264,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_2_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x59a43a, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a70a5bc6, nonce=135)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000801a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f600000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=135,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_2_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        33656,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_2_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 2 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x591b61, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a70ae49f, nonce=134)
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
        storage={0x0: 0x8a5045bc7a493061be89fdbc32ea8ae69e8d8b55ebe445fa41fa534b1543ab50},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000601a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000000000000000000000000000000000002"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=134,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_5616_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        49056,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_5616_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x3270ee, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7318f12, nonce=73)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000801a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f630644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=73,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_5616_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        48928,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_5616_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x31b1ce, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7324e32, nonce=72)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000601a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f630644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=72,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_5616_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        56056,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_5616_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x6ee8f2, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6f5170e, nonce=170)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000801a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f630644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000000000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=170,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_5616_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        34000,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_5616_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495616 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x6e5919, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6f5a6e7, nonce=169)
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
        storage={0x0: 0xac1de87792e425a22b81bdf624dc1b24fee26f16e9a879172aebc261cc51a2fe},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000601a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f630644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=169,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_5617_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        49120,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_5617_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x39706e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a72a8f92, nonce=83)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000801a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f630644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=83,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_5617_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        48992,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_5617_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x38b10e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a72b4ef2, nonce=82)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000601a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f630644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=82,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_5617_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        56120,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_5617_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x753a31, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6eec5cf, nonce=180)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000801a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f630644e72e131a029b85045b68181585d2833e84879b9709143e1f593f00000010000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=180,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_5617_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        55992,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_5617_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 21888242871839275222246405745257275088548364400416034343698204186575808495617 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x74aa18, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6ef55e8, nonce=179)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000601a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f630644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=179,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_9935_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        49248,
        50000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_9935_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x4073ae, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7238c52, nonce=93)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000801a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f6ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=93,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_9935_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        49120,
        50000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_9935_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x3fb3ce, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7244c32, nonce=92)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000601a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f6ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=92,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_9935_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        56248,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_9935_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x7b8f30, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6e870d0, nonce=190)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000801a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f6ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=190,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_9935_28000_96Filler.json"],
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
def test_ecmul_7827_6598_9935_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 115792089237316195423570985008687907853269984665640564039457584007913129639935 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x7afe97, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a6e90169, nonce=189)
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
        storage={0x0: 0xa34b6e4f9c282ff62c1e6f53fd92ad8efd8346d9866333a95ab4506a8158afc7},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000601a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f6ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=189,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_9_21000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        47264,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_9_21000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x21828e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7427d72, nonce=48)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000801a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f600000000000000000000000000000000000000000000000000000000000000090000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=48,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_9_21000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        47136,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_9_21000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 21000 bytes."""
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
    pre[coinbase] = Account(balance=0x20ca6e, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a7433592, nonce=47)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000601a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000000000000000000000000000000000009"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=47,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_9_28000_128Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        54264,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_9_28000_128(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 128 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x5fae39, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a70451c7, nonce=145)
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
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000801a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f600000000000000000000000000000000000000000000000000000000000000090000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=145,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stZeroKnowledge/ecmul_7827-6598_9_28000_96Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        33656,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecmul_7827_6598_9_28000_96(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the point (11999875504842010600789954262886096740416429265635183817701593963271973497827, 11843594000332171325303933275547366297934113019079887694534126289021216356598) and the factor 9 into the ECMUL precompile, truncating or expanding the input data to 96 bytes. Gives the execution 28000 bytes."""
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
    pre[coinbase] = Account(balance=0x5f2560, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a704daa0, nonce=144)
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
        storage={0x0: 0xc7b29565a7dd9915e6fd86d026aef2fc454506bae7f90e2f2bec5f25f01b2d95},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000601a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000000000000000000000000000000000009"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=144,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
