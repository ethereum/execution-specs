"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/VMTests/vmTests/randomFiller.yml

callee code:
    blockhash
    blockhash
    gaslimit
    swap2
    number
    blockhash
    coinbase
    prevrandao
    dup1
    swap8
    msize
    dup9
    push14 0x608f

callee_1 code:
    blockhash
    coinbase

callee_2 code:
    blockhash
    gaslimit
    blockhash
    coinbase
    gaslimit
    gaslimit
    prevrandao
    coinbase
    callvalue
    codecopy
    dup8
    selfdestruct
    calldatacopy
    calldataload
    div
    address
    sstore

callee_3 code:
    number
    number
    timestamp
    prevrandao
    timestamp
    prevrandao
    gaslimit
    gaslimit
    swap8

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x04
    calldataload
    push2 0x1000
    add
    gas
    call
    stop

callee_4 code:
    push6 0x424555

callee_5 code:
    push24 0x45414245403745f31387900a8d55
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
    ["tests/static/state_tests/VMTests/vmTests/randomFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "693c61390000000000000000000000000000000000000000000000000000000000000000",
        "693c61390000000000000000000000000000000000000000000000000000000000000001",
        "693c61390000000000000000000000000000000000000000000000000000000000000002",
        "693c61390000000000000000000000000000000000000000000000000000000000000003",
        "693c61390000000000000000000000000000000000000000000000000000000000000004",
        "693c61390000000000000000000000000000000000000000000000000000000000000005",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5'],
)
@pytest.mark.pre_alloc_mutable
def test_random(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x4fc23576bc27a8785d5c7bf6c8cbe6e3615139c2")
    contract = Address("0xa83db56c7ce68c06129b80c7be0d0f5e0869d536")
    callee = Address("0x15adfb805be4f3ee3e5c535abc860890a3a2a6c9")
    callee_1 = Address("0x2e3b99613a2e74ebb0cd62d7b9eb38bad240cec6")
    callee_2 = Address("0x3412d3ebac3fcacfb451708aef7cc8e5bf1e5261")
    callee_3 = Address("0x66b8dba513dc25f967ef7e84306616c0071cccae")
    callee_4 = Address("0xacd000f275b1a28d0c3b7dee7f114c4d28fb1636")
    callee_5 = Address("0xdfe69e96fb3aafde261565670b1fea29869c6950")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=bytes.fromhex("4040459143404144809759886d608f"),
    )
    pre[callee_1] = Account(balance=0xba1a9ce0ba1a9ce, nonce=0, code=Op.BLOCKHASH + Op.COINBASE)
    pre[callee_2] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.BLOCKHASH + Op.GASLIMIT + Op.BLOCKHASH + Op.COINBASE + Op.GASLIMIT
        + Op.GASLIMIT + Op.PREVRANDAO + Op.COINBASE + Op.CALLVALUE + Op.CODECOPY
        + Op.DUP8 + Op.SELFDESTRUCT + Op.CALLDATACOPY + Op.CALLDATALOAD + Op.DIV
        + Op.ADDRESS + Op.SSTORE
    ),
    )
    pre[sender] = Account(balance=0x10000000000000, nonce=0)
    pre[callee_3] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.NUMBER + Op.NUMBER + Op.TIMESTAMP + Op.PREVRANDAO + Op.TIMESTAMP
        + Op.PREVRANDAO + Op.GASLIMIT + Op.GASLIMIT + Op.SWAP8
    ),
    )
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH2[0x1000] + Op.ADD
        + Op.GAS + Op.CALL + Op.STOP
    ),
    )
    pre[callee_4] = Account(balance=0xba1a9ce0ba1a9ce, nonce=0, code=bytes.fromhex("65424555"))
    pre[callee_5] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=bytes.fromhex("7745414245403745f31387900a8d55"),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xf3630c36a29ec9af814ae38e4d48056a3368bb1435c5c2b3289763e4c77a3df0"
        ),
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
