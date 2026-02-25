"""
Puts the base 0, exponent 0 and modulus 0 into the MODEXP precompile, saves the hash of the result. Gives the execution 25000 gas

Ported from:
tests/static/state_tests/stPreCompiledContracts2/modexp_0_0_0_25000Filler.json

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
    ["tests/static/state_tests/stPreCompiledContracts2/modexp_0_0_0_25000Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        47040,
        90000,
        110000,
        200000,
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_modexp_0_0_0_25000(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the base 0, exponent 0 and modulus 0 into the MODEXP precompile, saves the hash of the result. Gives the execution 25000 gas."""
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
    pre[coinbase] = Account(balance=0x201ee, nonce=0)
    pre[sender] = Account(balance=0xde0b6b3a761fe12, nonce=1)
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
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x12b] + Op.JUMPI + Op.PUSH1[0x84]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.ADD + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH2[0x140] + Op.CALLDATACOPY + Op.PUSH1[0x1] + Op.PUSH2[0x240]
        + Op.PUSH2[0x140] + Op.MLOAD + Op.PUSH2[0x160] + Op.PUSH1[0x0] + Op.PUSH1[0x5]
        + Op.PUSH4[0x5f5e0ff] + Op.CALL + Op.ISZERO + Op.PC + Op.JUMPI + Op.PUSH1[0x1]
        + Op.PUSH2[0x220] + Op.MSTORE + Op.PUSH2[0x220] + Op.PUSH1[0x21] + Op.DUP1
        + Op.PUSH2[0x280] + Op.DUP3 + Op.DUP5 + Op.PUSH1[0x0] + Op.PUSH1[0x4]
        + Op.PUSH1[0x15] + Op.CALL + Op.POP + Op.POP + Op.POP + Op.PUSH2[0x280]
        + Op.DUP1 + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3 + Op.ADD + Op.SHA3 + Op.SWAP1
        + Op.POP + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH2[0x280] + Op.PUSH1[0x20]
        + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2
        + Op.MLOAD + Op.ADD + Op.PUSH1[0x20] + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB
        + Op.MOD + Op.PUSH1[0x1f] + Op.DUP3 + Op.ADD + Op.SUB + Op.SWAP1 + Op.POP
        + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB + Op.RETURN + Op.POP + Op.STOP
        + Op.JUMPDEST
    ),
    )

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
