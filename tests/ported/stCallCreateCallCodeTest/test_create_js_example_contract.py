"""
Deploy legacy contract normally

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest/createJS_ExampleContractFiller.json

contract code:
    push1 0x00
    calldataload
    push1 0xe0
    push1 0x02
    exp
    swap1
    div
    dup1
    push4 0x43d726d6
    eq
    push2 0x42
    jumpi
    dup1
    push4 0x91b7f5ed
    eq
    push2 0x50
    jumpi
    dup1
    push4 0xd686f9ee
    eq
    ... (541 more instructions)
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
    ["tests/static/state_tests/stCallCreateCallCodeTest/createJS_ExampleContractFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_js_example_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Deploy legacy contract normally."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xbcc416d85e26124ea4ec199a92cf495584a99831")
    contract = Address("0x1119d4ccf86b65812d85f2ff3e9b2d851e40ba5a")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[contract] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0xe0] + Op.PUSH1[0x2] + Op.EXP
        + Op.SWAP1 + Op.DIV + Op.DUP1 + Op.PUSH4[0x43d726d6] + Op.EQ + Op.PUSH2[0x42]
        + Op.JUMPI + Op.DUP1 + Op.PUSH4[0x91b7f5ed] + Op.EQ + Op.PUSH2[0x50]
        + Op.JUMPI + Op.DUP1 + Op.PUSH4[0xd686f9ee] + Op.EQ + Op.PUSH2[0x61]
        + Op.JUMPI + Op.DUP1 + Op.PUSH4[0xf5bade66] + Op.EQ + Op.PUSH2[0x6f]
        + Op.JUMPI + Op.DUP1 + Op.PUSH4[0xfcfff16f] + Op.EQ + Op.PUSH2[0x80]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH2[0x4a] + Op.PUSH2[0x1de]
        + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.RETURN
        + Op.JUMPDEST + Op.PUSH2[0x5b] + Op.PUSH1[0x4] + Op.CALLDATALOAD
        + Op.PUSH2[0xbf] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.RETURN + Op.JUMPDEST + Op.PUSH2[0x69] + Op.PUSH2[0x304] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH2[0x7a] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH2[0x8e] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH2[0x88] + Op.PUSH2[0xf0] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SLOAD
        + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.AND
        + Op.CALLER + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB
        + Op.AND + Op.EQ + Op.ISZERO + Op.PUSH2[0xaf] + Op.JUMPI + Op.PUSH2[0xb4]
        + Op.JUMP + Op.JUMPDEST + Op.PUSH2[0xbc] + Op.JUMP + Op.JUMPDEST + Op.DUP1
        + Op.PUSH1[0x1] + Op.DUP2 + Op.SWAP1 + Op.SSTORE + Op.POP + Op.JUMPDEST
        + Op.POP + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x1]
        + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.AND + Op.CALLER
        + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.AND
        + Op.EQ + Op.ISZERO + Op.PUSH2[0xe0] + Op.JUMPI + Op.PUSH2[0xe5] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH2[0xed] + Op.JUMP + Op.JUMPDEST + Op.DUP1
        + Op.PUSH1[0x2] + Op.DUP2 + Op.SWAP1 + Op.SSTORE + Op.POP + Op.JUMPDEST
        + Op.POP + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x1]
        + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.AND + Op.CALLER
        + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.AND
        + Op.EQ + Op.DUP1 + Op.PUSH2[0x125] + Op.JUMPI + Op.POP + Op.PUSH1[0x3]
        + Op.SLOAD + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB
        + Op.AND + Op.CALLER + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP
        + Op.SUB + Op.AND + Op.EQ + Op.JUMPDEST + Op.PUSH2[0x12e] + Op.JUMPI
        + Op.PUSH2[0x161] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x4]
        + Op.DUP2 + Op.SWAP1 + Op.SSTORE + Op.POP
        + Op.PUSH32[0x59ebeb90bc63057b6515673c3ecf9438e5058bca0f92585014eced636878c9a5]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.LOG1 + Op.PUSH2[0x1dc] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x4] + Op.SLOAD + Op.PUSH1[0x1] + Op.EQ + Op.DUP1
        + Op.PUSH2[0x173] + Op.JUMPI + Op.POP + Op.PUSH1[0x1] + Op.SLOAD
        + Op.CALLVALUE + Op.LT + Op.JUMPDEST + Op.PUSH2[0x1b8] + Op.JUMPI
        + Op.PUSH1[0x1] + Op.PUSH1[0x4] + Op.DUP2 + Op.SWAP1 + Op.SSTORE + Op.POP
        + Op.PUSH32[0x59ebeb90bc63057b6515673c3ecf9438e5058bca0f92585014eced636878c9a5]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.LOG1 + Op.TIMESTAMP + Op.PUSH1[0x5]
        + Op.DUP2 + Op.SWAP1 + Op.SSTORE + Op.POP + Op.CALLER + Op.PUSH1[0x3]
        + Op.DUP2 + Op.SWAP1 + Op.SSTORE + Op.POP + Op.PUSH2[0x1db] + Op.JUMP
        + Op.JUMPDEST + Op.CALLER + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2]
        + Op.EXP + Op.SUB + Op.AND + Op.PUSH1[0x0] + Op.CALLVALUE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.DUP5 + Op.DUP8 + Op.DUP8
        + Op.CALL + Op.PUSH2[0x1d7] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.POP
        + Op.POP + Op.POP + Op.JUMPDEST + Op.JUMPDEST + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.SLOAD + Op.PUSH1[0x0] + Op.EQ
        + Op.PUSH2[0x1ef] + Op.JUMPI + Op.PUSH2[0x1f4] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH2[0x301] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SLOAD
        + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.AND
        + Op.CALLER + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB
        + Op.AND + Op.EQ + Op.DUP1 + Op.ISZERO + Op.PUSH2[0x22c] + Op.JUMPI + Op.POP
        + Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2]
        + Op.EXP + Op.SUB + Op.AND + Op.PUSH1[0x3] + Op.SLOAD + Op.PUSH1[0x1]
        + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.AND + Op.EQ
        + Op.JUMPDEST + Op.PUSH2[0x235] + Op.JUMPI + Op.PUSH2[0x242] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.DUP2 + Op.SWAP1 + Op.SSTORE
        + Op.POP + Op.PUSH2[0x301] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x3] + Op.SLOAD
        + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.AND
        + Op.CALLER + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB
        + Op.AND + Op.EQ + Op.PUSH2[0x262] + Op.JUMPI + Op.PUSH2[0x300] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x5] + Op.SLOAD + Op.TIMESTAMP + Op.SUB
        + Op.PUSH1[0x2] + Op.SLOAD + Op.MUL + Op.SWAP1 + Op.POP + Op.PUSH1[0x1]
        + Op.SLOAD + Op.DUP2 + Op.GT + Op.PUSH2[0x2c7] + Op.JUMPI + Op.PUSH1[0x3]
        + Op.SLOAD + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB
        + Op.AND + Op.PUSH1[0x0] + Op.DUP3 + Op.PUSH1[0x1] + Op.SLOAD + Op.SUB
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.DUP5
        + Op.DUP8 + Op.DUP8 + Op.CALL + Op.PUSH2[0x29b] + Op.JUMPI + Op.STOP
        + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x0] + Op.SLOAD
        + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.AND
        + Op.PUSH1[0x0] + Op.DUP3 + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.DUP5 + Op.DUP8 + Op.DUP8 + Op.CALL + Op.PUSH2[0x2bf]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.POP + Op.POP + Op.POP
        + Op.PUSH2[0x2ee] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SLOAD
        + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.AND
        + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.SLOAD + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.DUP5 + Op.DUP8 + Op.DUP8 + Op.CALL
        + Op.PUSH2[0x2ea] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.POP + Op.POP
        + Op.POP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.DUP2 + Op.SWAP1
        + Op.SSTORE + Op.POP + Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x3] + Op.DUP2
        + Op.SWAP1 + Op.SSTORE + Op.POP + Op.JUMPDEST + Op.JUMPDEST + Op.POP + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x1]
        + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.AND + Op.CALLER
        + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.AND
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x327] + Op.JUMPI + Op.PUSH2[0x32c] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH2[0x37e] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x5]
        + Op.SLOAD + Op.TIMESTAMP + Op.SUB + Op.PUSH1[0x2] + Op.SLOAD + Op.MUL
        + Op.SWAP1 + Op.POP + Op.PUSH1[0x1] + Op.SLOAD + Op.DUP2 + Op.GT
        + Op.PUSH2[0x345] + Op.JUMPI + Op.PUSH2[0x37d] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2]
        + Op.EXP + Op.SUB + Op.AND + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.SLOAD
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.DUP5
        + Op.DUP8 + Op.DUP8 + Op.CALL + Op.PUSH2[0x368] + Op.JUMPI + Op.STOP
        + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x4]
        + Op.DUP2 + Op.SWAP1 + Op.SSTORE + Op.POP + Op.PUSH1[0x0] + Op.SLOAD
        + Op.PUSH1[0x3] + Op.DUP2 + Op.SWAP1 + Op.SSTORE + Op.POP + Op.JUMPDEST
        + Op.JUMPDEST + Op.POP + Op.JUMP
    ),
        storage={0x0: 0xbcc416d85e26124ea4ec199a92cf495584a99831, 0x1: 0x42, 0x2: 0x23, 0x3: 0xbcc416d85e26124ea4ec199a92cf495584a99831, 0x5: 0x54c98c81},
    )
    pre[sender] = Account(balance=0x9184e72a000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x6600370d1f9991e2d92ffe661c84e7c8c6ecafc094774f0f3db0f8dd663590e9"
        ),
        to=None,
        data=bytes.fromhex(
            "60406103ca60043960045160245133600081905550600060048190555081600181905550"
            "8060028190555042600581905550336003819055505050610381806100496000396000f3"
            "0060003560e060020a9004806343d726d61461004257806391b7f5ed14610050578063d6"
            "86f9ee14610061578063f5bade661461006f578063fcfff16f1461008057005b61004a61"
            "01de565b60006000f35b61005b6004356100bf565b60006000f35b610069610304565b60"
            "006000f35b61007a60043561008e565b60006000f35b6100886100f0565b60006000f35b"
            "600054600160a060020a031633600160a060020a031614156100af576100b4565b6100bc"
            "565b806001819055505b50565b600054600160a060020a031633600160a060020a031614"
            "156100e0576100e5565b6100ed565b806002819055505b50565b600054600160a060020a"
            "031633600160a060020a031614806101255750600354600160a060020a031633600160a0"
            "60020a0316145b61012e57610161565b60016004819055507f59ebeb90bc63057b651567"
            "3c3ecf9438e5058bca0f92585014eced636878c9a560006000a16101dc565b6004546001"
            "1480610173575060015434105b6101b85760016004819055507f59ebeb90bc63057b6515"
            "673c3ecf9438e5058bca0f92585014eced636878c9a560006000a1426005819055503360"
            "03819055506101db565b33600160a060020a03166000346000600060006000848787f161"
            "01d757005b5050505b5b565b60006004546000146101ef576101f4565b610301565b6000"
            "54600160a060020a031633600160a060020a031614801561022c5750600054600160a060"
            "020a0316600354600160a060020a0316145b61023557610242565b600060048190555061"
            "0301565b600354600160a060020a031633600160a060020a03161461026257610300565b"
            "600554420360025402905060015481116102c757600354600160a060020a031660008260"
            "0154036000600060006000848787f161029b57005b505050600054600160a060020a0316"
            "6000826000600060006000848787f16102bf57005b5050506102ee565b600054600160a0"
            "60020a031660006001546000600060006000848787f16102ea57005b5050505b60006004"
            "819055506000546003819055505b5b50565b6000600054600160a060020a031633600160"
            "a060020a031614156103275761032c565b61037e565b6005544203600254029050600154"
            "81116103455761037d565b600054600160a060020a031660006001546000600060006000"
            "848787f161036857005b50505060006004819055506000546003819055505b5b50560000"
            "000000000000000000000000000000000000000000000000000000000042000000000000"
            "0000000000000000000000000000000000000000000000000023"
        ),
        gas_limit=600000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
