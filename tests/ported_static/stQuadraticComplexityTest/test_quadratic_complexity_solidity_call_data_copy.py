"""
Test_quadratic_complexity_solidity_call_data_copy.

Ported from:
state_tests/stQuadraticComplexityTest/QuadraticComplexitySolidity_CallDataCopyFiller.json
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
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stQuadraticComplexityTest/QuadraticComplexitySolidity_CallDataCopyFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
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
@pytest.mark.pre_alloc_mutable
def test_quadratic_complexity_solidity_call_data_copy(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_quadratic_complexity_solidity_call_data_copy."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_1 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
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

    # Source: raw
    # 0x60003560e060020a9004806361a4770614601557005b601e6004356024565b60006000f35b60008160008190555073b94f5374fce5edbc8e2a8697c15331677e6ebf0b90505b600082131560bf5780600160a060020a03166000600060007f6a7573740000000000000000000000000000000000000000000000000000000081526004017f63616c6c000000000000000000000000000000000000000000000000000000008152602001600060008560155a03f150506001820391506045565b505056  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
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
        + Op.PUSH20[0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B]
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
        balance=0x11C37937E08000,
        nonce=0,
        address=Address(0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )
    # Source: lll
    # { (CALLDATACOPY 0 0 50000) }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=0xC350)
        + Op.STOP,
        balance=0x4C4B40,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )
    pre[sender] = Account(balance=0x11C37937E08000)

    tx_data = [
        Bytes("61a47706") + Hash(0xC350),
    ]
    tx_gas = [150000, 250000000]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {
        contract_0: Account(
            storage={},
            code=bytes.fromhex(
                "60003560e060020a9004806361a4770614601557005b601e6004356024565b60006000f35b60008160008190555073b94f5374fce5edbc8e2a8697c15331677e6ebf0b90505b600082131560bf5780600160a060020a03166000600060007f6a7573740000000000000000000000000000000000000000000000000000000081526004017f63616c6c000000000000000000000000000000000000000000000000000000008152602001600060008560155a03f150506001820391506045565b505056"  # noqa: E501
            ),
            nonce=0,
        ),
        contract_1: Account(
            storage={},
            code=bytes.fromhex("61c350600060003700"),
            nonce=0,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
