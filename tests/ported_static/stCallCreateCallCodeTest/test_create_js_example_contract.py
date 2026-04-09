"""
Deploy legacy contract normally.

Ported from:
state_tests/stCallCreateCallCodeTest/createJS_ExampleContractFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCallCreateCallCodeTest/createJS_ExampleContractFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_js_example_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Deploy legacy contract normally."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x9184E72A000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: raw
    # 0x60003560e060020a9004806343d726d61461004257806391b7f5ed14610050578063d686f9ee14610061578063f5bade661461006f578063fcfff16f1461008057005b61004a6101de565b60006000f35b61005b6004356100bf565b60006000f35b610069610304565b60006000f35b61007a60043561008e565b60006000f35b6100886100f0565b60006000f35b600054600160a060020a031633600160a060020a031614156100af576100b4565b6100bc565b806001819055505b50565b600054600160a060020a031633600160a060020a031614156100e0576100e5565b6100ed565b806002819055505b50565b600054600160a060020a031633600160a060020a031614806101255750600354600160a060020a031633600160a060020a0316145b61012e57610161565b60016004819055507f59ebeb90bc63057b6515673c3ecf9438e5058bca0f92585014eced636878c9a560006000a16101dc565b60045460011480610173575060015434105b6101b85760016004819055507f59ebeb90bc63057b6515673c3ecf9438e5058bca0f92585014eced636878c9a560006000a142600581905550336003819055506101db565b33600160a060020a03166000346000600060006000848787f16101d757005b5050505b5b565b60006004546000146101ef576101f4565b610301565b600054600160a060020a031633600160a060020a031614801561022c5750600054600160a060020a0316600354600160a060020a0316145b61023557610242565b6000600481905550610301565b600354600160a060020a031633600160a060020a03161461026257610300565b600554420360025402905060015481116102c757600354600160a060020a0316600082600154036000600060006000848787f161029b57005b505050600054600160a060020a03166000826000600060006000848787f16102bf57005b5050506102ee565b600054600160a060020a031660006001546000600060006000848787f16102ea57005b5050505b60006004819055506000546003819055505b5b50565b6000600054600160a060020a031633600160a060020a031614156103275761032c565b61037e565b600554420360025402905060015481116103455761037d565b600054600160a060020a031660006001546000600060006000848787f161036857005b50505060006004819055506000546003819055505b5b5056  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x0)
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
                    Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x0)),
                )
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
                    Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x0)),
                )
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
        + Op.POP * 3
        + Op.JUMPDEST * 2
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
        + Op.MUL(Op.SLOAD(key=0x2), Op.SUB(Op.TIMESTAMP, Op.SLOAD(key=0x5)))
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
        + Op.POP * 3
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
        + Op.POP * 3
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
        + Op.POP * 3
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
        + Op.JUMPDEST * 2
        + Op.POP
        + Op.JUMP
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.JUMPI(
            pc=0x327,
            condition=Op.ISZERO(
                Op.EQ(
                    Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.CALLER),
                    Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x0)),
                )
            ),
        )
        + Op.JUMP(pc=0x32C)
        + Op.JUMPDEST
        + Op.JUMP(pc=0x37E)
        + Op.JUMPDEST
        + Op.MUL(Op.SLOAD(key=0x2), Op.SUB(Op.TIMESTAMP, Op.SLOAD(key=0x5)))
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
        + Op.POP * 3
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
        + Op.JUMPDEST * 2
        + Op.POP
        + Op.JUMP,
        storage={
            0: sender,
            1: 66,
            2: 35,
            3: sender,
            5: 0x54C98C81,
        },
        balance=0x186A0,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Bytes(
            "60406103ca600439600451602451336000819055506000600481905550816001819055508060028190555042600581905550336003819055505050610381806100496000396000f30060003560e060020a9004806343d726d61461004257806391b7f5ed14610050578063d686f9ee14610061578063f5bade661461006f578063fcfff16f1461008057005b61004a6101de565b60006000f35b61005b6004356100bf565b60006000f35b610069610304565b60006000f35b61007a60043561008e565b60006000f35b6100886100f0565b60006000f35b600054600160a060020a031633600160a060020a031614156100af576100b4565b6100bc565b806001819055505b50565b600054600160a060020a031633600160a060020a031614156100e0576100e5565b6100ed565b806002819055505b50565b600054600160a060020a031633600160a060020a031614806101255750600354600160a060020a031633600160a060020a0316145b61012e57610161565b60016004819055507f59ebeb90bc63057b6515673c3ecf9438e5058bca0f92585014eced636878c9a560006000a16101dc565b60045460011480610173575060015434105b6101b85760016004819055507f59ebeb90bc63057b6515673c3ecf9438e5058bca0f92585014eced636878c9a560006000a142600581905550336003819055506101db565b33600160a060020a03166000346000600060006000848787f16101d757005b5050505b5b565b60006004546000146101ef576101f4565b610301565b600054600160a060020a031633600160a060020a031614801561022c5750600054600160a060020a0316600354600160a060020a0316145b61023557610242565b6000600481905550610301565b600354600160a060020a031633600160a060020a03161461026257610300565b600554420360025402905060015481116102c757600354600160a060020a0316600082600154036000600060006000848787f161029b57005b505050600054600160a060020a03166000826000600060006000848787f16102bf57005b5050506102ee565b600054600160a060020a031660006001546000600060006000848787f16102ea57005b5050505b60006004819055506000546003819055505b5b50565b6000600054600160a060020a031633600160a060020a031614156103275761032c565b61037e565b600554420360025402905060015481116103455761037d565b600054600160a060020a031660006001546000600060006000848787f161036857005b50505060006004819055506000546003819055505b5b505600000000000000000000000000000000000000000000000000000000000000420000000000000000000000000000000000000000000000000000000000000023"  # noqa: E501
        ),
        gas_limit=600000,
        value=0x186A0,
    )

    post = {
        addr: Account(
            storage={
                0: sender,
                1: 66,
                2: 35,
                3: sender,
                5: 0x54C98C81,
            },
            code=bytes.fromhex(
                "60003560e060020a9004806343d726d61461004257806391b7f5ed14610050578063d686f9ee14610061578063f5bade661461006f578063fcfff16f1461008057005b61004a6101de565b60006000f35b61005b6004356100bf565b60006000f35b610069610304565b60006000f35b61007a60043561008e565b60006000f35b6100886100f0565b60006000f35b600054600160a060020a031633600160a060020a031614156100af576100b4565b6100bc565b806001819055505b50565b600054600160a060020a031633600160a060020a031614156100e0576100e5565b6100ed565b806002819055505b50565b600054600160a060020a031633600160a060020a031614806101255750600354600160a060020a031633600160a060020a0316145b61012e57610161565b60016004819055507f59ebeb90bc63057b6515673c3ecf9438e5058bca0f92585014eced636878c9a560006000a16101dc565b60045460011480610173575060015434105b6101b85760016004819055507f59ebeb90bc63057b6515673c3ecf9438e5058bca0f92585014eced636878c9a560006000a142600581905550336003819055506101db565b33600160a060020a03166000346000600060006000848787f16101d757005b5050505b5b565b60006004546000146101ef576101f4565b610301565b600054600160a060020a031633600160a060020a031614801561022c5750600054600160a060020a0316600354600160a060020a0316145b61023557610242565b6000600481905550610301565b600354600160a060020a031633600160a060020a03161461026257610300565b600554420360025402905060015481116102c757600354600160a060020a0316600082600154036000600060006000848787f161029b57005b505050600054600160a060020a03166000826000600060006000848787f16102bf57005b5050506102ee565b600054600160a060020a031660006001546000600060006000848787f16102ea57005b5050505b60006004819055506000546003819055505b5b50565b6000600054600160a060020a031633600160a060020a031614156103275761032c565b61037e565b600554420360025402905060015481116103455761037d565b600054600160a060020a031660006001546000600060006000848787f161036857005b50505060006004819055506000546003819055505b5b5056"  # noqa: E501
            ),
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
