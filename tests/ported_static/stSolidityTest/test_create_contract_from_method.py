"""
Test_create_contract_from_method.

Ported from:
state_tests/stSolidityTest/CreateContractFromMethodFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSolidityTest/CreateContractFromMethodFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_contract_from_method(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_contract_from_method."""
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
    # 0x60003560e060020a900480637ee17e1214601f578063c040622614602b57005b60256047565b60006000f35b6031603b565b8060005260206000f35b600060436047565b5090565b60006060605d600039606060006000f09050905600605480600c6000396000f30060003560e060020a90048062f55d9d14601e578063b9c3d0a514602d57005b60276004356046565b60006000f35b6033603d565b8060005260206000f35b600060e1905090565b80600160a060020a0316ff5056  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x0)
        + Op.EXP(0x2, 0xE0)
        + Op.SWAP1
        + Op.DIV
        + Op.JUMPI(pc=0x1F, condition=Op.EQ(0x7EE17E12, Op.DUP1))
        + Op.JUMPI(pc=0x2B, condition=Op.EQ(0xC0406226, Op.DUP1))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x25]
        + Op.JUMP(pc=0x47)
        + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0)
        + Op.JUMPDEST
        + Op.PUSH1[0x31]
        + Op.JUMP(pc=0x3B)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.PUSH1[0x43]
        + Op.JUMP(pc=0x47)
        + Op.JUMPDEST
        + Op.POP
        + Op.SWAP1
        + Op.JUMP
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.CODECOPY(dest_offset=0x0, offset=0x5D, size=0x60)
        + Op.CREATE(value=0x0, offset=0x0, size=0x60)
        + Op.SWAP1
        + Op.POP
        + Op.SWAP1
        + Op.JUMP
        + Op.STOP
        + Op.PUSH1[0x54]
        + Op.CODECOPY(dest_offset=0x0, offset=0xC, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.STOP
        + Op.CALLDATALOAD(offset=0x0)
        + Op.EXP(0x2, 0xE0)
        + Op.SWAP1
        + Op.DIV
        + Op.JUMPI(pc=0x1E, condition=Op.EQ(0xF55D9D, Op.DUP1))
        + Op.JUMPI(pc=0x2D, condition=Op.EQ(0xB9C3D0A5, Op.DUP1))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x27]
        + Op.CALLDATALOAD(offset=0x4)
        + Op.JUMP(pc=0x46)
        + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0)
        + Op.JUMPDEST
        + Op.PUSH1[0x33]
        + Op.JUMP(pc=0x3D)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.PUSH1[0xE1]
        + Op.SWAP1
        + Op.POP
        + Op.SWAP1
        + Op.JUMP
        + Op.JUMPDEST
        + Op.SELFDESTRUCT(
            address=Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.DUP1)
        )
        + Op.POP
        + Op.JUMP,
        balance=0x186A0,
        nonce=0,
        address=Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5F5E100)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes("c0406226"),
        gas_limit=350000,
        value=1,
    )

    post = {
        contract_0: Account(nonce=1),
        compute_create_address(address=contract_0, nonce=0): Account(
            storage={},
            code=bytes.fromhex(
                "60003560e060020a90048062f55d9d14601e578063b9c3d0a514602d57005b60276004356046565b60006000f35b6033603d565b8060005260206000f35b600060e1905090565b80600160a060020a0316ff5056"  # noqa: E501
            ),
            balance=0,
            nonce=1,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
