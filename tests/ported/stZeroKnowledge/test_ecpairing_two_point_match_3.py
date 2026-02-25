"""
Puts the given data into the ECPAIRING precompile

Ported from:
tests/static/state_tests/stZeroKnowledge/ecpairing_two_point_match_3Filler.json

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
    ["tests/static/state_tests/stZeroKnowledge/ecpairing_two_point_match_3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        333736,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_ecpairing_two_point_match_3(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the given data into the ECPAIRING precompile."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = Address("0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1")
    contract = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    callee = Address("0x0000000000000000000000000000000000000001")
    callee_1 = Address("0x0000000000000000000000000000000000000002")
    callee_2 = Address("0x0000000000000000000000000000000000000003")
    callee_3 = Address("0x0000000000000000000000000000000000000004")
    callee_4 = Address("0x0000000000000000000000000000000000000005")
    callee_5 = Address("0x0000000000000000000000000000000000000006")
    callee_6 = Address("0x0000000000000000000000000000000000000007")
    callee_7 = Address("0x0000000000000000000000000000000000000008")
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
    pre[coinbase] = Account(balance=0x302897, nonce=0)
    pre[callee_11] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_12] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_13] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a733d769, nonce=14)
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
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12c] + Op.JUMPI + Op.PUSH2[0x780]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x20] + Op.PUSH2[0x920]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x8]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI
        + Op.PUSH1[0x20] + Op.PUSH2[0x900] + Op.MSTORE + Op.PUSH2[0x900]
        + Op.PUSH1[0x40] + Op.DUP1 + Op.PUSH2[0x960] + Op.DUP3 + Op.DUP5
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH1[0x18] + Op.CALL + Op.POP + Op.POP
        + Op.POP + Op.PUSH2[0x960] + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH2[0x960] + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.MLOAD + Op.ADD + Op.PUSH1[0x20]
        + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3
        + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.RETURN + Op.POP + Op.STOP + Op.JUMPDEST
    ),
        storage={0x0: 0xb10e2d527612073b26eecdfd717e6a320cf44b4afac2b0732d9fcbe2b7fa0cf6},
    )
    pre[callee_15] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_16] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d"
        ),
        to=contract,
        data=bytes.fromhex("30c8d1da0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000018000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002203e205db4f19b37b60121b83a7333706db86431c6d835849957ed8c3928ad7927dc7234fd11d3e8c36c59277c3e6f149d5cd3cfa9a62aee49f8130962b4b3b9195e8aa5b7827463722b8c153931579d3505566b4edf48d498e185f0509de15204bb53b8977e5f92a0bc372742c4830944a59b4fe6b1c0466e2a6dad122b5d2e030644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd31a76dae6d3272396d0cbe61fced2bc532edac647851e3ac53ce1cc9c7e645a83198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=14,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
