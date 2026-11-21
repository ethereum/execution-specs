"""
Test_quadratic_complexity_solidity_call_data_copy.

Ported from:
state_tests/stQuadraticComplexityTest/QuadraticComplexitySolidity_CallDataCopyFiller.json

@manually-enhanced: Do not overwrite. The loop calls the deployed
CALLDATACOPY contract; the large arm uses a 2**24 gas limit.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stQuadraticComplexityTest/QuadraticComplexitySolidity_CallDataCopyFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
    ],
)
def test_quadratic_complexity_solidity_call_data_copy(
    state_test: StateTestFiller,
    pre: Alloc,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_quadratic_complexity_solidity_call_data_copy."""
    sender = pre.fund_eoa()

    # Source: lll
    # { (CALLDATACOPY 0 0 50000) }
    contract_1 = pre.deploy_contract(
        code=Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=0xC350)
        + Op.STOP,
    )
    contract_0 = pre.deploy_contract(
        code=Op.CALLDATALOAD(offset=0x0)
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
        + Op.PUSH20[contract_1]
        + Op.SWAP1
        + Op.POP
        + Op.JUMPDEST
        + Op.JUMPI(pc=0xBF, condition=Op.ISZERO(Op.SGT(Op.DUP3, 0x0)))
        + Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.DUP1)
        + Op.PUSH1[0x0] * 3
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
        + Op.PUSH1[0x0] * 2
        + Op.DUP6
        + Op.SUB(Op.GAS, 0x15)
        + Op.POP(Op.CALL)
        + Op.POP
        + Op.SUB(Op.DUP3, 0x1)
        + Op.SWAP2
        + Op.POP
        + Op.JUMP(pc=0x45)
        + Op.JUMPDEST
        + Op.POP * 2
        + Op.JUMP,
    )

    tx_data = [
        Bytes("61a47706") + Hash(0xC350),
    ]
    tx_gas = [150000, 2**24]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {
        contract_0: Account(storage={}),
        contract_1: Account(storage={}),
    }

    state_test(pre=pre, post=post, tx=tx)
