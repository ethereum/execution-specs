"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stEIP158Specific/EXP_EmptyFiller.json
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
    ["tests/static/state_tests/stEIP158Specific/EXP_EmptyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_exp_empty(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: LLL
    # { [0](GAS) [[1]](EXP 0 12)  [[2]](SUB @0 (GAS)) [0](GAS) [[3]](EXP 12 0) [[4]](SUB @0 (GAS)) [0](GAS) [[5]](EXP 0 0xffffffffffffffff) [[6]](SUB @0 (GAS)) [0](GAS) [[7]](EXP 0 0xffffffffffffffffffffffffffffffff) [[8]](SUB @0 (GAS)) [0](GAS) [[9]](EXP 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) [[10]](SUB @0 (GAS)) [0](GAS) [[11]](EXP 0xffffffffffffffff 0) [[12]](SUB @0 (GAS)) [0](GAS) [[13]](EXP 0xffffffffffffffffffffffffffffffff 0) [[14]](SUB @0 (GAS)) [0] (GAS) [[15]](EXP 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0) [[100]] (SUB @0 (GAS)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
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
                key=0x7,
                value=Op.EXP(0x0, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
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
                key=0xD,
                value=Op.EXP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, 0x0),
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
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x8a3c9879fc69c8c45c1201c27da63312e9e9f6fe"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=600000,
    )

    post = {
        contract: Account(
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
