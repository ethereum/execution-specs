"""
Test_recursive_create_contracts_create4_contracts.

Ported from:
state_tests/stSolidityTest/RecursiveCreateContractsCreate4ContractsFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stSolidityTest/RecursiveCreateContractsCreate4ContractsFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_recursive_create_contracts_create4_contracts(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_recursive_create_contracts_create4_contracts."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
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

    # Source: raw
    # 0x60003560e060020a90048063820b13f614610021578063a444f5e91461003257005b61002c600435610093565b60006000f35b61003d600435610043565b60006000f35b600073095e7baea6a6c7c4c2dfeb977efac326af552d8760008190555081600181905550606b6101ad600039606b600054600160a060020a0316815260200182815260200160006000f090505050565b600060c86100e560003960c8600054600160a060020a0316815260200182815260200160006000f0905080600160a060020a0316600060026000600060006000848787f16100dd57005b50505050505600604060c860043960045160245160006001820391508160008190555060008211602657604c565b606b605d600039606b83600160a060020a0316815260200182815260200160006000f090505b505050600180605c6000396000f300006040606b6004396004516024516001810390508060008190555060008111602457605b565b81600160a060020a031663820b13f6600060008260e060020a026000526004858152602001600060008660325a03f1605857005b50505b5050600180606a6000396000f300006040606b6004396004516024516001810390508060008190555060008111602457605b565b81600160a060020a031663820b13f6600060008260e060020a026000526004858152602001600060008660325a03f1605857005b50505b5050600180606a6000396000f30000  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x0)
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
            value=Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x0)),
        )
        + Op.PUSH1[0x20]
        + Op.ADD
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP3)
        + Op.PUSH1[0x20]
        + Op.CREATE(value=0x0, offset=0x0, size=Op.ADD)
        + Op.SWAP1
        + Op.POP * 3
        + Op.JUMP
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.CODECOPY(dest_offset=0x0, offset=Op.PUSH2[0xE5], size=0xC8)
        + Op.PUSH1[0xC8]
        + Op.MSTORE(
            offset=Op.DUP2,
            value=Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.SLOAD(key=0x0)),
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
        + Op.POP * 5
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
        + Op.POP * 3
        + Op.PUSH1[0x1]
        + Op.CODECOPY(dest_offset=0x0, offset=0x5C, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.STOP * 2
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
        + Op.PUSH1[0x0] * 2
        + Op.MSTORE(offset=0x0, value=Op.MUL(Op.EXP(0x2, 0xE0), Op.DUP3))
        + Op.PUSH1[0x4]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP6)
        + Op.PUSH1[0x20]
        + Op.ADD
        + Op.PUSH1[0x0] * 2
        + Op.DUP7
        + Op.SUB(Op.GAS, 0x32)
        + Op.JUMPI(pc=0x58, condition=Op.CALL)
        + Op.STOP
        + Op.JUMPDEST
        + Op.POP * 2
        + Op.JUMPDEST
        + Op.POP * 2
        + Op.PUSH1[0x1]
        + Op.CODECOPY(dest_offset=0x0, offset=0x6A, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.STOP * 2
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
        + Op.PUSH1[0x0] * 2
        + Op.MSTORE(offset=0x0, value=Op.MUL(Op.EXP(0x2, 0xE0), Op.DUP3))
        + Op.PUSH1[0x4]
        + Op.MSTORE(offset=Op.DUP2, value=Op.DUP6)
        + Op.PUSH1[0x20]
        + Op.ADD
        + Op.PUSH1[0x0] * 2
        + Op.DUP7
        + Op.SUB(Op.GAS, 0x32)
        + Op.JUMPI(pc=0x58, condition=Op.CALL)
        + Op.STOP
        + Op.JUMPDEST
        + Op.POP * 2
        + Op.JUMPDEST
        + Op.POP * 2
        + Op.PUSH1[0x1]
        + Op.CODECOPY(dest_offset=0x0, offset=0x6A, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.STOP * 2,
        balance=0x314DC6448D9338C15B0A00000000,
        nonce=0,
        address=Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87),  # noqa: E501
    )
    pre[sender] = Account(balance=0x1DCD6500)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes("a444f5e9") + Hash(0x4),
        gas_limit=300000,
        value=1,
    )

    post = {
        contract_0: Account(
            storage={
                0: 0x95E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87,
                1: 4,
            },
            nonce=3,
        ),
        Address(0x2B25AE4B13CB6E06869F694D29DE45E7614EBD97): Account(
            storage={0: 1}, nonce=1
        ),
        compute_create_address(address=contract_0, nonce=2): Account(
            balance=2, nonce=1
        ),
        sender: Account(nonce=1),
        compute_create_address(address=contract_0, nonce=1): Account(
            storage={0: 2}, balance=2, nonce=2
        ),
        compute_create_address(address=contract_0, nonce=0): Account(
            storage={0: 3}, nonce=1
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
