"""
test_contract_inheritance

Ported from:
state_tests/stSolidityTest/ContractInheritanceFiller.json
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
    ["state_tests/stSolidityTest/ContractInheritanceFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_contract_inheritance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_contract_inheritance"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xa9ae12cb2700c0214f86b9796881bc03a1fd5605d0e76d2da2ca592e62d53e52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw
    # 0x7c010000000000000000000000000000000000000000000000000000000060003504633e0bca3b8114610039578063c0406226146100a857005b6100b55b600160008060456101ec8339604560006000f091508173ffffffffffffffffffffffffffffffffffffffff166381bda09b60206000827c010000000000000000000000000000000000000000000000000000000002600052600460006000866161da5a03f161011957005b6100bf60006100c961003d565b8060005260206000f35b8060005260206000f35b600080547fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0016919091179081905560ff16919050565b505060005163ffffffff166002141561019d575b5b505090565b505060005163ffffffff1660011415610194575b60456101a7600039604560006000f090508073ffffffffffffffffffffffffffffffffffffffff166381bda09b60206000827c010000000000000000000000000000000000000000000000000000000002600052600460006000866161da5a03f16100ff57005b60009250610114565b600092506101145600603980600c6000396000f3007c0100000000000000000000000000000000000000000000000000000000600035046381bda09b8114602d57005b60026000818152602090f3603980600c6000396000f3007c0100000000000000000000000000000000000000000000000000000000600035046381bda09b8114602d57005b60016000818152602090f3
    target = pre.deploy_contract(
        code=Op.DIV(Op.CALLDATALOAD(offset=0x0), 0x100000000000000000000000000000000000000000000000000000000)
        + Op.JUMPI(pc=Op.PUSH2[0x39], condition=Op.EQ(Op.DUP2, 0x3e0bca3b))
        + Op.JUMPI(pc=Op.PUSH2[0xa8], condition=Op.EQ(0xc0406226, Op.DUP1))
        + Op.STOP + Op.JUMPDEST + Op.PUSH2[0xb5] + Op.JUMPDEST + Op.PUSH1[0x1]
        + Op.PUSH1[0x0] + Op.DUP1
        + Op.CODECOPY(dest_offset=Op.DUP4, offset=0x1ec, size=0x45)
        + Op.CREATE(value=0x0, offset=0x0, size=0x45) + Op.SWAP2 + Op.POP
        + Op.AND(0xffffffffffffffffffffffffffffffffffffffff, Op.DUP2)
        + Op.PUSH4[0x81bda09b] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.MSTORE(offset=0x0, value=Op.MUL(0x100000000000000000000000000000000000000000000000000000000, Op.DUP3))
        + Op.PUSH1[0x4] + Op.PUSH1[0x0] * 2 + Op.DUP7 + Op.SUB(Op.GAS, 0x61da)
        + Op.JUMPI(pc=0x119, condition=Op.CALL) + Op.STOP + Op.JUMPDEST
        + Op.PUSH2[0xbf] + Op.PUSH1[0x0] + Op.PUSH2[0xc9]
        + Op.JUMP(pc=Op.PUSH2[0x3d]) + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1) + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20) + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.AND(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00, Op.SLOAD(key=Op.DUP1))  # noqa: E501
        + Op.SWAP2 + Op.SWAP1 + Op.SWAP2 + Op.OR + Op.SWAP1 + Op.DUP2 + Op.SWAP1
        + Op.SSTORE + Op.PUSH1[0xff] + Op.AND + Op.SWAP2 + Op.SWAP1 + Op.POP
        + Op.JUMP + Op.JUMPDEST + Op.POP * 2
        + Op.JUMPI(pc=0x19d, condition=Op.ISZERO(Op.EQ(0x2, Op.AND(0xffffffff, Op.MLOAD(offset=0x0)))))
        + Op.JUMPDEST * 2 + Op.POP * 2 + Op.SWAP1 + Op.JUMP + Op.JUMPDEST
        + Op.POP * 2
        + Op.JUMPI(pc=0x194, condition=Op.ISZERO(Op.EQ(0x1, Op.AND(0xffffffff, Op.MLOAD(offset=0x0)))))
        + Op.JUMPDEST + Op.CODECOPY(dest_offset=0x0, offset=0x1a7, size=0x45)
        + Op.CREATE(value=0x0, offset=0x0, size=0x45) + Op.SWAP1 + Op.POP
        + Op.AND(0xffffffffffffffffffffffffffffffffffffffff, Op.DUP1)
        + Op.PUSH4[0x81bda09b] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.MSTORE(offset=0x0, value=Op.MUL(0x100000000000000000000000000000000000000000000000000000000, Op.DUP3))
        + Op.PUSH1[0x4] + Op.PUSH1[0x0] * 2 + Op.DUP7 + Op.SUB(Op.GAS, 0x61da)
        + Op.JUMPI(pc=Op.PUSH2[0xff], condition=Op.CALL) + Op.STOP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.SWAP3 + Op.POP + Op.JUMP(pc=0x114) + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.SWAP3 + Op.POP + Op.JUMP(pc=0x114) + Op.STOP
        + Op.PUSH1[0x39] + Op.CODECOPY(dest_offset=0x0, offset=0xc, size=Op.DUP1)
        + Op.PUSH1[0x0] + Op.RETURN + Op.STOP
        + Op.DIV(Op.CALLDATALOAD(offset=0x0), 0x100000000000000000000000000000000000000000000000000000000)
        + Op.JUMPI(pc=0x2d, condition=Op.EQ(Op.DUP2, 0x81bda09b)) + Op.STOP
        + Op.JUMPDEST + Op.PUSH1[0x2] + Op.PUSH1[0x0]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2) + Op.PUSH1[0x20] + Op.SWAP1
        + Op.RETURN + Op.PUSH1[0x39]
        + Op.CODECOPY(dest_offset=0x0, offset=0xc, size=Op.DUP1) + Op.PUSH1[0x0]
        + Op.RETURN + Op.STOP
        + Op.DIV(Op.CALLDATALOAD(offset=0x0), 0x100000000000000000000000000000000000000000000000000000000)
        + Op.JUMPI(pc=0x2d, condition=Op.EQ(Op.DUP2, 0x81bda09b)) + Op.STOP
        + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2) + Op.PUSH1[0x20] + Op.SWAP1
        + Op.RETURN,
        balance=0x186a0,
        nonce=0,
        address=Address("0x3809b123c157b2d0d3b998255f35b5f8b8ae4789"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x12a05f200)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("c0406226"),
        gas_limit=35000000,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
