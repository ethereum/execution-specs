"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stQuadraticComplexityTest
QuadraticComplexitySolidity_CallDataCopyFiller.json
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
        "tests/static/state_tests/stQuadraticComplexityTest/QuadraticComplexitySolidity_CallDataCopyFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_gas_limit, expected_post",
    [
        (150000, {}),
        (250000000, {}),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_quadratic_complexity_solidity_call_data_copy(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x6A7EEAC5F12B409D42028F66B0B2132535EE158CFDA439E3BFDD4558E8F4BF6C
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=350000000,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x0)
            + Op.EXP(0x2, 0xE0)
            + Op.SWAP1
            + Op.DIV
            + Op.JUMPI(pc=0x15, condition=Op.EQ(0x61A47706, Op.DUP1))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x1E]
            + Op.CALLDATALOAD(offset=0x4)
            + Op.JUMP(pc=0x24)
            + Op.JUMPDEST
            + Op.RETURN(offset=0x0, size=0x0)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.DUP2
            + Op.PUSH1[0x0]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.PUSH20[0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B]
            + Op.SWAP1
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xBF, condition=Op.ISZERO(Op.SGT(Op.DUP3, 0x0)))
            + Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.MSTORE(
                offset=Op.DUP2,
                value=0x6A75737400000000000000000000000000000000000000000000000000000000,  # noqa: E501
            )
            + Op.PUSH1[0x4]
            + Op.ADD
            + Op.MSTORE(
                offset=Op.DUP2,
                value=0x63616C6C00000000000000000000000000000000000000000000000000000000,  # noqa: E501
            )
            + Op.PUSH1[0x20]
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.DUP6
            + Op.SUB(Op.GAS, 0x15)
            + Op.POP(Op.CALL)
            + Op.POP
            + Op.SUB(Op.DUP3, 0x1)
            + Op.SWAP2
            + Op.POP
            + Op.JUMP(pc=0x45)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.JUMP
        ),
        balance=0x11C37937E08000,
        nonce=0,
        address=Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: LLL
    # { (CALLDATACOPY 0 0 50000) }
    pre.deploy_contract(
        code=(
            Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=0xC350) + Op.STOP
        ),
        balance=0x4C4B40,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x11C37937E08000)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "61a47706000000000000000000000000000000000000000000000000000000000000c350"  # noqa: E501
        ),
        gas_limit=tx_gas_limit,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
