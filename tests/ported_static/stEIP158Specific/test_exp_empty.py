"""
Test_exp_empty.

Ported from:
state_tests/stEIP158Specific/EXP_EmptyFiller.json
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
    ["state_tests/stEIP158Specific/EXP_EmptyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_exp_empty(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_exp_empty."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { [0](GAS) [[1]](EXP 0 12)  [[2]](SUB @0 (GAS)) [0](GAS) [[3]](EXP 12 0) [[4]](SUB @0 (GAS)) [0](GAS) [[5]](EXP 0 0xffffffffffffffff) [[6]](SUB @0 (GAS)) [0](GAS) [[7]](EXP 0 0xffffffffffffffffffffffffffffffff) [[8]](SUB @0 (GAS)) [0](GAS) [[9]](EXP 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) [[10]](SUB @0 (GAS)) [0](GAS) [[11]](EXP 0xffffffffffffffff 0) [[12]](SUB @0 (GAS)) [0](GAS) [[13]](EXP 0xffffffffffffffffffffffffffffffff 0) [[14]](SUB @0 (GAS)) [0] (GAS) [[15]](EXP 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0) [[100]] (SUB @0 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x1, value=Op.EXP(0x0, 0xC))
        + Op.SSTORE(key=0x2, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x3, value=Op.EXP(0xC, 0x0))
        + Op.SSTORE(key=0x4, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x5, value=Op.EXP(0x0, 0xFFFFFFFFFFFFFFFF))
        + Op.SSTORE(key=0x6, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(
            key=0x7, value=Op.EXP(0x0, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        )
        + Op.SSTORE(key=0x8, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(
            key=0x9,
            value=Op.EXP(
                0x0,
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            ),
        )
        + Op.SSTORE(key=0xA, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0xB, value=Op.EXP(0xFFFFFFFFFFFFFFFF, 0x0))
        + Op.SSTORE(key=0xC, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(
            key=0xD, value=Op.EXP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, 0x0)
        )
        + Op.SSTORE(key=0xE, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(
            key=0xF,
            value=Op.EXP(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                0x0,
            ),
        )
        + Op.SSTORE(key=0x64, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        target: Account(
            storage={
                2: 2280,
                3: 1,
                4: 22127,
                6: 2627,
                8: 3027,
                10: 3827,
                11: 1,
                12: 22127,
                13: 1,
                14: 22127,
                15: 1,
                100: 22127,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
