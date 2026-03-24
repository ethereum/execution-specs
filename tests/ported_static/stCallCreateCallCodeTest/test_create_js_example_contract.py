"""
Deploy legacy contract normally.

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest
createJS_ExampleContractFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCallCreateCallCodeTest/createJS_ExampleContractFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_js_example_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Deploy legacy contract normally."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x6600370D1F9991E2D92FFE661C84E7C8C6ECAFC094774F0F3DB0F8DD663590E9
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x0)
            + Op.EXP(0x2, 0xE0)
            + Op.SWAP1
            + Op.DIV
            + Op.JUMPI(pc=Op.PUSH2[0x42], condition=Op.EQ(0x43D726D6, Op.DUP1))
            + Op.JUMPI(pc=Op.PUSH2[0x50], condition=Op.EQ(0x91B7F5ED, Op.DUP1))
            + Op.JUMPI(pc=Op.PUSH2[0x61], condition=Op.EQ(0xD686F9EE, Op.DUP1))
            + Op.JUMPI(pc=Op.PUSH2[0x6F], condition=Op.EQ(0xF5BADE66, Op.DUP1))
            + Op.JUMPI(pc=Op.PUSH2[0x80], condition=Op.EQ(0xFCFFF16F, Op.DUP1))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH2[0x4A]
            + Op.JUMP(pc=0x1DE)
            + Op.JUMPDEST
            + Op.RETURN(offset=0x0, size=0x0)
            + Op.JUMPDEST
            + Op.PUSH2[0x5B]
            + Op.CALLDATALOAD(offset=0x4)
            + Op.JUMP(pc=Op.PUSH2[0xBF])
            + Op.JUMPDEST
            + Op.RETURN(offset=0x0, size=0x0)
            + Op.JUMPDEST
            + Op.PUSH2[0x69]
            + Op.JUMP(pc=0x304)
            + Op.JUMPDEST
            + Op.RETURN(offset=0x0, size=0x0)
            + Op.JUMPDEST
            + Op.PUSH2[0x7A]
            + Op.CALLDATALOAD(offset=0x4)
            + Op.JUMP(pc=Op.PUSH2[0x8E])
            + Op.JUMPDEST
            + Op.RETURN(offset=0x0, size=0x0)
            + Op.JUMPDEST
            + Op.PUSH2[0x88]
            + Op.JUMP(pc=Op.PUSH2[0xF0])
            + Op.JUMPDEST
            + Op.RETURN(offset=0x0, size=0x0)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0xAF],
                condition=Op.ISZERO(
                    Op.EQ(
                        Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.CALLER),
                        Op.AND(
                            Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x0)
                        ),
                    ),
                ),
            )
            + Op.JUMP(pc=Op.PUSH2[0xB4])
            + Op.JUMPDEST
            + Op.JUMP(pc=Op.PUSH2[0xBC])
            + Op.JUMPDEST
            + Op.DUP1
            + Op.PUSH1[0x1]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0xE0],
                condition=Op.ISZERO(
                    Op.EQ(
                        Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.CALLER),
                        Op.AND(
                            Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x0)
                        ),
                    ),
                ),
            )
            + Op.JUMP(pc=Op.PUSH2[0xE5])
            + Op.JUMPDEST
            + Op.JUMP(pc=Op.PUSH2[0xED])
            + Op.JUMPDEST
            + Op.DUP1
            + Op.PUSH1[0x2]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMP
            + Op.JUMPDEST
            + Op.EQ(
                Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.CALLER),
                Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x0)),
            )
            + Op.JUMPI(pc=0x125, condition=Op.DUP1)
            + Op.POP
            + Op.EQ(
                Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.CALLER),
                Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x3)),
            )
            + Op.JUMPDEST
            + Op.PUSH2[0x12E]
            + Op.JUMPI
            + Op.JUMP(pc=0x161)
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x4]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.LOG1(
                offset=0x0,
                size=0x0,
                topic_1=0x59EBEB90BC63057B6515673C3ECF9438E5058BCA0F92585014ECED636878C9A5,  # noqa: E501
            )
            + Op.JUMP(pc=0x1DC)
            + Op.JUMPDEST
            + Op.EQ(0x1, Op.SLOAD(key=0x4))
            + Op.JUMPI(pc=0x173, condition=Op.DUP1)
            + Op.POP
            + Op.LT(Op.CALLVALUE, Op.SLOAD(key=0x1))
            + Op.JUMPDEST
            + Op.PUSH2[0x1B8]
            + Op.JUMPI
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x4]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.LOG1(
                offset=0x0,
                size=0x0,
                topic_1=0x59EBEB90BC63057B6515673C3ECF9438E5058BCA0F92585014ECED636878C9A5,  # noqa: E501
            )
            + Op.TIMESTAMP
            + Op.PUSH1[0x5]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.CALLER
            + Op.PUSH1[0x3]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.JUMP(pc=0x1DB)
            + Op.JUMPDEST
            + Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.CALLER)
            + Op.PUSH1[0x0]
            + Op.CALLVALUE
            + Op.JUMPI(
                pc=0x1D7,
                condition=Op.CALL(
                    gas=Op.DUP8,
                    address=Op.DUP8,
                    value=Op.DUP5,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMP
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.JUMPI(pc=0x1EF, condition=Op.EQ(0x0, Op.SLOAD(key=0x4)))
            + Op.JUMP(pc=0x1F4)
            + Op.JUMPDEST
            + Op.JUMP(pc=0x301)
            + Op.JUMPDEST
            + Op.EQ(
                Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.CALLER),
                Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x0)),
            )
            + Op.JUMPI(pc=0x22C, condition=Op.ISZERO(Op.DUP1))
            + Op.POP
            + Op.EQ(
                Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x3)),
                Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x0)),
            )
            + Op.JUMPDEST
            + Op.PUSH2[0x235]
            + Op.JUMPI
            + Op.JUMP(pc=0x242)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x4]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.JUMP(pc=0x301)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x262,
                condition=Op.EQ(
                    Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.CALLER),
                    Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x3)),
                ),
            )
            + Op.JUMP(pc=0x300)
            + Op.JUMPDEST
            + Op.MUL(
                Op.SLOAD(key=0x2), Op.SUB(Op.TIMESTAMP, Op.SLOAD(key=0x5))
            )
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(pc=0x2C7, condition=Op.GT(Op.DUP2, Op.SLOAD(key=0x1)))
            + Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x3))
            + Op.PUSH1[0x0]
            + Op.SUB(Op.SLOAD(key=0x1), Op.DUP3)
            + Op.JUMPI(
                pc=0x29B,
                condition=Op.CALL(
                    gas=Op.DUP8,
                    address=Op.DUP8,
                    value=Op.DUP5,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x0))
            + Op.PUSH1[0x0]
            + Op.DUP3
            + Op.JUMPI(
                pc=0x2BF,
                condition=Op.CALL(
                    gas=Op.DUP8,
                    address=Op.DUP8,
                    value=Op.DUP5,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.JUMP(pc=0x2EE)
            + Op.JUMPDEST
            + Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x0))
            + Op.PUSH1[0x0]
            + Op.SLOAD(key=0x1)
            + Op.JUMPI(
                pc=0x2EA,
                condition=Op.CALL(
                    gas=Op.DUP8,
                    address=Op.DUP8,
                    value=Op.DUP5,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x4]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.SLOAD(key=0x0)
            + Op.PUSH1[0x3]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMP
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.JUMPI(
                pc=0x327,
                condition=Op.ISZERO(
                    Op.EQ(
                        Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.CALLER),
                        Op.AND(
                            Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x0)
                        ),
                    ),
                ),
            )
            + Op.JUMP(pc=0x32C)
            + Op.JUMPDEST
            + Op.JUMP(pc=0x37E)
            + Op.JUMPDEST
            + Op.MUL(
                Op.SLOAD(key=0x2), Op.SUB(Op.TIMESTAMP, Op.SLOAD(key=0x5))
            )
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(pc=0x345, condition=Op.GT(Op.DUP2, Op.SLOAD(key=0x1)))
            + Op.JUMP(pc=0x37D)
            + Op.JUMPDEST
            + Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x0))
            + Op.PUSH1[0x0]
            + Op.SLOAD(key=0x1)
            + Op.JUMPI(
                pc=0x368,
                condition=Op.CALL(
                    gas=Op.DUP8,
                    address=Op.DUP8,
                    value=Op.DUP5,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x4]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.SLOAD(key=0x0)
            + Op.PUSH1[0x3]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.POP
            + Op.JUMP
        ),
        storage={
            0x0: 0xBCC416D85E26124EA4EC199A92CF495584A99831,
            0x1: 0x42,
            0x2: 0x23,
            0x3: 0xBCC416D85E26124EA4EC199A92CF495584A99831,
            0x5: 0x54C98C81,
        },
        balance=0x186A0,
        nonce=0,
        address=Address("0x1119d4ccf86b65812d85f2ff3e9b2d851e40ba5a"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x9184E72A000)

    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex(
            "60406103ca60043960045160245133600081905550600060048190555081600181905550"  # noqa: E501
            "8060028190555042600581905550336003819055505050610381806100496000396000f3"  # noqa: E501
            "0060003560e060020a9004806343d726d61461004257806391b7f5ed14610050578063d6"  # noqa: E501
            "86f9ee14610061578063f5bade661461006f578063fcfff16f1461008057005b61004a61"  # noqa: E501
            "01de565b60006000f35b61005b6004356100bf565b60006000f35b610069610304565b60"  # noqa: E501
            "006000f35b61007a60043561008e565b60006000f35b6100886100f0565b60006000f35b"  # noqa: E501
            "600054600160a060020a031633600160a060020a031614156100af576100b4565b6100bc"  # noqa: E501
            "565b806001819055505b50565b600054600160a060020a031633600160a060020a031614"  # noqa: E501
            "156100e0576100e5565b6100ed565b806002819055505b50565b600054600160a060020a"  # noqa: E501
            "031633600160a060020a031614806101255750600354600160a060020a031633600160a0"  # noqa: E501
            "60020a0316145b61012e57610161565b60016004819055507f59ebeb90bc63057b651567"  # noqa: E501
            "3c3ecf9438e5058bca0f92585014eced636878c9a560006000a16101dc565b6004546001"  # noqa: E501
            "1480610173575060015434105b6101b85760016004819055507f59ebeb90bc63057b6515"  # noqa: E501
            "673c3ecf9438e5058bca0f92585014eced636878c9a560006000a1426005819055503360"  # noqa: E501
            "03819055506101db565b33600160a060020a03166000346000600060006000848787f161"  # noqa: E501
            "01d757005b5050505b5b565b60006004546000146101ef576101f4565b610301565b6000"  # noqa: E501
            "54600160a060020a031633600160a060020a031614801561022c5750600054600160a060"  # noqa: E501
            "020a0316600354600160a060020a0316145b61023557610242565b600060048190555061"  # noqa: E501
            "0301565b600354600160a060020a031633600160a060020a03161461026257610300565b"  # noqa: E501
            "600554420360025402905060015481116102c757600354600160a060020a031660008260"  # noqa: E501
            "0154036000600060006000848787f161029b57005b505050600054600160a060020a0316"  # noqa: E501
            "6000826000600060006000848787f16102bf57005b5050506102ee565b600054600160a0"  # noqa: E501
            "60020a031660006001546000600060006000848787f16102ea57005b5050505b60006004"  # noqa: E501
            "819055506000546003819055505b5b50565b6000600054600160a060020a031633600160"  # noqa: E501
            "a060020a031614156103275761032c565b61037e565b6005544203600254029050600154"  # noqa: E501
            "81116103455761037d565b600054600160a060020a031660006001546000600060006000"  # noqa: E501
            "848787f161036857005b50505060006004819055506000546003819055505b5b50560000"  # noqa: E501
            "000000000000000000000000000000000000000000000000000000000042000000000000"  # noqa: E501
            "0000000000000000000000000000000000000000000000000023"
        ),
        gas_limit=600000,
        value=100000,
    )

    post = {
        contract: Account(
            storage={
                0: 0xBCC416D85E26124EA4EC199A92CF495584A99831,
                1: 66,
                2: 35,
                3: 0xBCC416D85E26124EA4EC199A92CF495584A99831,
                5: 0x54C98C81,
            },
        ),
        Address("0x1ce6265a59bf9efb80a801e28d956a6974834375"): Account(
            storage={
                0: 0xBCC416D85E26124EA4EC199A92CF495584A99831,
                1: 66,
                2: 35,
                3: 0xBCC416D85E26124EA4EC199A92CF495584A99831,
                5: 1000,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
