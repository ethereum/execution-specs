"""
Create2OnDepth1023, 0x0400 indicates 1022 level.

Ported from:
state_tests/stCreate2/Create2OnDepth1023Filler.json
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
    ["state_tests/stCreate2/Create2OnDepth1023Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_create2_on_depth1023(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Create2OnDepth1023, 0x0400 indicates 1022 level."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_1 = Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(
        balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (CALLDATALOAD 0)) (MSTORE 0 (ADD 2 (MLOAD 0))) (if (EQ (MLOAD 0) 0x0400) (seq (MSTORE 32 0x6000600060006000f5600155) [[1]] (CREATE2 0 52 12 0))  (CALL (GAS) 0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b (EQ (MLOAD 0) 0x0400) 0 32 0 0)) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=Op.ADD(0x2, Op.MLOAD(offset=0x0)))
        + Op.JUMPI(pc=0x43, condition=Op.EQ(Op.MLOAD(offset=0x0), 0x400))
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                value=Op.EQ(Op.MLOAD(offset=0x0), 0x400),
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMP(pc=0x60)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x20, value=0x6000600060006000F5600155)
        + Op.SSTORE(
            key=0x1,
            value=Op.CREATE2(value=0x0, offset=0x34, size=0xC, salt=0x0),
        )
        + Op.JUMPDEST
        + Op.STOP,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (CALLDATALOAD 0)) (CALL (GAS) 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 32 0 0) }  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.CALL(
            gas=Op.GAS,
            address=0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
            value=0x0,
            args_offset=0x0,
            args_size=0x20,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=9151314442816847871,
    )

    post = {
        Address(0x4F05179F0987710F94F2CBDE67C5357BC1815AF3): Account(nonce=1),
        Address(0xA3DA9580897E90044FA0DE6969815406B3172E3A): Account(
            storage={1: 0x4F05179F0987710F94F2CBDE67C5357BC1815AF3},
        ),
        contract_0: Account(
            storage={1: 0xA3DA9580897E90044FA0DE6969815406B3172E3A},
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
