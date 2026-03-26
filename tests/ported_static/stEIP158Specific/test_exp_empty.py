"""
test_exp_empty

Ported from:
state_tests/stEIP158Specific/EXP_EmptyFiller.json
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
    ["state_tests/stEIP158Specific/EXP_EmptyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_exp_empty(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_exp_empty"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # { [0](GAS) [[1]](EXP 0 12)  [[2]](SUB @0 (GAS)) [0](GAS) [[3]](EXP 12 0) [[4]](SUB @0 (GAS)) [0](GAS) [[5]](EXP 0 0xffffffffffffffff) [[6]](SUB @0 (GAS)) [0](GAS) [[7]](EXP 0 0xffffffffffffffffffffffffffffffff) [[8]](SUB @0 (GAS)) [0](GAS) [[9]](EXP 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) [[10]](SUB @0 (GAS)) [0](GAS) [[11]](EXP 0xffffffffffffffff 0) [[12]](SUB @0 (GAS)) [0](GAS) [[13]](EXP 0xffffffffffffffffffffffffffffffff 0) [[14]](SUB @0 (GAS)) [0] (GAS) [[15]](EXP 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0) [[100]] (SUB @0 (GAS)) }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x1, value=Op.EXP(0x0, 0xc))
        + Op.SSTORE(key=0x2, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x3, value=Op.EXP(0xc, 0x0))
        + Op.SSTORE(key=0x4, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x5, value=Op.EXP(0x0, 0xffffffffffffffff))
        + Op.SSTORE(key=0x6, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x7, value=Op.EXP(0x0, 0xffffffffffffffffffffffffffffffff))  # noqa: E501
        + Op.SSTORE(key=0x8, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x9, value=Op.EXP(0x0, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff))  # noqa: E501
        + Op.SSTORE(key=0xa, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0xb, value=Op.EXP(0xffffffffffffffff, 0x0))
        + Op.SSTORE(key=0xc, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0xd, value=Op.EXP(0xffffffffffffffffffffffffffffffff, 0x0))  # noqa: E501
        + Op.SSTORE(key=0xe, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0xf, value=Op.EXP(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, 0x0))  # noqa: E501
        + Op.SSTORE(key=0x64, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        nonce=0,
        address=Address("0x8a3c9879fc69c8c45c1201c27da63312e9e9f6fe"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=600000,
        nonce=0,
        gas_price=10,
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
