"""
Create2OnDepth1024, 0x0400 indicates 1022 level.

Ported from:
tests/static/state_tests/stCreate2/Create2OnDepth1024Filler.json
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
    ["tests/static/state_tests/stCreate2/Create2OnDepth1024Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_create2_on_depth1024(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Create2OnDepth1024, 0x0400 indicates 1022 level."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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
        balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
    )
    # Source: LLL
    # { (MSTORE 0 (CALLDATALOAD 0)) (MSTORE 0 (ADD 2 (MLOAD 0))) (if (EQ (MLOAD 0) 0x0400) (seq (MSTORE 32 0x686000600060006000f56000526000600960176000f5600155) [[1]] (CREATE2 0 39 25 0))  (CALL (GAS) 0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b (EQ (MLOAD 0) 0x0400) 0 32 0 0)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
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
                ),
            )
            + Op.JUMP(pc=0x6D)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0x20,
                value=0x686000600060006000F56000526000600960176000F5600155,
            )
            + Op.SSTORE(
                key=0x1,
                value=Op.CREATE2(value=0x0, offset=0x27, size=0x19, salt=0x0),
            )
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: LLL
    # { (MSTORE 0 (CALLDATALOAD 0)) (CALL (GAS) 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 32 0 0) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
            + Op.CALL(
                gas=Op.GAS,
                address=0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=9151314442816847871,
    )

    post = {
        Address("0xb250d8cdad4a7a81323be508f4ac44584dd27597"): Account(
            storage={1: 0x436B8F99E8D953CDAF8F9472116ADD83CCD82A65},
        ),
        contract: Account(
            storage={1: 0xB250D8CDAD4A7A81323BE508F4AC44584DD27597},
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
