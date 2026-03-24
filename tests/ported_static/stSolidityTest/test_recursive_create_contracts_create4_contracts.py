"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSolidityTest
RecursiveCreateContractsCreate4ContractsFiller.json
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
        "tests/static/state_tests/stSolidityTest/RecursiveCreateContractsCreate4ContractsFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_recursive_create_contracts_create4_contracts(
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
        gas_limit=100000000,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x0)
            + Op.EXP(0x2, 0xE0)
            + Op.SWAP1
            + Op.DIV
            + Op.JUMPI(pc=Op.PUSH2[0x21], condition=Op.EQ(0x820B13F6, Op.DUP1))
            + Op.JUMPI(pc=Op.PUSH2[0x32], condition=Op.EQ(0xA444F5E9, Op.DUP1))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH2[0x2C]
            + Op.CALLDATALOAD(offset=0x4)
            + Op.JUMP(pc=Op.PUSH2[0x93])
            + Op.JUMPDEST
            + Op.RETURN(offset=0x0, size=0x0)
            + Op.JUMPDEST
            + Op.PUSH2[0x3D]
            + Op.CALLDATALOAD(offset=0x4)
            + Op.JUMP(pc=Op.PUSH2[0x43])
            + Op.JUMPDEST
            + Op.RETURN(offset=0x0, size=0x0)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH20[0x95E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87]
            + Op.PUSH1[0x0]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.DUP2
            + Op.PUSH1[0x1]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.CODECOPY(dest_offset=0x0, offset=0x1AD, size=0x6B)
            + Op.PUSH1[0x6B]
            + Op.MSTORE(
                offset=Op.DUP2,
                value=Op.AND(
                    Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x0)
                ),
            )
            + Op.PUSH1[0x20]
            + Op.ADD
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP3)
            + Op.PUSH1[0x20]
            + Op.CREATE(value=0x0, offset=0x0, size=Op.ADD)
            + Op.SWAP1
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.JUMP
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.CODECOPY(dest_offset=0x0, offset=Op.PUSH2[0xE5], size=0xC8)
            + Op.PUSH1[0xC8]
            + Op.MSTORE(
                offset=Op.DUP2,
                value=Op.AND(
                    Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x0)
                ),
            )
            + Op.PUSH1[0x20]
            + Op.ADD
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP3)
            + Op.PUSH1[0x20]
            + Op.CREATE(value=0x0, offset=0x0, size=Op.ADD)
            + Op.SWAP1
            + Op.POP
            + Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x2]
            + Op.JUMPI(
                pc=Op.PUSH2[0xDD],
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
            + Op.POP
            + Op.POP
            + Op.JUMP
            + Op.STOP
            + Op.CODECOPY(dest_offset=0x4, offset=0xC8, size=0x40)
            + Op.MLOAD(offset=0x4)
            + Op.MLOAD(offset=0x24)
            + Op.PUSH1[0x0]
            + Op.SUB(Op.DUP3, 0x1)
            + Op.SWAP2
            + Op.POP
            + Op.DUP2
            + Op.PUSH1[0x0]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.JUMPI(pc=0x26, condition=Op.GT(Op.DUP3, 0x0))
            + Op.JUMP(pc=0x4C)
            + Op.JUMPDEST
            + Op.CODECOPY(dest_offset=0x0, offset=0x5D, size=0x6B)
            + Op.PUSH1[0x6B]
            + Op.MSTORE(
                offset=Op.DUP2,
                value=Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.DUP4),
            )
            + Op.PUSH1[0x20]
            + Op.ADD
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP3)
            + Op.PUSH1[0x20]
            + Op.CREATE(value=0x0, offset=0x0, size=Op.ADD)
            + Op.SWAP1
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x1]
            + Op.CODECOPY(dest_offset=0x0, offset=0x5C, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.RETURN
            + Op.STOP
            + Op.STOP
            + Op.CODECOPY(dest_offset=0x4, offset=0x6B, size=0x40)
            + Op.MLOAD(offset=0x4)
            + Op.MLOAD(offset=0x24)
            + Op.SUB(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.DUP1
            + Op.PUSH1[0x0]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.JUMPI(pc=0x24, condition=Op.GT(Op.DUP2, 0x0))
            + Op.JUMP(pc=0x5B)
            + Op.JUMPDEST
            + Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.DUP2)
            + Op.PUSH4[0x820B13F6]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.MSTORE(offset=0x0, value=Op.MUL(Op.EXP(0x2, 0xE0), Op.DUP3))
            + Op.PUSH1[0x4]
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP6)
            + Op.PUSH1[0x20]
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.DUP7
            + Op.SUB(Op.GAS, 0x32)
            + Op.JUMPI(pc=0x58, condition=Op.CALL)
            + Op.STOP
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x1]
            + Op.CODECOPY(dest_offset=0x0, offset=0x6A, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.RETURN
            + Op.STOP
            + Op.STOP
            + Op.CODECOPY(dest_offset=0x4, offset=0x6B, size=0x40)
            + Op.MLOAD(offset=0x4)
            + Op.MLOAD(offset=0x24)
            + Op.SUB(Op.DUP2, 0x1)
            + Op.SWAP1
            + Op.POP
            + Op.DUP1
            + Op.PUSH1[0x0]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.JUMPI(pc=0x24, condition=Op.GT(Op.DUP2, 0x0))
            + Op.JUMP(pc=0x5B)
            + Op.JUMPDEST
            + Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.DUP2)
            + Op.PUSH4[0x820B13F6]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.MSTORE(offset=0x0, value=Op.MUL(Op.EXP(0x2, 0xE0), Op.DUP3))
            + Op.PUSH1[0x4]
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP6)
            + Op.PUSH1[0x20]
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.DUP7
            + Op.SUB(Op.GAS, 0x32)
            + Op.JUMPI(pc=0x58, condition=Op.CALL)
            + Op.STOP
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x1]
            + Op.CODECOPY(dest_offset=0x0, offset=0x6A, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.RETURN
            + Op.STOP
            + Op.STOP
        ),
        balance=0x314DC6448D9338C15B0A00000000,
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x1DCD6500)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "a444f5e90000000000000000000000000000000000000000000000000000000000000004"  # noqa: E501
        ),
        gas_limit=300000,
        value=1,
    )

    post = {
        contract: Account(
            storage={
                0: 0x95E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87,
                1: 4,
            },
        ),
        Address("0x2b25ae4b13cb6e06869f694d29de45e7614ebd97"): Account(
            storage={0: 1},
        ),
        Address("0xb88de88b35ecbf3c141e3caae2baf35834d18f63"): Account(
            storage={0: 2},
        ),
        Address("0xd2571607e241ecf590ed94b12d87c94babe36db6"): Account(
            storage={0: 3},
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
