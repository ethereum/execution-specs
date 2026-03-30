"""
Test_test_store_gas_prices.

Ported from:
state_tests/stSolidityTest/TestStoreGasPricesFiller.json
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
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSolidityTest/TestStoreGasPricesFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_test_store_gas_prices(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_test_store_gas_prices."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x185FBEA9F643C40E33475353B07FA51D0695CA94789492166B67D60FDB6EF7FB
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw
    # 0x7c01000000000000000000000000000000000000000000000000000000006000350463c04062268114602d57005b6033603d565b8060005260206000f35b600060005a600160205590505a81036000555a600260205590505a81036001555a600260205590505a81036002555a65168aa8d53fe660205590505a81036003555a600260205590505a81036004555a600060205590505a81036005555a5060019291505056  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.DIV(
            Op.CALLDATALOAD(offset=0x0),
            0x100000000000000000000000000000000000000000000000000000000,
        )
        + Op.JUMPI(pc=0x2D, condition=Op.EQ(Op.DUP2, 0xC0406226))
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x33]
        + Op.JUMP(pc=0x3D)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.PUSH1[0x0] * 2
        + Op.GAS
        + Op.SSTORE(key=0x20, value=0x1)
        + Op.SWAP1
        + Op.POP
        + Op.SSTORE(key=0x0, value=Op.SUB(Op.DUP2, Op.GAS))
        + Op.GAS
        + Op.SSTORE(key=0x20, value=0x2)
        + Op.SWAP1
        + Op.POP
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.DUP2, Op.GAS))
        + Op.GAS
        + Op.SSTORE(key=0x20, value=0x2)
        + Op.SWAP1
        + Op.POP
        + Op.SSTORE(key=0x2, value=Op.SUB(Op.DUP2, Op.GAS))
        + Op.GAS
        + Op.SSTORE(key=0x20, value=0x168AA8D53FE6)
        + Op.SWAP1
        + Op.POP
        + Op.SSTORE(key=0x3, value=Op.SUB(Op.DUP2, Op.GAS))
        + Op.GAS
        + Op.SSTORE(key=0x20, value=0x2)
        + Op.SWAP1
        + Op.POP
        + Op.SSTORE(key=0x4, value=Op.SUB(Op.DUP2, Op.GAS))
        + Op.GAS
        + Op.SSTORE(key=0x20, value=0x0)
        + Op.SWAP1
        + Op.POP
        + Op.SSTORE(key=0x5, value=Op.SUB(Op.DUP2, Op.GAS))
        + Op.POP(Op.GAS)
        + Op.PUSH1[0x1]
        + Op.SWAP3
        + Op.SWAP2
        + Op.POP * 2
        + Op.JUMP,
        balance=0x186A0,
        nonce=0,
        address=Address(0xFE58F48415DCF9D527F770E3148B769A76EF83F1),  # noqa: E501
    )
    pre[sender] = Account(balance=0x746A528800)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("c0406226"),
        gas_limit=35000000,
    )

    post = {
        target: Account(
            storage={0: 22113, 1: 113, 2: 113, 3: 113, 4: 113, 5: 113},
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
