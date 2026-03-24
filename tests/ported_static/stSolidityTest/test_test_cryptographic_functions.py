"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSolidityTest/TestCryptographicFunctionsFiller.json
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
        "tests/static/state_tests/stSolidityTest/TestCryptographicFunctionsFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_test_cryptographic_functions(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x0)
            + Op.PUSH29[
                0x100000000000000000000000000000000000000000000000000000000
            ]
            + Op.SWAP1
            + Op.DIV
            + Op.JUMPI(pc=Op.PUSH2[0x3A], condition=Op.EQ(0xC0406226, Op.DUP1))
            + Op.JUMPI(pc=Op.PUSH2[0x4C], condition=Op.EQ(0xE0A9FD28, Op.DUP1))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH2[0x42]
            + Op.JUMP(pc=Op.PUSH2[0x5E])
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=Op.DUP1)
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH2[0x54]
            + Op.JUMP(pc=Op.PUSH2[0x99])
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=Op.DUP1)
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH2[0x68]
            + Op.JUMP(pc=Op.PUSH2[0x99])
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.EXP(0x100, 0x0)
            + Op.AND(Op.NOT(Op.MUL(0xFF, Op.DUP2)), Op.SLOAD(key=Op.DUP2))
            + Op.SWAP1
            + Op.OR(Op.MUL, Op.DUP4)
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.SLOAD
            + Op.SWAP1
            + Op.PUSH2[0x100]
            + Op.EXP
            + Op.SWAP1
            + Op.AND(0xFF, Op.DIV)
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=Op.PUSH2[0x96])
            + Op.JUMPDEST
            + Op.SWAP1
            + Op.JUMP
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x1]
            + Op.SWAP1
            + Op.POP
            + Op.POP(Op.DUP1)
            + Op.MUL(
                0x1,
                0x43C4B4524ADB81E4E9A5C4648A98E9D320E3908AC5B6C889144B642CD08AE16D,  # noqa: E501
            )
            + Op.PUSH1[0x40]
            + Op.MSTORE(
                offset=Op.DUP2,
                value=0x74657374737472696E6700000000000000000000000000000000000000000000,  # noqa: E501
            )
            + Op.PUSH1[0xA]
            + Op.ADD
            + Op.PUSH1[0x40]
            + Op.SWAP1
            + Op.SHA3(offset=0x40, size=Op.SUB)
            + Op.JUMPI(pc=Op.PUSH2[0xFF], condition=Op.ISZERO(Op.EQ))
            + Op.JUMP(pc=0x108)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x2EC)
            + Op.JUMPDEST
            + Op.MUL(
                0x1,
                0x3C8727E019A42B444667A587B6001251BECADABBB36BFED8087A92C18882D111,  # noqa: E501
            )
            + Op.PUSH1[0x2]
            + Op.PUSH1[0x20]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.MSTORE(
                offset=Op.DUP2,
                value=0x74657374737472696E6700000000000000000000000000000000000000000000,  # noqa: E501
            )
            + Op.PUSH1[0xA]
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.DUP6
            + Op.SUB(Op.GAS, 0x61DA)
            + Op.JUMPI(pc=0x16B, condition=Op.CALL)
            + Op.STOP
            + Op.JUMPDEST
            + Op.POP
            + Op.MLOAD(offset=0x0)
            + Op.JUMPI(pc=0x17A, condition=Op.ISZERO(Op.EQ))
            + Op.JUMP(pc=0x183)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x2EC)
            + Op.JUMPDEST
            + Op.MUL(
                0x1000000000000000000000000,
                0xCD566972B5E50104011A92B59FA8E0B1234851AE,
            )
            + Op.PUSH1[0x3]
            + Op.PUSH1[0x20]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.MSTORE(
                offset=Op.DUP2,
                value=0x74657374737472696E6700000000000000000000000000000000000000000000,  # noqa: E501
            )
            + Op.PUSH1[0xA]
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.DUP6
            + Op.SUB(Op.GAS, 0x61DA)
            + Op.JUMPI(pc=0x1E6, condition=Op.CALL)
            + Op.STOP
            + Op.JUMPDEST
            + Op.POP
            + Op.MUL(0x1000000000000000000000000, Op.MLOAD(offset=0x0))
            + Op.JUMPI(pc=0x204, condition=Op.ISZERO(Op.EQ))
            + Op.JUMP(pc=0x20D)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x2EC)
            + Op.JUMPDEST
            + Op.PUSH20[0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B]
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x20]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.MSTORE(
                offset=Op.DUP2,
                value=Op.MUL(
                    0x1,
                    0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C,  # noqa: E501
                ),
            )
            + Op.PUSH1[0x20]
            + Op.ADD
            + Op.MSTORE(offset=Op.DUP2, value=0x1C)
            + Op.PUSH1[0x20]
            + Op.ADD
            + Op.MSTORE(
                offset=Op.DUP2,
                value=Op.MUL(
                    0x1,
                    0x73B1693892219D736CABA55BDB67216E485557EA6B6AF75F37096C9AA6A5A75F,  # noqa: E501
                ),
            )
            + Op.PUSH1[0x20]
            + Op.ADD
            + Op.MSTORE(
                offset=Op.DUP2,
                value=Op.MUL(
                    0x1,
                    0xEEB940B1D03B21E36B0E47E79769F095FE2AB855BD91E3A38756B7D75A9C4549,  # noqa: E501
                ),
            )
            + Op.PUSH1[0x20]
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.DUP6
            + Op.SUB(Op.GAS, 0x61DA)
            + Op.JUMPI(pc=0x2BD, condition=Op.CALL)
            + Op.STOP
            + Op.JUMPDEST
            + Op.POP
            + Op.AND(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                Op.MLOAD(offset=0x0),
            )
            + Op.JUMPI(pc=0x2E2, condition=Op.ISZERO(Op.EQ))
            + Op.JUMP(pc=0x2EB)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x2EC)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.SWAP1
            + Op.JUMP
        ),
        balance=0x186A0,
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x12A05F200)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("c0406226"),
        gas_limit=35000000,
        value=100,
    )

    post = {
        contract: Account(storage={0: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
