"""
Ported from:
tests/static/state_tests/stTransactionTest/Opcodes_TransactionInitFiller.json

contract code:
    push2 0xffff
    pop
    push1 0x04
    push1 0x00
    return

callee_1 code:
    push1 0x01
    push1 0x00
    sstore
    stop
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
    ["tests/static/state_tests/stTransactionTest/Opcodes_TransactionInitFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0060016000f3",
        "60ff60ff60ff9150505060006000f3",
        "60ff60ff60ff60ff925050505060006000f3",
        "60ff60ff60ff60ff60ff93505050505060006000f3",
        "60ff60ff60ff60ff60ff60ff9450505050505060006000f3",
        "60ff60ff60ff60ff60ff60ff60ff955050505050505060006000f3",
        "60ff60ff60ff60ff60ff60ff60ff60ff96505050505050505060006000f3",
        "600060ff60ff60ff60ff60ff60ff60ff60ff9750505050505050505060006000f3",
        "600060ff60ff60ff60ff60ff60ff60ff60ff60ff985050505050505050505060006000f3",
        "600060ff60ff60ff60ff60ff60ff60ff60ff60ff60ff99505050505050505050505060006000f3",
        "600060ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff9a50505050505050505050505060006000f3",
        "600160010a5060006000f3",
        "600060ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff9b5050505050505050505050505060006000f3",
        "600060ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff9c505050505050505050505050505060006000f3",
        "600060ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff9d50505050505050505050505050505060006000f3",
        "600060ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff9e5050505050505050505050505050505060006000f3",
        "600060ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff9f505050505050505050505050505050505060006000f3",
        "60006000a060006000f3",
        "60ff60006000a160006000f3",
        "60ff60ff60006000a260006000f3",
        "60ff60ff60ff60006000a360006000f3",
        "60ff60ff60ff60ff60006000a460006000f3",
        "600160010b5060006000f3",
        "6000600060fff05060006000f3",
        "60006000600060006017730f572e5295c57f15886f9b263e2f6d2d6c7b5ec66064f15060006000f3",
        "60006000600060006000730f572e5295c57f15886f9b263e2f6d2d6c7b5ec66064f25060006000f3",
        "60006000f3",
        "6000600060006000730f572e5295c57f15886f9b263e2f6d2d6c7b5ec6620186a0f45060006000f3",
        "6000600060006000730f572e5295c57f15886f9b263e2f6d2d6c7b5ec6612710fa5060006000f3",
        "60006000fd60006000f3",
        "32ff",
        "60016001105060006000f3",
        "60016001115060006000f3",
        "60016001125060006000f3",
        "60016001135060006000f3",
        "60016001145060006000f3",
        "6000155060006000f3",
        "60006000165060006000f3",
        "60006000175060006000f3",
        "60016001015060006000f3",
        "60006000185060006000f3",
        "6000195060006000f3",
        "67805020100804020160001a5060006000f3",
        "600060002060006000f3",
        "305060006000f3",
        "6000315060006000f3",
        "325060006000f3",
        "335060006000f3",
        "345060006000f3",
        "6000355060006000f3",
        "60016001025060006000f3",
        "365060006000f3",
        "6000600060003760006000f3",
        "385060006000f3",
        "38600060013960015160005560006000f3",
        "3a5060006000f3",
        "60003b5060006000f3",
        "6014600060007310000000000000000000000000000000000000103c60006000f3",
        "3d5060006000f3",
        "6000600060003e60006000f3",
        "60005060005060006000f3",
        "60016001035060006000f3",
        "6000515060006000f3",
        "600060005260006000f3",
        "60ff60005360006000f3",
        "6000545060006000f3",
        "600160015560006000f3",
        "600456005b60006000f3",
        "6001600657005b60006000f3",
        "585060006000f3",
        "595060006000f3",
        "5a5060006000f3",
        "60016001045060006000f3",
        "5b60006000f3",
        "60ff5060006000f3",
        "61ffff5060006000f3",
        "62ffffff5060006000f3",
        "63ffffffff5060006000f3",
        "64ffffffffff5060006000f3",
        "65ffffffffffff5060006000f3",
        "66ffffffffffffff5060006000f3",
        "67ffffffffffffffff5060006000f3",
        "68ffffffffffffffffff5060006000f3",
        "60016001055060006000f3",
        "69ffffffffffffffffffff5060006000f3",
        "6affffffffffffffffffffff5060006000f3",
        "6bffffffffffffffffffffffff5060006000f3",
        "6cffffffffffffffffffffffffff5060006000f3",
        "6dffffffffffffffffffffffffffff5060006000f3",
        "6effffffffffffffffffffffffffffff5060006000f3",
        "6fffffffffffffffffffffffffffffffff5060006000f3",
        "70ffffffffffffffffffffffffffffffffff5060006000f3",
        "71ffffffffffffffffffffffffffffffffffff5060006000f3",
        "72ffffffffffffffffffffffffffffffffffffff5060006000f3",
        "60016001065060006000f3",
        "73ffffffffffffffffffffffffffffffffffffffff5060006000f3",
        "74ffffffffffffffffffffffffffffffffffffffffff5060006000f3",
        "75ffffffffffffffffffffffffffffffffffffffffffff5060006000f3",
        "76ffffffffffffffffffffffffffffffffffffffffffffff5060006000f3",
        "77ffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3",
        "78ffffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3",
        "79ffffffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3",
        "7affffffffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3",
        "7bffffffffffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3",
        "7cffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3",
        "60016001075060006000f3",
        "7dffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3",
        "7effffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3",
        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3",
        "60ff80505060006000f3",
        "60ff60ff8150505060006000f3",
        "60ff60ff60ff825050505060006000f3",
        "60ff60ff60ff60ff83505050505060006000f3",
        "60ff60ff60ff60ff60ff8450505050505060006000f3",
        "60ff60ff60ff60ff60ff60ff855050505050505060006000f3",
        "60ff60ff60ff60ff60ff60ff60ff86505050505050505060006000f3",
        "600160016001085060006000f3",
        "60ff60ff60ff60ff60ff60ff60ff60ff8750505050505050505060006000f3",
        "60ff60ff60ff60ff60ff60ff60ff60ff60ff885050505050505050505060006000f3",
        "60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff89505050505050505050505060006000f3",
        "60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff8a50505050505050505050505060006000f3",
        "60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff8b5050505050505050505050505060006000f3",
        "60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff8c505050505050505050505050505060006000f3",
        "60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff8d50505050505050505050505050505060006000f3",
        "60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff8e5050505050505050505050505050505060006000f3",
        "60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff8f505050505050505050505050505050505060006000f3",
        "60ff60ff90505060006000f3",
        "600160016001095060006000f3",
        "ef",
        "60008080808073b94f5374fce5edbc8e2a8697c15331677e6ebf0b61c350f100",
        "60008080808073b94f5374fce5edbc8e2a8697c15331677e6ebf0b61c350f150fe",
        "60008080808073b94f5374fce5edbc8e2a8697c15331677e6ebf0b61c350f15060ef60005360016000f3",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10', 'case11', 'case12', 'case13', 'case14', 'case15', 'case16', 'case17', 'case18', 'case19', 'case20', 'case21', 'case22', 'case23', 'case24', 'case25', 'case26', 'case27', 'case28', 'case29', 'case30', 'case31', 'case32', 'case33', 'case34', 'case35', 'case36', 'case37', 'case38', 'case39', 'case40', 'case41', 'case42', 'case43', 'case44', 'case45', 'case46', 'case47', 'case48', 'case49', 'case50', 'case51', 'case52', 'case53', 'case54', 'case55', 'case56', 'case57', 'case58', 'case59', 'case60', 'case61', 'case62', 'case63', 'case64', 'case65', 'case66', 'case67', 'case68', 'case69', 'case70', 'case71', 'case72', 'case73', 'case74', 'case75', 'case76', 'case77', 'case78', 'case79', 'case80', 'case81', 'case82', 'case83', 'case84', 'case85', 'case86', 'case87', 'case88', 'case89', 'case90', 'case91', 'case92', 'case93', 'case94', 'case95', 'case96', 'case97', 'case98', 'case99', 'case100', 'case101', 'case102', 'case103', 'case104', 'case105', 'case106', 'case107', 'case108', 'case109', 'case110', 'case111', 'case112', 'case113', 'case114', 'case115', 'case116', 'case117', 'case118', 'case119', 'case120', 'case121', 'case122', 'case123', 'case124', 'case125', 'case126', 'case127', 'case128', 'case129', 'case130', 'case131'],
)
@pytest.mark.pre_alloc_mutable
def test_opcodes_transaction_init(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6")
    callee_1 = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=Op.PUSH2[0xffff] + Op.POP + Op.PUSH1[0x4] + Op.PUSH1[0x0] + Op.RETURN,
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0, storage={0x0: 0x0})
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=None,
        data=tx_data,
        gas_limit=400000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
