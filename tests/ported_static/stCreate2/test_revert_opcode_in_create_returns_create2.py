"""
RevertOpcodeInCreateReturns for CREATE2.

Ported from:
tests/static/state_tests/stCreate2
RevertOpcodeInCreateReturnsCreate2Filler.json
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
        "tests/static/state_tests/stCreate2/RevertOpcodeInCreateReturnsCreate2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_in_create_returns_create2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """RevertOpcodeInCreateReturns for CREATE2."""
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
        gas_limit=47244640256,
    )

    # Source: LLL
    # { (seq (CREATE2 0 0 (lll (seq (mstore 0 0x112233) (revert 0 32) (STOP)) 0) 0) (SSTORE 0 (RETURNDATASIZE)) (STOP) )}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH1[0xE]
            + Op.CODECOPY(dest_offset=0x0, offset=0x17, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.CREATE2)
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.STOP
            + Op.STOP
            + Op.INVALID
            + Op.MSTORE(offset=0x0, value=0x112233)
            + Op.REVERT(offset=0x0, size=0x20)
            + Op.STOP
            + Op.STOP
        ),
        storage={0x0: 0x1},
        nonce=0,
        address=Address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
    )

    post = {
        contract: Account(storage={0: 32}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
