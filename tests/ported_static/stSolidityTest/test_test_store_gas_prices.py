"""
Measure SSTORE gas for zero, non-zero, same and huge value changes.

Ported from:
state_tests/stSolidityTest/TestStoreGasPricesFiller.json

@manually-enhanced: Do not overwrite. Expected readings are derived
from SSTORE metadata.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Fork,
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
def test_test_store_gas_prices(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Store the gas of each SSTORE window in slots 0-5."""
    sender = pre.fund_eoa()

    # Source: raw
    # 0x7c01000000000000000000000000000000000000000000000000000000006000350463c04062268114602d57005b6033603d565b8060005260206000f35b600060005a600160205590505a81036000555a600260205590505a81036001555a600260205590505a81036002555a65168aa8d53fe660205590505a81036003555a600260205590505a81036004555a600060205590505a81036005555a5060019291505056  # noqa: E501
    target = pre.deploy_contract(
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
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("c0406226"),
        state_gas_reservoir=0,
    )

    # Each window spans the SSTORE with its pushes, SWAP1, POP and GAS;
    # a state gas refund is credited inside the window.
    values = [0, 1, 2, 2, 0x168AA8D53FE6, 2, 0]
    storage = {}
    for slot, (current, new) in enumerate(
        zip(values, values[1:], strict=False)
    ):
        window = (
            Op.SSTORE(
                key=0x20,
                value=new,
                key_warm=slot > 0,
                original_value=0,
                current_value=current,
                new_value=new,
            )
            + Op.SWAP1
            + Op.POP
            + Op.GAS
        )
        storage[slot] = (
            window.gas_cost(fork) - window.state_refund(fork)
        ) % 2**256
    post = {target: Account(storage=storage)}

    state_test(pre=pre, post=post, tx=tx)
